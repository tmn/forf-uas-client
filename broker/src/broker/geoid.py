import os
from functools import lru_cache

from pygeodesy import GeoidKarney

GEOID_PATH = os.getenv("GEOID_PATH", "/app/geoids/egm2008-5.pgm")


@lru_cache(maxsize=1)
def load_geoid() -> GeoidKarney:
    """Load the geoid grid from GEOID_PATH (cached after the first call).

    Call this at startup so a missing or invalid grid fails immediately,
    instead of on the first OSD message inside the MQTT callback."""
    return GeoidKarney(GEOID_PATH)


def ellipsoid_to_amsl(height: float, latitude: float, longitude: float) -> float:
    """Convert WGS84 ellipsoid height (DJI `height`) to height above mean sea level.

    AMSL = ellipsoid height - geoid undulation (EGM2008) at the position."""
    return height - load_geoid().height(latitude, longitude)