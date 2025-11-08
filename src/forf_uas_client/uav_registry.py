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

    def __init__(self):
        self._uavs: dict[str, UAV] = {}
        self._callsign_map: dict[str, str] = {}  # serial -> official callsign

    def update_uav(
        self,
        *,
        serial_number: str,
        latitude: float,
        longitude: float,
        altitude: float,
        ground_speed: float,
        vertical_rate: float,
        elevation: float,
    ) -> UAV:
        """
        Update existing UAV or create a new one.

        Args:
            serial_number: UAV serial number (unique identifier)
            latitude: Geographic latitude
            longitude: Geographic longitude
            altitude: Height above sea level
            ground_speed: Horizontal velocity
            vertical_rate: Vertical velocity
            elevation: Height above ground level

        Returns:
            The updated or newly created UAV instance
        """
        if serial_number in self._uavs:
            self._uavs[serial_number].update(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                ground_speed=ground_speed,
                vertical_rate=vertical_rate,
                elevation=elevation,
            )
        else:
            self._uavs[serial_number] = UAV(
                id=serial_number,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                elevation=elevation,
                ground_speed=ground_speed,
                vertical_rate=vertical_rate,
            )

        return self._uavs[serial_number]

    def get_uav(self, serial_number: str) -> UAV | None:
        """
        Get a specific UAV by serial number.

        Args:
            serial_number: UAV serial number

        Returns:
            UAV instance or None if not found
        """
        return self._uavs.get(serial_number)

    def get_all_uavs(self) -> list[str]:
        """
        Get all UAVs in the registry.

        Returns:
            List of all UAV instances
        """
        return list(self._uavs.keys())

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

    def load_callsign_mapping(self, filepath: Path):
        """
        Load official callsign mapping.

        Args:
            filepath: Path to callsign mapping file (CSV or JSON)
        """
        # TODO: Implement when data format is known
        raise NotImplementedError("Callsign mapping not yet implemented")

    def get_callsign(self, serial_number: str) -> str | None:
        """
        Get official callsign for a UAV if available.

        Args:
            serial_number: UAV serial number

        Returns:
            Official callsign or None if not mapped
        """
        return self._callsign_map.get(serial_number)

    def __len__(self) -> int:
        """Return number of UAVs in registry."""
        return len(self._uavs)

    def __repr__(self) -> str:
        """String representation of registry."""
        return f"UAVRegistry(uavs={len(self._uavs)})"
