from forf_uas_client.models.UAVTelemetry import UAVTelemetry
from datetime import datetime, timezone
from pathlib import Path

from forf_uas_client.uav import UAV


class UAVRegistry:
    """
    Manages the registry of active UAVs.

    Responsibilities:
    - Maintain collection of UAV instances
    - Update existing UAVs or create new ones
    - Track last seen times
    - Filter active UAVs based on age
    - Support future callsign mapping from Luftfartstilsynet
    """

    def __init__(self, mapper=None):
        self._uavs: dict[str, UAV] = {}
        self._mapper = mapper  # Optional callsign mapper for dependency injection

    def update_uav(self, *, telemetry: UAVTelemetry) -> UAV:
        """
        Update existing UAV or create a new one.

        Args:
            telemetry: UAVTelemetry object.

        Returns:
            The updated or newly created UAV instance
        """
        if telemetry.serial_number in self._uavs:
            self._uavs[telemetry.serial_number].update(
                latitude=telemetry.latitude,
                longitude=telemetry.longitude,
                altitude=telemetry.height,
                attitude_head=telemetry.attitude_head,
                ground_speed=telemetry.horizontal_speed,
                vertical_rate=telemetry.vertical_speed,
                elevation=telemetry.elevation,
            )
        else:
            self._uavs[telemetry.serial_number] = UAV(
                id=telemetry.serial_number,
                latitude=telemetry.latitude,
                longitude=telemetry.longitude,
                altitude=telemetry.height,
                elevation=telemetry.elevation,
                attitude_head=telemetry.attitude_head,
                ground_speed=telemetry.horizontal_speed,
                vertical_rate=telemetry.vertical_speed,
                mapper=self._mapper,
            )

        return self._uavs[telemetry.serial_number]

    def get_uav(self, serial_number: str) -> UAV | None:
        """
        Get a specific UAV by serial number.

        Args:
            serial_number: UAV serial number

        Returns:
            UAV instance or None if not found
        """
        return self._uavs.get(serial_number)

    def get_active_uavs(self, max_age_seconds: int = 30) -> list[UAV]:
        """
        Get UAVs that have been seen recently.

        Args:
            max_age_seconds: Maximum age in seconds for a UAV to be considered active

        Returns:
            List of UAVs updated within the specified time window
        """
        now = datetime.now(timezone.utc)
        active = []

        for uav in self._uavs.values():
            age = (now - uav.last_updated).total_seconds()
            if age <= max_age_seconds:
                active.append(uav)

        return active

    def remove_inactive_uavs(self, max_age_seconds: int = 300) -> int:
        """
        Remove UAVs that haven't been seen recently.

        Args:
            max_age_seconds: Maximum age in seconds before a UAV is removed

        Returns:
            Number of UAVs removed
        """
        now = datetime.now(timezone.utc)
        to_remove = []

        for serial, uav in self._uavs.items():
            age = (now - uav.last_updated).total_seconds()
            if age > max_age_seconds:
                to_remove.append(serial)

        for serial in to_remove:
            del self._uavs[serial]

        return len(to_remove)

    def __len__(self) -> int:
        """Return number of UAVs in registry."""
        return len(self._uavs)

    def __repr__(self) -> str:
        """String representation of registry."""
        return f"UAVRegistry(uavs={len(self._uavs)})"
