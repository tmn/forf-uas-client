import logging
import os
from .client import UASClient


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main():
    # Read configuration from environment
    api_enabled = os.getenv("API_ENABLED", "true").lower() == "true"
    api_base_url = os.getenv("API_BASE_URL")
    api_key = os.getenv("API_KEY")
    api_interval = float(os.getenv("API_UPDATE_INTERVAL", "1.0"))

    client = UASClient(
        enable_api_sender=api_enabled,
        api_base_url=api_base_url,
        api_key=api_key,
        api_update_interval=api_interval,
    )
    client.connect()


if __name__ == "__main__":
    main()
