import hashlib
import json
from pathlib import Path

from core.models import FeedItem


REGISTRY_FILE = Path("state/registry.json")


def generate_id(url: str) -> str:
    """
    Generate stable ID based on article URL.
    """

    return hashlib.sha256(
        url.strip().encode("utf-8")
    ).hexdigest()


def load_registry() -> dict:
    """
    Load article registry from disk.
    """

    if not REGISTRY_FILE.exists():
        return {}

    with REGISTRY_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_registry(registry: dict) -> None:
    """
    Save article registry to disk.
    """

    REGISTRY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with REGISTRY_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            registry,
            file,
            ensure_ascii=False,
            indent=2
        )


def is_known(item: FeedItem, registry: dict) -> bool:
    """
    Check whether article already exists in registry.
    """

    return item.id in registry


def register_item(item: FeedItem, registry: dict) -> None:
    """
    Add article to registry.
    """

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
        "telegram_published": False,
        "telegram_message_id": None,
    }

