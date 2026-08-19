"""
Tenable source collector.

Fetches Cyber Exposure Alerts from the official Tenable RSS feed
and converts them into normalized FeedItem objects.
"""

import hashlib
from datetime import datetime

import feedparser
import yaml

from core.former import FeedItem


CONFIG_FILE = "config.yaml"


def load_config():
    """Load application configuration."""

    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return yaml.safe_load(file)


def generate_id(url: str) -> str:
    """Generate a stable article ID from its URL."""

    return hashlib.sha256(
        url.strip().encode("utf-8")
    ).hexdigest()


def parse_published_date(entry):
    """
    Parse publication date from an RSS entry.

    Returns a datetime object or None if the date
    cannot be parsed.
    """

    published = entry.get(
        "published_parsed"
    )

    if not published:
        return None

    return datetime(
        published.tm_year,
        published.tm_mon,
        published.tm_mday,
        published.tm_hour,
        published.tm_min,
        published.tm_sec,
    )


def fetch_tenable():
    """
    Fetch Cyber Exposure Alerts from Tenable RSS.

    Returns a list of normalized FeedItem objects.
    """

    config = load_config()

    sources_config = config.get(
        "sources",
        {}
    )

    tenable_config = sources_config.get(
        "tenable",
        {}
    )

    if not tenable_config.get(
        "enabled",
        False
    ):

        print(
            "Tenable source is disabled."
        )

        return []

    feed_url = tenable_config.get(
        "feed_url"
    )

    source_name = tenable_config.get(
        "name",
        "Tenable"
    )

    hashtag = tenable_config.get(
        "hashtag",
        "tenable"
    )

    if not feed_url:

        print(
            "Tenable feed URL is not configured."
        )

        return []

    print(
        f"Fetching Tenable RSS: "
        f"{feed_url}"
    )

    feed = feedparser.parse(
        feed_url
    )

    if feed.bozo:

        print(
            f"Failed to parse Tenable RSS: "
            f"{feed_url}"
        )

        return []

    articles = {}

    for entry in feed.entries:

        url = entry.get(
            "link"
        )

        if not url:
            continue

        title = entry.get(
            "title",
            ""
        ).strip()

        if not title:
            continue

        print(
            f"\nProcessing: {title}"
        )

        print(
            f"URL: {url}"
        )

        article_id = generate_id(
            url
        )

        article = FeedItem(
            id=article_id,
            source=source_name,
            source_type="research",
            title=title,
            url=url,
            published=parse_published_date(
                entry
            ),
            categories=[
                "Cyber Exposure Alerts"
            ],
            tags=[],
            summary=entry.get(
                "summary",
                ""
            ).strip(),
            hashtag=hashtag,
        )

        articles[article_id] = article

    return list(
        articles.values()
    )


if __name__ == "__main__":

    articles = fetch_tenable()

    print(
        "\n" + "=" * 80
    )

    print(
        f"TOTAL TENABLE ARTICLES: "
        f"{len(articles)}"
    )

    print(
        "=" * 80
    )

    for article in articles:

        print(
            "\n" + "-" * 80
        )

        print(
            f"ID:         {article.id}"
        )

        print(
            f"Source:     {article.source}"
        )

        print(
            f"Type:       {article.source_type}"
        )

        print(
            f"Categories: "
            f"{', '.join(article.categories)}"
        )

        print(
            f"Title:      {article.title}"
        )

        print(
            f"Published:  {article.published}"
        )

        print(
            f"URL:        {article.url}"
        )

