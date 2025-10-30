from typing import Generator

import pytest

from forf_uas_client.uav import UAV


def test_flight_status(uav: UAV):
    """
    Flight status should change between GROUNDED and AIRBORNE depending
    on the elevation of the UAV.
    """
    assert uav.flight_status == "GROUNDED"
    uav.elevation = 10
    assert uav.flight_status == "AIRBORNE"
    uav.elevation = 0
    assert uav.flight_status == "GROUNDED"


@pytest.fixture()
def uav() -> Generator[UAV]:
    uav = UAV(
        id="",
        latitude=0,
        longitude=0,
        altitude=0,
        elevation=0,
        ground_speed=0,
        vertical_rate=0,
    )

    yield uav
