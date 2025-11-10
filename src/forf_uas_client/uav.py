import json
import math
from datetime import datetime, timezone
from typing import override

from forf_uas_client.callsign_mapper import get_mapper
from forf_uas_client.models.UAVStatus import UAVStatus, UAVStatusLiteral
from forf_uas_client.utils import serial_to_id

CALL_SIGN_PREFIX = "Norsk Folkehjelp"


class UAV:
    """..."""

    def __init__(
        self,
        *,
        id: str,
        latitude: float,
        longitude: float,
        altitude: float,
        elevation: float = 0,
        attitude_head: float = 0,
        ground_speed: float = 0,
        vertical_rate: float = 0,
    ):
        self.id: str = id

        # Metadata
        self.altitude: float = altitude
        self.elevation: float = elevation
        self.last_updated: datetime = datetime.now(timezone.utc)

        self.old_latitude: float = -1
        self.old_longitude: float = -1

        # Location
        self.latitude: float = latitude
        self.longitude: float = longitude

        # Speed
        self.ground_speed: float = ground_speed
        self.vertical_rate: float = vertical_rate

        self.attitude_head: float = attitude_head

        # Utils
        self.mapper = get_mapper()

    def update(
        self,
        *,
        latitude: float,
        longitude: float,
        altitude: float,
        attitude_head: float,
        ground_speed: float,
        vertical_rate: float,
        elevation: float,
    ):
        # store old position
        self.old_latitude = self.latitude
        self.old_longitude = self.longitude

        # set new values
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.attitude_head = attitude_head
        self.ground_speed = ground_speed
        self.vertical_rate = vertical_rate
        self.elevation = elevation

        self.last_updated = datetime.now(timezone.utc)

    def status(self) -> UAVStatus:
        """
        Returns current UAV Status.

        Returns:
            UAVStatus containing current state.
        """
        return UAVStatus(
            id=f"{serial_to_id(self.id)}",
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude,
            status=self.flight_status,
            call_sign=self.call_sign,
            course=self.course,  # attitude_head,
            ground_speed=self.ground_speed,
            vertical_rate=self.vertical_rate,
            last_update=self.last_updated.timestamp(),
        )

    @property
    def course(self) -> float:
        """
        Calculate the UAV bearing based on two last coordinates.
        """
        if self.old_latitude < 0 or self.old_longitude < 0:
            return self.attitude_head

        lat1_rad = math.radians(self.old_latitude)
        lat2_rad = math.radians(self.latitude)
        dlon = math.radians(self.longitude - self.old_longitude)

        x = math.sin(dlon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(
            lat2_rad
        ) * math.cos(dlon)

        initial_bearing = math.atan2(x, y)
        bearing = (math.degrees(initial_bearing) + 360) % 360

        return bearing

    @property
    def flight_status(self) -> UAVStatusLiteral:
        """
        Return UAVs flight status.

        Returns:
            AIRBORNE if elevation is greater than 0, else GROUNDED.
        """
        return "AIRBORNE" if self.elevation > 0 else "GROUNDED"

    @property
    def call_sign(self) -> str:
        """Retrieve call sign from."""
        callsign_suffix: str | None = self.mapper.get_callsign(self.id)

        if callsign_suffix is None:
            return f"{CALL_SIGN_PREFIX} {serial_to_id(self.id)}"

        return f"{CALL_SIGN_PREFIX} ({callsign_suffix})"

    @override
    def __str__(self):
        return json.dumps(self.status().to_json(), indent=4)
