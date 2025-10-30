import json
from typing import override
from datetime import datetime, timezone

from forf_uas_client.models.UAVStatus import UAVStatus, UAVStatusLiteral
from forf_uas_client.utils import serial_to_id

CALL_SIGN_PREFIX = "NFS"


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
        ground_speed: float = 0,
        vertical_rate: float = 0,
    ):
        self.id: str = id

        # Metadata
        self.altitude: float = altitude
        self.elevation: float = elevation
        self.last_updated: datetime = datetime.now(timezone.utc)

        # Location
        self.latitude: float = latitude
        self.longitude: float = longitude

        # Speed
        self.ground_speed: float = ground_speed
        self.vertical_rate: float = vertical_rate

    def update(
        self,
        *,
        latitude: float,
        longitude: float,
        altitude: float,
        ground_speed: float,
        vertical_rate: float,
        elevation: float,
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.ground_speed = ground_speed
        self.vertical_rate = vertical_rate
        self.elevation = elevation

        self.last_update = datetime.now(timezone.utc)

    def status(self) -> UAVStatus:
        """
        Returns current UAV Status.

        Returns:
            UAVStatus containing current state.
        """
        return UAVStatus(
            id=self.call_sign,
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude,
            status=self.flight_status,
            call_sign=self.call_sign,
            ground_speed=self.ground_speed,
            vertical_rate=self.vertical_rate,
            last_update=self.last_update.timestamp(),
        )

    @property
    def flight_status(self) -> UAVStatusLiteral:
        """
        Return UAVs flight status.

        Returns:
            AIRBORNE if elevation is greater than 0, else GROUNDED.
        """
        return "AIRBORNE" if self.elevation > 0 else "GROUNDED"

    @override
    def __str__(self):
        return json.dumps(self.status().to_json(), indent=4)

    @property
    def call_sign(self) -> str:
        """Retrieve call sign from."""
        return f"{CALL_SIGN_PREFIX}{serial_to_id(self.id)}"
