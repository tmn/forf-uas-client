import json
from pathlib import Path

from forf_uas_client.uav import UAV


uavs: dict[str, UAV] = {}


def on_osd_message(payload: bytes, *, output_file: Path):
    """
    Parse osd message and update registry.
    """
    write_data_to_file(output_file, payload)

    res = json.loads(payload)
    data = res.get("data", {})
    host = data.get("host", {})

    elevation = host.get("elevation", 0)

    serialnumber: str = data.get("sn", "")
    latitude: float = host.get("latitude", 0)
    longitude: float = host.get("longitude", 0)
    altitude: float = host.get("height", 0)
    ground_speed: float = host.get("horizontal_speed", 0)
    vertical_rate: float = host.get("vertical_speed", 0)

    if serialnumber in uavs:
        uavs[serialnumber].update(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            ground_speed=ground_speed,
            vertical_rate=vertical_rate,
            elevation=elevation,
        )
    else:
        uavs[serialnumber] = UAV(
            id=serialnumber,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            elevation=elevation,
            ground_speed=ground_speed,
            vertical_rate=vertical_rate,
        )

    print(list(uavs.values()))


def on_state_message(payload: bytes, *, output_file: Path):
    """
    Parse state message.
    """
    write_data_to_file(output_file, payload)
    print(payload.decode("utf-8"))


def write_data_to_file(output_file: Path, payload: bytes):
    """
    Writing data to file.
    """
    with output_file.open("a", encoding="utf-8") as f:
        f.write(payload.decode("utf-8"))
        f.write("\n")
