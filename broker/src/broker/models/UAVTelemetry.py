from typing import NamedTuple


class UAVTelemetry(NamedTuple):
    """
    Parsed UAV telemetry data.
    """

    serial_number: str
    latitude: float
    longitude: float
    height: float
    elevation: float
    attitude_head: float
    horizontal_speed: float
    vertical_speed: float
