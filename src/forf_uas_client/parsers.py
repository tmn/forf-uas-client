import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from forf_uas_client.models.UAVTelemetry import UAVTelemetry
from forf_uas_client.uav_registry import UAVRegistry

OUTPUT_DIR: Path = Path("/app/data") / "logs"

# Create output directory if it doesn't exist
try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    # Fall back to local directory if /app is not writable (e.g., in tests)
    OUTPUT_DIR = Path("data") / "logs"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# OSD Logger
logger_osd = logging.getLogger("telemetry_osd")
logger_osd.setLevel(logging.INFO)

handler_osd = RotatingFileHandler(
    OUTPUT_DIR / "osd.log",
    maxBytes=250 * 1024 * 1024,
    backupCount=5,
)
handler_osd.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger_osd.addHandler(handler_osd)

# State logger
logger_state = logging.getLogger("telemetry_state")
logger_state.setLevel(logging.INFO)

handler_state = RotatingFileHandler(
    OUTPUT_DIR / "state.log",
    maxBytes=250 * 1024 * 1024,
    backupCount=5,
)
handler_state.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger_state.addHandler(handler_state)


def parse_osd_message(data: dict, host: dict) -> UAVTelemetry | None:
    """
    Parse and extract UAV telemetry data.

    Args:
        data: dict from osd message
        host: dict form data object on the osd message

    Returns:
        UAVTelemetry if message contains valid UAV data
    """
    required_fields: list[str] = [
        "latitude",
        "longitude",
        "height",
        "attitude_head",
        "horizontal_speed",
        "vertical_speed",
        "elevation",
    ]

    if not all(field in host for field in required_fields):
        logger_osd.warning("Missing required fields in OSD message.")
        return None

    return UAVTelemetry(
        serial_number=data.get("sn", ""),
        latitude=host.get("latitude", 0.0),
        longitude=host.get("longitude", 0.0),
        height=host.get("height", 0.0),
        attitude_head=host.get("attitude_head", 0),
        horizontal_speed=host.get("horizontal_speed", 0.0),
        vertical_speed=host.get("vertical_speed", 0.0),
        elevation=host.get("elevation", 0.0),
    )


def on_osd_message(payload: bytes, *, registry: UAVRegistry):
    """
    Handle OSD message: parse, update registry, and log to file.

    Args:
        payload: Raw MQTT message payload
        registry: UAVRegistry to update
        output_file: Path to log file
    """
    write_data_to_file(payload, logger_osd)

    try:
        res = json.loads(payload)
        data = res.get("data", {})
        host = data.get("host", {})
    except (json.JSONDecodeError, KeyError) as e:
        logger_osd.error("Unable to read message")
        return

    if not _is_uav(data, host):
        return

    telemetry: UAVTelemetry | None = parse_osd_message(data, host)
    if telemetry is not None:
        registry.update_uav(telemetry=telemetry)


def on_state_message(payload: bytes):
    """
    Handle state message: log to file and print.

    Args:
        payload: Raw MQTT message payload
        output_file: Path to log file
    """
    write_data_to_file(payload, logger_state)


def write_data_to_file(payload: bytes, log: logging.Logger) -> None:
    """
    Append payload to output file.

    Args:
        output_file: Path to log file
        log: A logger object
    """
    try:
        json_obj = json.loads(payload.decode("utf-8"))
        compact_json = json.dumps(json_obj, separators=(",", ":"))
        log.info(compact_json)
    except Exception as e:
        logger.error(f"Something went wrong: {e}")


def _is_uav(data: dict, host: dict) -> bool:
    """
    Check if message is from a UAV.

    Args:
        data: Data dictionary from parsed message
        host: Host data dictionary from parsed message

    Returns:
        True if message contains UAV telemetry fields, else False.
    """
    try:
        has_location = "latitude" in host or "longitude" in host
        has_serialnumber = bool(data.get("sn"))
        has_speed = "horizontal_speed" in host or "vertical_speed" in host
        return has_location and has_speed and has_serialnumber
    except (KeyError, TypeError):
        return False
