"""
Source manager.

Loads and executes enabled source collectors.
Provides a common interface between individual sources
and the main application.
"""

from sources.unit42 import fetch_unit42
from sources.tenable import fetch_tenable
from sources.cert_ua import fetch_certua
from sources.sekoia import fetch_sekoia
from sources.hunt import fetch_hunt

SOURCE_COLLECTORS = {
    "unit42": fetch_unit42,
    "tenable": fetch_tenable,
    "certua": fetch_certua,
    "sekoia": fetch_sekoia,
    "huntio": fetch_hunt,
     }



def fetch_all_sources() -> list:
    """
    Fetch articles from all enabled source collectors.
    """

    articles = []

    for source_name, collector in SOURCE_COLLECTORS.items():

        print(
            f"\n{'=' * 80}"
        )

        print(
            f"Fetching source: {source_name}"
        )

        print(
            f"{'=' * 80}"
        )

        try:

            source_articles = collector()

            articles.extend(
                source_articles
            )

            print(
                f"Collected from "
                f"{source_name}: "
                f"{len(source_articles)}"
            )

        except Exception as error:

            print(
                f"Source failed: "
                f"{source_name}"
            )

            print(
                f"Error: {error}"
            )

    return articles

