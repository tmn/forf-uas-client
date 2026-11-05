import atexit
import json
import logging
import queue
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path

from broker.models.UAVTelemetry import UAVTelemetry
from broker.uav_registry import UAVRegistry

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

# Max number of log records buffered between the MQTT thread and the file writer.
LOG_QUEUE_SIZE = 10_000


class _DropWhenFullQueueHandler(QueueHandler):
    """Never block (or raise in) the MQTT thread: drop the record if the writer lags."""

    def enqueue(self, record: logging.LogRecord) -> None:
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            pass


def _file_logger(name: str, filename: str) -> logging.Logger:
    """
    Create a logger that writes to a rotating file from a background thread,
    so disk I/O never blocks the MQTT callback thread.
    """
    file_handler = RotatingFileHandler(
        OUTPUT_DIR / filename,
        maxBytes=250 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))

    log_queue: queue.Queue = queue.Queue(maxsize=LOG_QUEUE_SIZE)
    listener = QueueListener(log_queue, file_handler)
    listener.start()
    atexit.register(listener.stop)  # flush remaining records on shutdown

    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    log.addHandler(_DropWhenFullQueueHandler(log_queue))
    return log


logger_osd = _file_logger("telemetry_osd", "osd.log")
logger_state = _file_logger("telemetry_state", "state.log")


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
        height=host.get("height", 0.0),4
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
    """
    log_payload(payload, logger_osd)

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
    Handle state message: log to file.

    Args:
        payload: Raw MQTT message payload
    """
    log_payload(payload, logger_state)


def log_payload(payload: bytes, log: logging.Logger) -> None:
    """
    Queue the raw payload for the telemetry log file, one message per line.

    The payload is not parsed or re-serialised; newlines are replaced so each
    message stays on a single line. Writing on a background thread.

    Args:
        payload: Raw MQTT message payload
        log: A file logger created by `_file_logger`
    """
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as e:
        logger.error(f"Unable to decode payload for logging: {e}")
        return

    log.info(text.replace("\r", " ").replace("\n", " "))


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
