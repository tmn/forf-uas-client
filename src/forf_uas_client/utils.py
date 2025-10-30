import hashlib


def serial_to_id(serial: str) -> int:
    """..."""
    h = hashlib.sha256(serial.encode()).digest()
    num = int.from_bytes(h, "big")
    return num % 1_000_000
