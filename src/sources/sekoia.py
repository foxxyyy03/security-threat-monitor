import hashlib
from datetime import datetime
from urllib.parse import urljoin
from datetime import datetime
import requests
import yaml
from bs4 import BeautifulSoup

from core.former import FeedItem


CONFIG_FILE = "config.yaml"

BASE_URL = "https://www.sekoia.com"
BLOG_URL = f"{BASE_URL}/blog"

START_DATE = datetime(2026, 6, 1)
MAX_PAGES = 20


def load_config():
    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return yaml.safe_load(file)


def generate_id(url):
    return hashlib.sha256(
        url.strip().encode("utf-8")
    ).hexdigest()


def parse_date(date_text):
    if not date_text:
        return None

    try:
        return datetime.strptime(
            date_text.strip(),
            "%B %d, %Y"
        )
    except ValueError:
        return None


def fetch_page(url):
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as error:
        print(
            f"Failed to fetch Sekoia page: {url}"
        )
        print(
            f"Error: {error}"
        )

        return None


def fetch_sekoia():
    """
    Fetch Threat Research & Intelligence articles
    published from START_DATE onwards.
    """

    config = load_config()

    sekoia_config = config.get(
        "sources",
        {}
    ).get(
        "sekoia",
        {}
    )

    if not sekoia_config.get(
        "enabled",
        False
    ):
        print(
            "Sekoia source is disabled."
        )

        return []

    source_name = sekoia_config.get(
        "name",
        "Sekoia"
    )

    hashtag = sekoia_config.get(
        "hashtag",
        "sekoia"
    )

    target_category = sekoia_config.get(
        "category",
        "Threat Research & Intelligence"
    )

    articles = {}
    seen_urls = set()

    stop_pagination = False

    for page in range(1, MAX_PAGES + 1):

        if page == 1:
            url = BLOG_URL
        else:
            url = (
                f"{BLOG_URL}"
                f"?08108354_page={page}"
            )

        print(
            f"\nFetching Sekoia page {page}: "
            f"{url}"
        )

        html = fetch_page(url)

        if not html:
            break

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        article_nodes = soup.select(
            "div.blog-list_item.w-dyn-item"
        )

        if not article_nodes:
            print(
                "No articles found. "
                "Stopping pagination."
            )
            break

        new_articles = 0
        old_articles_on_page = 0

        for article_node in article_nodes:

            categories = [
                node.get_text(
                    " ",
                    strip=True
                )
                for node in article_node.select(
                    '[fs-list-field="filter"]'
                )
            ]

            title_node = article_node.select_one(
                '[fs-list-field="title"]'
            )

            description_node = article_node.select_one(
                '[fs-list-field="description"]'
            )

            link_node = article_node.select_one(
                'a[href^="/blog/"]'
            )

            date_node = article_node.select_one(
                ".text-size-small.text-color-alternate"
            )

            if not title_node or not link_node:
                continue

            title = title_node.get_text(
                " ",
                strip=True
            )

            href = link_node.get(
                "href"
            )

            if not href:
                continue

            article_url = urljoin(
                BASE_URL,
                href
            )

            published = None

            if date_node:
                published = parse_date(
                    date_node.get_text(
                        " ",
                        strip=True
                    )
                )

            if published is None:
                print(
                    f"Skipped: unable to parse date: "
                    f"{title}"
                )
                continue

            # Articles are ordered newest -> oldest.
            # Once we reach articles older than START_DATE,
            # older pages can be skipped.
            if published < START_DATE:

                old_articles_on_page += 1

                continue

            if target_category not in categories:
                continue

            if article_url in seen_urls:
                continue

            seen_urls.add(
                article_url
            )

            description = ""

            if description_node:
                description = (
                    description_node
                    .get_text(
                        " ",
                        strip=True
                    )
                )

            article_id = generate_id(
                article_url
            )

            articles[article_id] = FeedItem(
                id=article_id,
                source=source_name,
                source_type="research",
                title=title,
                url=article_url,
                published=published,
                categories=[
                    target_category
                ],
                tags=[],
                summary=description,
                hashtag=hashtag,
            )

            new_articles += 1

            print(
                f"Processing: {title}"
            )

            print(
                f"Published: "
                f"{published.strftime('%Y-%m-%d')}"
            )

            print(
                f"URL: {article_url}"
            )

        # If every article on this page is older
        # than START_DATE, stop pagination.
        if old_articles_on_page == len(
            article_nodes
        ):
            print(
                f"All articles on page {page} "
                f"are older than "
                f"{START_DATE.strftime('%Y-%m-%d')}."
            )

            stop_pagination = True

        if stop_pagination:
            break

        next_page = soup.select_one(
            'a.w-pagination-next[aria-label="Next Page"]'
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

    articles = fetch_sekoia()

    print(
        "\n" + "=" * 80
    )

    print(
        f"TOTAL SEKOIA ARTICLES: "
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
