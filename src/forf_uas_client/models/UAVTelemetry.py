from typing import NamedTuple


class UAVTelemetry(NamedTuple):
    """
    Parsed UAV telemetry data from OSD message.
    """

    serial_number: str
    latitude: float
    longitude: float
    altitude: float
    elevation: float
    ground_speed: float
    vertical_rate: float
