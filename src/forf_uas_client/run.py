from dotenv import load_dotenv

from .client import UASClient

load_dotenv()


def main():
    client = UASClient()
    client.connect()


if __name__ == "__main__":
    main()
