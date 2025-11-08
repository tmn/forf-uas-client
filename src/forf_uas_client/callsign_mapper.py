import os
import sqlite3
import threading
from datetime import datetime

from dotenv.main import load_dotenv

load_dotenv()


class CallsignMapper:
    """
    ...
    """

    def __init__(self, db: str = os.environ.get("DB_PATH", "")):
        """

        Args:
            db: Path to database file.
        """
        self.db = db
        self._local = threading.local()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db) as conn:
            conn.execute("""
                             CREATE TABLE IF NOT EXISTS uav_callsigns (
                                 serial_number TEXT PRIMARY KEY,
                                 callsign TEXT NOT NULL,
                                 regid TEXT,
                                 notes TEXT,
                                 active BOOLEAN DEFAULT 1,
                                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                             )
                         """)

    def _get_conn(self):
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(
                self.db, check_same_thread=False, timeout=10.0
            )
            self._local.conn.row_factory = sqlite3.Row

        return self._local.conn

    def get_callsign(self, serial_number: str):
        conn = self._get_conn()
        result = conn.execute(
            "SELECT callsign, regid FROM uav_callsigns WHERE serial_number = ? AND active = 1",
            (serial_number,),
        ).fetchone()

        if result is None:
            return None

        return result["callsign"] if result["callsign"] else result["regid"][-2:]

    def add_or_update(
        self, serial_number: str, callsign: str, regid: str = "", notes: str = ""
    ):
        conn = self._get_conn()
        conn.execute(
            """
                         INSERT INTO uav_callsigns (serial_number, callsign, regid, notes, updated_at)
                         VALUES (?, ?, ?, ?, ?)
                         ON CONFLICT(serial_number) DO UPDATE SET
                             callsign = excluded.callsign,
                             regid = excluded.regid,
                             notes = excluded.notes,
                             updated_at = excluded.updated_at
                     """,
            (serial_number, callsign, regid, notes, datetime.now()),
        )

        conn.commit()

    def list_all(self):
        conn = self._get_conn()
        return conn.execute("""
                                SELECT * FROM uav_callsigns ORDER BY callsign
                            """).fechall()


_mapper_instance: CallsignMapper | None = None


def get_mapper(db: str = os.environ.get("DB_PATH", "")):
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = CallsignMapper(db)

    return _mapper_instance
