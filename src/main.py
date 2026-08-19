"""
Application entry point.

Coordinates source collectors, article registry and Telegram
publication workflow.

Articles are registered before publication so that failed
Telegram deliveries can be retried on subsequent runs.
"""

from sources.unit42 import fetch_unit42

from core.registry import (
    load_registry,
    save_registry,
    is_known,
    register_item,
    mark_telegram_success,
    mark_telegram_failed,
)

from core.telegram import send_message


def main():

    print("Starting Security Threat Monitor...\n")

    registry = load_registry()

    articles = fetch_unit42()

    new_articles = []
    retry_articles = []
    published_articles = []
    failed_articles = []

    for article in articles:

        # Article has never been seen before
        if not is_known(article, registry):

            print(
                f"\n[NEW] {article.title}"
            )

            register_item(
                article,
                registry
            )

            # Save immediately.
            # If Telegram fails, the article remains
            # registered and can be retried later.
            save_registry(registry)

            new_articles.append(article)

        else:

            state = registry[article.id]

            status = state.get(
                "status",
                "unknown"
            )

            if status == "published":

                print(
                    f"\n[PUBLISHED] "
                    f"{article.title}"
                )

                published_articles.append(
                    article
                )

                continue

            if status == "failed":

                print(
                    f"\n[RETRY] "
                    f"{article.title}"
                )

                retry_articles.append(
                    article
                )

                continue

            if status == "discovered":

                print(
                    f"\n[UNPUBLISHED] "
                    f"{article.title}"
                )

                retry_articles.append(
                    article
                )

                continue

            print(
                f"\n[UNKNOWN STATUS] "
                f"{article.title}"
            )

            retry_articles.append(
                article
            )

    # New articles + failed/unpublished articles
    # are candidates for Telegram publication.
    articles_to_publish = (
        new_articles + retry_articles
    )

    print("\n" + "=" * 80)
    print(
        f"Articles received:  {len(articles)}"
    )
    print(
        f"New articles:       {len(new_articles)}"
    )
    print(
        f"Already published:  "
        f"{len(published_articles)}"
    )
    print(
        f"To publish/retry:   "
        f"{len(articles_to_publish)}"
    )
    print("=" * 80)

    # Publish articles to Telegram
    for article in articles_to_publish:

        print(
            f"\n[TELEGRAM] "
            f"{article.title}"
        )

        try:

            message_id = send_message(
                article
            )

            mark_telegram_success(
                article.id,
                message_id,
                registry
            )

            save_registry(registry)

            print(
                f"[SUCCESS] "
                f"Telegram message ID: "
                f"{message_id}"
            )

        except Exception as error:

            error_message = str(error)

            mark_telegram_failed(
                article.id,
                error_message,
                registry
            )

            save_registry(registry)

            failed_articles.append(
                article
            )

            print(
                f"[FAILED] "
                f"{article.title}"
            )

            print(
                f"Error: {error_message}"
            )

    print("\n" + "=" * 80)
    print("Run completed.")
    print(
        f"Published this run: "
        f"{len(articles_to_publish) - len(failed_articles)}"
    )
    print(
        f"Failed this run:    "
        f"{len(failed_articles)}"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
"""
Application entry point.

Coordinates source collectors, article registry and Telegram
publication workflow.

Sources are managed independently through source_manager.py.
"""

from core.source_manager import fetch_all_sources

from core.registry import (
    load_registry,
    save_registry,
    is_known,
    register_item,
    mark_telegram_success,
    mark_telegram_failed,
)

from core.telegram import send_message


def main():

    print(
        "Starting Security Threat Monitor...\n"
    )

    registry = load_registry()

    articles = fetch_all_sources()

    new_articles = []
    retry_articles = []
    published_articles = []
    failed_articles = []

    for article in articles:

        if not is_known(
            article,
            registry
        ):

            print(
                f"\n[NEW] {article.title}"
            )

            register_item(
                article,
                registry
            )

            save_registry(
                registry
            )

            new_articles.append(
                article
            )

        else:

            state = registry[
                article.id
            ]

            status = state.get(
                "status",
                "unknown"
            )

            if status == "published":

                print(
                    f"\n[PUBLISHED] "
                    f"{article.title}"
                )

                published_articles.append(
                    article
                )

                continue

            if status == "failed":

                print(
                    f"\n[RETRY] "
                    f"{article.title}"
                )

                retry_articles.append(
                    article
                )

                continue

            if status == "discovered":

                print(
                    f"\n[UNPUBLISHED] "
                    f"{article.title}"
                )

                retry_articles.append(
                    article
                )

                continue

            print(
                f"\n[UNKNOWN STATUS] "
                f"{article.title}"
            )

            retry_articles.append(
                article
            )

    articles_to_publish = (
        new_articles +
        retry_articles
    )

    print(
        "\n" + "=" * 80
    )

    print(
        f"Articles received: "
        f"{len(articles)}"
    )

    print(
        f"New articles: "
        f"{len(new_articles)}"
    )

    print(
        f"Already published: "
        f"{len(published_articles)}"
    )

    print(
        f"To publish/retry: "
        f"{len(articles_to_publish)}"
    )

    print(
        "=" * 80
    )

    for article in articles_to_publish:

        print(
            f"\n[TELEGRAM] "
            f"{article.title}"
        )

        try:

            message_id = send_message(
                article
            )

            mark_telegram_success(
                article.id,
                message_id,
                registry
            )

            save_registry(
                registry
            )

            print(
                f"[SUCCESS] "
                f"Telegram message ID: "
                f"{message_id}"
            )

        except Exception as error:

            error_message = str(
                error
            )

            mark_telegram_failed(
                article.id,
                error_message,
                registry
            )

            save_registry(
                registry
            )

            failed_articles.append(
                article
            )

            print(
                f"[FAILED] "
                f"{article.title}"
            )

            print(
                f"Error: "
                f"{error_message}"
            )

    print(
        "\n" + "=" * 80
    )

    print(
        "Run completed."
    )

    print(
        f"Published this run: "
        f"{len(articles_to_publish) - len(failed_articles)}"
    )

    print(
        f"Failed this run: "
        f"{len(failed_articles)}"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":
    main()

