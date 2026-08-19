"""
Application entry point.

Coordinates source collectors and the article registry.
Identifies new, existing, and failed articles.

Telegram publication will be integrated into this workflow
after the source and registry layers are finalized.
"""

from sources.unit42 import fetch_unit42

from core.registry import (
    load_registry,
    save_registry,
    is_known,
    register_item,
)


def main():

    print("Starting Security Threat Monitor...\n")

    registry = load_registry()

    articles = fetch_unit42()

    new_articles = []
    existing_articles = []
    failed_articles = []

    for article in articles:

        if not is_known(article, registry):

            print(
                f"[NEW] {article.title}"
            )

            register_item(
                article,
                registry
            )

            new_articles.append(article)

        else:

            state = registry[article.id]

            status = state.get(
                "status",
                "unknown"
            )

            if status == "published":

                print(
                    f"[PUBLISHED] "
                    f"{article.title}"
                )

                existing_articles.append(
                    article
                )

            elif status == "failed":

                print(
                    f"[RETRY] "
                    f"{article.title}"
                )

                failed_articles.append(
                    article
                )

            else:

                print(
                    f"[EXISTING] "
                    f"{article.title}"
                )

                existing_articles.append(
                    article
                )

    save_registry(registry)

    print("\n" + "=" * 80)

    print(
        f"Articles received: "
        f"{len(articles)}"
    )

    print(
        f"New articles:      "
        f"{len(new_articles)}"
    )

    print(
        f"Already published:  "
        f"{len(existing_articles)}"
    )

    print(
        f"Failed / retry:     "
        f"{len(failed_articles)}"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()

