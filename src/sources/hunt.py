"""
Hunt.io source collector.

Collects Hunt.io Threat Research articles for configured
victim regions and publication date.

Source:
https://hunt.io/blog
"""

import hashlib
from datetime import datetime
from urllib.parse import urljoin

import requests
import yaml
from bs4 import BeautifulSoup

from core.former import FeedItem


CONFIG_FILE = "config.yaml"

BASE_URL = "https://hunt.io"
BLOG_URL = "https://hunt.io/blog"

MAX_PAGES = 100

USER_AGENT = (
    "Mozilla/5.0 "
    "(X11; Linux x86_64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/151.0.0.0 Safari/537.36"
)


def load_config():
    """
    Load application configuration.
    """

    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return yaml.safe_load(file)


def generate_id(url):
    """
    Generate stable article ID from URL.
    """

    return hashlib.sha256(
        url.strip().encode("utf-8")
    ).hexdigest()


def parse_date(date_text):
    """
    Parse Hunt.io publication date.

    Expected format:
        Aug 18, 2026
    """

    if not date_text:
        return None

    date_text = date_text.strip()

    try:

        return datetime.strptime(
            date_text,
            "%b %d, %Y"
        )

    except ValueError:

        return None


def normalize_region(value):
    """
    Normalize Hunt.io victim region.
    """

    if not value:
        return None

    value = value.strip()

    if "Europe" in value:
        return "EU"

    if "Global" in value:
        return "Global"

    if "Middle East" in value:
        return "Middle East"

    return None


def fetch_page(url):
    """
    Fetch Hunt.io page.
    """

    try:

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml"
                ),
            }
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as error:

        print(
            f"Failed to fetch Hunt.io page: {url}"
        )

        print(
            f"Error: {error}"
        )

        return None


def find_article_container(title_node):
    """
    Find the smallest parent container representing
    one Hunt.io article card.
    """

    current = title_node

    for _ in range(10):

        if current.parent is None:
            return None

        current = current.parent

        headings = current.find_all(
            "h3"
        )

        if len(headings) != 1:
            continue

        links = current.select(
            'a[href*="/blog/"]'
        )

        if not links:
            continue

        text = current.get_text(
            " ",
            strip=True
        )

        if "Threat Research" not in text:
            continue

        if not any(
            region in text
            for region in (
                "Europe",
                "Global",
                "Middle East",
            )
        ):
            continue

        return current

    return None


def extract_article(container):
    """
    Extract one article from a Hunt.io article card.
    """

    # --------------------------------------------------
    # TITLE
    # --------------------------------------------------

    title_node = container.find(
        "h3"
    )

    if not title_node:
        return None

    title = title_node.get_text(
        " ",
        strip=True
    )

    if not title:
        return None

    # --------------------------------------------------
    # URL
    # --------------------------------------------------

    article_url = None

    title_link = title_node.find(
        "a",
        href=True
    )

    if title_link:

        article_url = title_link.get(
            "href"
        )

    if not article_url:

        parent_link = title_node.find_parent(
            "a",
            href=True
        )

        if parent_link:

            article_url = parent_link.get(
                "href"
            )

    if not article_url:

        link_node = container.select_one(
            'a[href*="/blog/"]'
        )

        if link_node:

            article_url = link_node.get(
                "href"
            )

    if not article_url:
        return None

    article_url = urljoin(
        BASE_URL,
        article_url
    )

    # --------------------------------------------------
    # CATEGORY
    # --------------------------------------------------

    category = None

    for node in container.find_all("p"):

        text = node.get_text(
            " ",
            strip=True
        )

        if text == "Threat Research":

            category = text

            break

    if category is None:
        return None

    # --------------------------------------------------
    # VICTIM REGION
    # --------------------------------------------------

    victim_region = None

    for node in container.find_all("p"):

        text = node.get_text(
            " ",
            strip=True
        )

        region = normalize_region(
            text
        )

        if region:

            victim_region = region

            break

    if victim_region is None:
        return None

    # --------------------------------------------------
    # PUBLICATION DATE
    # --------------------------------------------------

    published = None

    for node in container.find_all("p"):

        text = node.get_text(
            " ",
            strip=True
        )

        parsed_date = parse_date(
            text
        )

        if parsed_date:

            published = parsed_date

            break

    if published is None:
        return None

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    summary = ""

    for node in container.find_all("p"):

        text = node.get_text(
            " ",
            strip=True
        )

        if not text:
            continue

        if text == "Threat Research":
            continue

        if normalize_region(text):
            continue

        if parse_date(text):
            continue

        summary = text

        break

    return {
        "title": title,
        "url": article_url,
        "published": published,
        "category": category,
        "victim_region": victim_region,
        "summary": summary,
    }


