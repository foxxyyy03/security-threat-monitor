"""
Unit 42 source collector.

Fetches articles from the Unit 42 RSS feed, extracts article
categories from individual pages, filters configured categories,
and returns normalized FeedItem objects.
"""

import feedparser
import yaml
import requests

from bs4 import BeautifulSoup

from core.former import FeedItem
from core.registry import generate_id


CONFIG_FILE = "config.yaml"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_article_categories(url):
    """
    Open Unit 42 article page and extract article categories.
    """

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"Failed to fetch article: {url}")
        print(f"Error: {error}")
        return []

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    categories = []

    for link in soup.select("a.card-category"):
        category = link.get_text(strip=True)

        if category and category not in categories:
            categories.append(category)

    return categories


def parse_published_date(entry):
    """
    Convert RSS publication date to datetime.
    """

    if hasattr(entry, "published_parsed") and entry.published_parsed:
        from datetime import datetime

        return datetime(*entry.published_parsed[:6])

    return None


def fetch_unit42():

    config = load_config()

    unit42_config = config.get("unit42", {})

    if not unit42_config.get("enabled", False):
        print("Unit 42 source is disabled.")
        return []

    feed_url = unit42_config["feed_url"]

    allowed_categories = set(
        unit42_config.get("categories", [])
    )

    print(f"Fetching Unit 42 RSS: {feed_url}")

    feed = feedparser.parse(feed_url)

    if feed.bozo:
        print(
            f"Failed to parse Unit 42 RSS: {feed_url}"
        )
        return []

    articles = {}

    for entry in feed.entries:

        url = entry.get("link")

        if not url:
            continue

        title = entry.get(
            "title",
            ""
        ).strip()

        print(f"\nProcessing: {title}")
        print(f"URL: {url}")

        categories = get_article_categories(url)

        print(
            f"Categories: {categories}"
        )

        matched_categories = [
            category
            for category in categories
            if category in allowed_categories
        ]

        if not matched_categories:
            print(
                "Skipped: no matching category"
            )
            continue

        item_id = generate_id(url)

        item = FeedItem(
            id=item_id,
            source="Unit 42",
            source_type="research",
            title=title,
            url=url,
            published=parse_published_date(entry),
            categories=matched_categories,
            tags=[],
            summary=entry.get(
                "summary",
                ""
            ).strip(),
        )

        articles[url] = item

    return list(articles.values())


if __name__ == "__main__":

    articles = fetch_unit42()

    print("\n" + "=" * 80)
    print(
        f"TOTAL UNIQUE MATCHING ARTICLES: "
        f"{len(articles)}"
    )
    print("=" * 80)

    for article in articles:

        print("\n" + "-" * 80)

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
