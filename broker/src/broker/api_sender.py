import asyncio
import logging
from urllib.parse import urljoin

import aiohttp

from broker.uav_registry import UAVRegistry

logger = logging.getLogger(__name__)


class APISenderError(Exception):
    pass


class APISender:
    """
    Sends UAV position updates to external API on a periodic schedule.
    """

    def __init__(
        self,
        registry: UAVRegistry,
        api_base_url: str,
        api_key: str | None = None,
        update_interval: float = 1.0,
        max_uav_age: int = 30,
        timeout: float = 5.0,
    ):
        """
        Initialize API sender.

        Args:
            registry: UAVRegistry to read UAV data from
            api_base_url: Base URL for the API
            api_key: API key for authentication (optional)
            update_interval: Seconds between updates (default: 1.0)
            max_uav_age: Maximum age in seconds for UAV to be considered active (default: 30)
            timeout: HTTP request timeout in seconds (default: 5.0)
        """
        self._registry = registry
        self._api_base_url = api_base_url.rstrip("/")
        self._api_key = api_key
        self._update_interval = update_interval
        self._max_uav_age = max_uav_age
        self._timeout = timeout
        self._running = False
        self._task: asyncio.Task | None = None
        self._session: aiohttp.ClientSession | None = None
        self._headers = {}

        if api_key:
            self._headers["x-api-key"] = api_key
        else:
            raise APISenderError("Missing API key. Please set API key.")

    async def start(self):
        """
        Create background task and start API Sender periodic task.
        """
        if self._running:
            logger.warning("APISender is already running")
            return

        self._running = True

        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self._timeout),
            headers={"Content-Type": "application/json"},
        )

        self._task = asyncio.create_task(self._update_loop())

        logger.info(
            f"APISender started: interval={self._update_interval}s, "
            f"max_age={self._max_uav_age}s, api={self._api_base_url}"
        )

    async def stop(self):
        """
        Stop the periodic update task and cleanup resources.
        """
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()

            try:
                await self._task
            except asyncio.CancelledError:
                pass

            self._task = None

        if self._session:
            await self._session.close()
            self._session = None

        logger.info("APISender stopped")

    async def _update_loop(self):
        """
        Main update loop that runs periodically.
        """
        while self._running:
            try:
                self._registry.remove_inactive_uavs()
                await self.send_updates()
            except Exception as e:
                logger.error(f"Error in update loop: {e}", exc_info=True)

            try:
                await asyncio.sleep(self._update_interval)
            except asyncio.CancelledError:
                break

    async def send_updates(self):
        """
        Send bulk update for all active UAVs to the API.

        Gets active UAVs from registry and sends their current status as a single
        bulk request containing a list of all UAV positions.
        """
        active_uavs = self._registry.get_active_uavs(max_age_seconds=self._max_uav_age)

        if not active_uavs:
            logger.debug("No active UAVs to send")
            return

        logger.debug(f"Sending bulk update for {len(active_uavs)} UAVs")

        # Build list of UAV statuses
        uav_list = [uav.status().to_json() for uav in active_uavs]

        # Send as single bulk request
        success = await self._send_bulk_update(uav_list)

        if success:
            logger.info(
                f"Successfully sent bulk update for {len(active_uavs)} UAVs: {', '.join([uav.call_sign for uav in active_uavs])}"
            )
        else:
            logger.error(f"Failed to send bulk update for {len(active_uavs)} UAVs")

    async def _send_bulk_update(self, uav_list: list) -> bool:
        """
        Send bulk UAV update to the API.

        Args:
            uav_list: List of UAV status dictionaries

        Returns:
            True if successful, False otherwise
        """
        if not self._session:
            logger.error("Session not initialized")
            return False

        url = urljoin(self._api_base_url + "/", "v1/uav")

        try:
            async with self._session.post(
                url, json=uav_list, headers=self._headers
            ) as response:
                if response.status >= 200 and response.status < 300:
                    logger.debug(
                        f"Successfully sent bulk update for {len(uav_list)} UAVs "
                        f"(status: {response.status})"
                    )
                    return True
                else:
                    response_text = await response.text()
                    logger.error(
                        f"API error for bulk update: "
                        f"status={response.status}, body={response_text}"
                    )
                    return False

        except asyncio.TimeoutError:
            logger.error("Timeout sending bulk update")
            return False
        except aiohttp.ClientError as e:
            logger.error(f"Network error sending bulk update: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending bulk update: {e}", exc_info=True)
            return False

    @property
    def update_interval(self) -> float:
        """Get the current update interval."""
        return self._update_interval

    @update_interval.setter
    def update_interval(self, value: float):
        """Set a new update interval (takes effect on next cycle)."""
        if value <= 0:
            raise ValueError("Update interval must be positive")

        self._update_interval = value
        logger.info(f"Update interval changed to {value}s")
