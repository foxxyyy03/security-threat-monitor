"""
Core data models.

Defines the common FeedItem structure used by all data sources.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FeedItem:
    """
    Common normalized representation of a security information item.
    """

    id: str
    source: str
    source_type: str
    title: str
    url: str
    published: datetime | None = None
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    summary: str = ""
    hashtag: str = ""