def fetch_hunt():
    """
    Fetch Hunt.io Threat Research articles.

    Filters:

        category:
            configured category

        victim_region:
            configured regions

        start_date:
            configured minimum publication date
    """

    config = load_config()

    hunt_config = (
        config
        .get("sources", {})
        .get("hunt", {})
    )

    if not hunt_config.get(
        "enabled",
        False
    ):

        print(
            "Hunt.io source is disabled."
        )

        return []

    source_name = hunt_config.get(
        "name",
        "Hunt.io"
    )

    hashtag = hunt_config.get(
        "hashtag",
        "huntio"
    )

    target_category = hunt_config.get(
        "category",
        "Threat Research"
    )

    target_regions = set(
        hunt_config.get(
            "victim_regions",
            []
        )
    )

    if not target_regions:

        print(
            "Hunt.io: no victim regions "
            "configured."
        )

        return []

    start_date_text = hunt_config.get(
        "start_date"
    )

    if not start_date_text:

        print(
            "Hunt.io: start_date is not configured."
        )

        return []

    try:

        start_date = datetime.strptime(
            start_date_text,
            "%Y-%m-%d"
        )

    except ValueError:

        print(
            "Hunt.io: invalid start_date: "
            f"{start_date_text}"
        )

        return []

    print(
        f"Fetching Hunt.io: {BLOG_URL}"
    )

    print(
        f"Category: {target_category}"
    )

    print(
        "Victim Regions: "
        f"{', '.join(sorted(target_regions))}"
    )

    print(
        "Start date: "
        f"{start_date.strftime('%Y-%m-%d')}"
    )

    articles = {}

    processed_urls = set()

    for page in range(
        1,
        MAX_PAGES + 1
    ):

        if page == 1:

            page_url = BLOG_URL

        else:

            page_url = (
                f"{BLOG_URL}"
                f"?page={page}"
            )

        print(
            f"\nFetching page {page}: "
            f"{page_url}"
        )

        html = fetch_page(
            page_url
        )

        if not html:
            break

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # --------------------------------------------------
        # ARTICLE HEADINGS
        # --------------------------------------------------

        title_nodes = soup.find_all(
            "h3"
        )

        if not title_nodes:

            print(
                "No article headings found."
            )

            break

        page_urls = set()

        old_articles = 0

        for title_node in title_nodes:

            container = find_article_container(
                title_node
            )

            if container is None:
                continue

            article = extract_article(
                container
            )

            if article is None:
                continue

            article_url = article["url"]

            if article_url in page_urls:
                continue

            page_urls.add(
                article_url
            )

            # --------------------------------------------------
            # DATE FILTER
            # --------------------------------------------------

            if article["published"] < start_date:

                old_articles += 1

                continue

            # --------------------------------------------------
            # CATEGORY FILTER
            # --------------------------------------------------

            if (
                article["category"]
                != target_category
            ):

                continue

            # --------------------------------------------------
            # REGION FILTER
            # --------------------------------------------------

            if (
                article["victim_region"]
                not in target_regions
            ):

                continue

            # --------------------------------------------------
            # GLOBAL DEDUPLICATION
            # --------------------------------------------------

            if article_url in processed_urls:
                continue

            processed_urls.add(
                article_url
            )

            article_id = generate_id(
                article_url
            )

            feed_item = FeedItem(
                id=article_id,
                source=source_name,
                source_type="research",
                title=article["title"],
                url=article_url,
                published=article["published"],
                categories=[
                    target_category
                ],
                tags=[
                    article["victim_region"]
                ],
                summary=article["summary"],
                hashtag=hashtag,
            )

            articles[article_id] = feed_item

            # --------------------------------------------------
            # DEBUG OUTPUT
            # --------------------------------------------------

            print(
                "\nProcessing: "
                f"{article['title']}"
            )

            print(
                f"URL: {article_url}"
            )

            print(
                "Category: "
                f"{article['category']}"
            )

            print(
                "Victim Region: "
                f"{article['victim_region']}"
            )

            print(
                "Published: "
                f"{article['published'].strftime('%Y-%m-%d')}"
            )

        # --------------------------------------------------
        # PAGINATION
        # --------------------------------------------------

        if old_articles > 0:

            print(
                "\nReached articles older "
                "than start date."
            )

            break

        if not page_urls:

            print(
                "No article URLs found "
                "on this page."
            )

            break

        next_page = soup.select_one(
            'a[aria-label="Next"]'
        )

        if not next_page:

            print(
                "No next page found."
            )

            break

    return list(
        articles.values()
    )


if __name__ == "__main__":

    articles = fetch_hunt()

    print(
        "\n" + "=" * 80
    )

    print(
        "TOTAL UNIQUE MATCHING ARTICLES: "
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
            "Categories: "
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

        print(
            f"Tags:       {', '.join(article.tags)}"
            ) 
