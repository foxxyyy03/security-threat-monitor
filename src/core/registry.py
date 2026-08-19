"""
Article registry management.

Stores article processing state and prevents duplicate processing
and Telegram publications across application runs.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from core.former import FeedItem


REGISTRY_FILE = Path("state/registry.json")


def generate_id(url: str) -> str:
    """Generate stable ID based on article URL."""

    return hashlib.sha256(
        url.strip().encode("utf-8")
    ).hexdigest()


def get_current_timestamp() -> str:
    """Return current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def load_registry() -> dict:
    """Load registry from disk."""

    if not REGISTRY_FILE.exists():
        return {}

    with REGISTRY_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_registry(registry: dict) -> None:
    """Save registry to disk."""

    REGISTRY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with REGISTRY_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            registry,
            file,
            ensure_ascii=False,
            indent=2
        )


def is_known(item: FeedItem, registry: dict) -> bool:
    """Check whether article already exists."""

    return item.id in registry


def register_item(
    item: FeedItem,
    registry: dict
) -> None:
    """Register a newly discovered article."""

    registry[item.id] = {
        "source": item.source,
        "source_type": item.source_type,
        "title": item.title,
        "url": item.url,
        "published": (
            item.published.isoformat()
            if item.published
            else None
        ),
        "categories": item.categories,
        "tags": item.tags,

        "first_seen": get_current_timestamp(),

        "status": "discovered",

        "telegram": {
            "published": False,
            "message_id": None,
            "published_at": None,
            "last_error": None,
            "attempts": 0
        }
    }


def mark_telegram_success(
    item_id: str,
    message_id: int,
    registry: dict
) -> None:
    """Mark article as successfully published to Telegram."""

    if item_id not in registry:
        return

    registry[item_id]["status"] = "published"

    registry[item_id]["telegram"] = {
        "published": True,
        "message_id": message_id,
        "published_at": get_current_timestamp(),
        "last_error": None,
        "attempts": (
            registry[item_id]["telegram"].get(
                "attempts",
                0
            )
        )
    }


def mark_telegram_failed(
    item_id: str,
    error: str,
    registry: dict
) -> None:
    """Mark Telegram publication as failed."""

    if item_id not in registry:
        return

    telegram_state = registry[item_id]["telegram"]

    telegram_state["published"] = False
    telegram_state["last_error"] = error
    telegram_state["attempts"] = (
        telegram_state.get("attempts", 0) + 1
    )

    registry[item_id]["status"] = "failed"

