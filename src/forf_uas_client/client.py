import os
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from forf_uas_client.parsers import on_osd_message, on_state_message

load_dotenv()


OUTPUT_DIR = Path.home() / ".forf/output"


class UASClient:
    """
    The purpose of the client is to connect to a message stream, and act
    like a bridge between data source and and receivers.
    """

    def __init__(self) -> None:
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.username_pw_set(
            os.environ.get("USERNAME", ""), os.environ.get("PASSWORD", "")
        )

        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message

        if not OUTPUT_DIR.exists():
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def connect(self):
        """
        Connect to host and start loop.
        """
        self._client.connect(os.getenv("HOST", ""), 1883, 60)
        self._client.loop_forever()

    def disconnect(self):
        """
        Disconnect client and stop looping.
        """
        self._client.loop_stop()
        self._client.disconnect()

    def on_connect(self, client, userdata, flags, reason_code, props):
        """
        Setup subscriptions when connected.
        """
        print(f"Connected with res code: {reason_code}")

        topics: list[str] = str(os.getenv("TOPICS")).split(",")

        for topic in topics:
            client.subscribe(topic)

    def on_message(self, client, userdata, msg):
        """
        Handle incoming messages.
        """
        if str(msg.topic).endswith("/osd"):
            on_osd_message(msg.payload, output_file=OUTPUT_DIR / "osd.txt")
        elif str(msg.topic).endswith("/state"):
            on_state_message(msg.payload, output_file=OUTPUT_DIR / "state.txt")

    @property
    def client(self):
        return self._client
