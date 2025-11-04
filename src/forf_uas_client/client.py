import asyncio
import logging
import os
import threading
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from forf_uas_client.api_sender import APISender
from forf_uas_client.parsers import on_osd_message, on_state_message
from forf_uas_client.uav_registry import UAVRegistry

load_dotenv()

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path.home() / ".forf/output"


class UASClient:
    """
    The purpose of the client is to connect to a message stream, and act
    like a bridge between data source and and receivers.
    """

    def __init__(
        self,
        registry: UAVRegistry | None = None,
        enable_api_sender: bool = True,
        api_base_url: str | None = None,
        api_key: str | None = None,
        api_update_interval: float = 1.0,
    ) -> None:
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.username_pw_set(
            os.environ.get("USERNAME", ""), os.environ.get("PASSWORD", "")
        )

        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message

        # Use provided registry or create a new one
        self._registry = registry if registry is not None else UAVRegistry()

        # API sender setup
        self._enable_api_sender = enable_api_sender
        self._api_sender: APISender | None = None
        self._api_thread: threading.Thread | None = None
        self._api_loop: asyncio.AbstractEventLoop | None = None

        if enable_api_sender:
            api_url = api_base_url or os.getenv("API_BASE_URL", "")
            api_key = api_key or os.getenv("API_KEY")
            self._api_sender = APISender(
                registry=self._registry,
                api_base_url=api_url,
                api_key=api_key,
                update_interval=api_update_interval,
            )

        if not OUTPUT_DIR.exists():
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def connect(self):
        """
        Connect to host and start loop.

        If API sender is enabled, starts it in a background thread before
        starting the MQTT loop.
        """
        # Start API sender in background thread
        if self._api_sender:
            self._start_api_sender()

        # Connect MQTT and start blocking loop
        self._client.connect(os.getenv("HOST", ""), 1883, 60)
        try:
            self._client.loop_forever()
        finally:
            self.disconnect()

    def disconnect(self):
        """
        Disconnect client and stop looping.
        """
        self._client.loop_stop()
        self._client.disconnect()

        # Stop API sender
        if self._api_sender:
            self._stop_api_sender()

    def _start_api_sender(self):
        """Start the API sender in a background thread."""
        if self._api_thread and self._api_thread.is_alive():
            logger.warning("API sender thread already running")
            return

        def run_async_loop():
            """Run asyncio event loop in thread."""
            self._api_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._api_loop)

            try:
                self._api_loop.run_until_complete(self._api_sender.start())
                # Keep loop running
                self._api_loop.run_forever()
            except Exception as e:
                logger.error(f"Error in API sender thread: {e}", exc_info=True)
            finally:
                self._api_loop.close()

        self._api_thread = threading.Thread(target=run_async_loop, daemon=True)
        self._api_thread.start()
        logger.info("API sender thread started")

    def _stop_api_sender(self):
        """Stop the API sender and cleanup."""
        if not self._api_loop:
            return

        # Schedule stop in the event loop
        asyncio.run_coroutine_threadsafe(self._api_sender.stop(), self._api_loop)

        # Stop the event loop
        self._api_loop.call_soon_threadsafe(self._api_loop.stop)

        # Wait for thread to finish
        if self._api_thread:
            self._api_thread.join(timeout=5.0)
            if self._api_thread.is_alive():
                logger.warning("API sender thread did not stop gracefully")

        logger.info("API sender stopped")

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
            on_osd_message(
                msg.payload, registry=self._registry, output_file=OUTPUT_DIR / "osd.txt"
            )
        elif str(msg.topic).endswith("/state"):
            on_state_message(msg.payload, output_file=OUTPUT_DIR / "state.txt")

    @property
    def client(self):
        return self._client

    @property
    def registry(self) -> UAVRegistry:
        """Access the UAV registry."""
        return self._registry

    @property
    def api_sender(self) -> APISender | None:
        """Access the API sender (if enabled)."""
        return self._api_sender
