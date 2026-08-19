"""
Telegram integration.

Provides functionality for publishing formatted messages
to the configured Telegram channel.
"""

import os

import requests
from dotenv import load_dotenv

from core.former import FeedItem
from core.formatter import format_telegram_message


TELEGRAM_API_URL = "https://api.telegram.org"

load_dotenv()


def get_telegram_token() -> str:
    """Get Telegram bot token from environment."""

    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    return token


def get_telegram_chat_id() -> str:
    """Get Telegram chat ID from environment."""

    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not chat_id:
        raise RuntimeError(
            "TELEGRAM_CHAT_ID is not configured."
        )

    return chat_id


def send_message(item: FeedItem) -> int:
    """
    Send a FeedItem to Telegram.

    Returns Telegram message ID on success.
    Raises RuntimeError on failure.
    """

    token = get_telegram_token()
    chat_id = get_telegram_chat_id()

    url = (
        f"{TELEGRAM_API_URL}"
        f"/bot{token}/sendMessage"
    )

    payload = {
        "chat_id": chat_id,
        "text": format_telegram_message(item),
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()

    except requests.RequestException as error:

        raise RuntimeError(
            f"Telegram API request failed: {error}"
        ) from error

    try:
        data = response.json()

    except ValueError as error:

        raise RuntimeError(
            "Telegram API returned invalid JSON."
        ) from error

    if not data.get("ok"):

        raise RuntimeError(
            f"Telegram API returned an error: {data}"
        )

    return data["result"]["message_id"]
