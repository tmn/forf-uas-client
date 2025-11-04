import json
from pathlib import Path

from forf_uas_client.models.UAVTelemetry import UAVTelemetry
from forf_uas_client.uav_registry import UAVRegistry


def parse_osd_message(data: dict, host: dict) -> UAVTelemetry:
    """
    Parse OSD message and extract UAV telemetry data.

    Args:
        data: dict...
        host: dict...

    Returns:
        UAVTelemetry if message contains valid UAV data
    """

    return UAVTelemetry(
        serial_number=data.get("sn", ""),
        latitude=host.get("latitude", 0.0),
        longitude=host.get("longitude", 0.0),
        altitude=host.get("height", 0.0),
        ground_speed=host.get("horizontal_speed", 0.0),
        vertical_rate=host.get("vertical_speed", 0.0),
        elevation=host.get("elevation", 0.0),
    )


def on_osd_message(payload: bytes, *, registry: UAVRegistry, output_file: Path):
    """
    Handle OSD message: parse, update registry, and log to file.

    Args:
        payload: Raw MQTT message payload
        registry: UAVRegistry to update
        output_file: Path to log file
    """
    write_data_to_file(output_file, payload)

    try:
        res = json.loads(payload)
        data = res.get("data", {})
        host = data.get("host", {})
    except (json.JSONDecodeError, KeyError):
        raise Exception("Unable to read message.")

    if not _is_uav(data, host):
        return

    telemetry: UAVTelemetry = parse_osd_message(data, host)

    registry.update_uav(
        serial_number=telemetry.serial_number,
        latitude=telemetry.latitude,
        longitude=telemetry.longitude,
        altitude=telemetry.altitude,
        ground_speed=telemetry.ground_speed,
        vertical_rate=telemetry.vertical_rate,
        elevation=telemetry.elevation,
    )

    print(registry.get_all_uavs())


def on_state_message(payload: bytes, *, output_file: Path):
    """
    Handle state message: log to file and print.

    Args:
        payload: Raw MQTT message payload
        output_file: Path to log file
    """
    write_data_to_file(output_file, payload)
    print(payload.decode("utf-8"))


def write_data_to_file(output_file: Path, payload: bytes):
    """
    Append payload to output file.

    Args:
        output_file: Path to log file
        payload: Raw bytes to write
    """
    with output_file.open("a", encoding="utf-8") as f:
        f.write(payload.decode("utf-8"))
        f.write("\n")


def _is_uav(data: dict, host: dict) -> bool:
    """
    Check if message is from a UAV.

    Args:
        host: Host data dictionary from parsed message

    Returns:
        True if message contains UAV telemetry fields
    """
    try:
        has_speed = "horizontal_speed" in host or "vertical_speed" in host
        has_serialnumber = bool(data.get("sn"))
        return has_speed and has_serialnumber
    except (KeyError, TypeError):
        return False
