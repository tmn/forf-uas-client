import dataclasses
from typing import Literal

UAVStatusLiteral = Literal["GROUNDED", "AIRBORNE"]


@dataclasses.dataclass
class UAVStatus:
    id: str
    call_sign: str
    latitude: float
    longitude: float
    altitude: float  # height

    # If UAV is GROUNDED or AIRBORNE
    status: UAVStatusLiteral

    ground_speed: float
    vertical_rate: float

    last_update: float

    def to_json(self):
        return dataclasses.asdict(self)
