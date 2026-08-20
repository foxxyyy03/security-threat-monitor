"""
Message formatting.

Converts normalized FeedItem objects into formatted messages
for Telegram publication.
"""

from html import escape

from core.former import FeedItem


DEFAULT_HASHTAG = "threats"


def format_telegram_message(
    item: FeedItem
) -> str:
    """
    Format a FeedItem as a Telegram HTML message.
    """

    categories = " · ".join(
        escape(category)
        for category in item.categories
    )

    message = (
        f"#{escape(item.hashtag)} "
        f"#{DEFAULT_HASHTAG}\n"
        f"<b>{escape(item.title)}</b>\n\n"
        f"<i>{categories}</i>\n"
        f"{escape(item.url)}"
    )

    return message

