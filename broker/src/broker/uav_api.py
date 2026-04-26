import atexit
import httpx
import os


class UavApiClient:
    def __init__(self):
        self.base_url = os.getenv("BASE_URL", "http://api:8000")
        self.client = httpx.Client()

    def get_uav(self, serial_number: str):
        res = self.client.get(f"{self.base_url}/uav/{serial_number}")
        if res.status_code == 404:
            return None

        res.raise_for_status()
        return res.json()

    def close(self):
        self.client.close()


uav_client = UavApiClient()
atexit.register(uav_client.close)
