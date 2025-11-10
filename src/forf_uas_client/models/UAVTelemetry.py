from typing import NamedTuple


class UAVTelemetry(NamedTuple):
    """
    Parsed UAV telemetry data.
    """

    serial_number: str
    latitude: float
    longitude: float
    altitude: float
    elevation: float
    attitude_head: float
    ground_speed: float
    vertical_rate: float
