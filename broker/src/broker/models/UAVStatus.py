import dataclasses
from typing import Literal

UAVStatusLiteral = Literal["GROUNDED", "AIRBORNE"]


@dataclasses.dataclass
class UAVStatus:
    """
    Status message of UAV Telemetry data.
    """

    id: str
    call_sign: str
    latitude: float
    longitude: float
    altitude: float

    status: UAVStatusLiteral

    course: float
    ground_speed: float
    vertical_rate: float

    last_update: float

    def to_json(self):
        return dataclasses.asdict(self)
