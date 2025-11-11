"""Discord webhook poster module."""
import requests
from typing import Dict, Optional


class DiscordPoster:
    """Post messages to Discord via webhook."""

    def __init__(self, webhook_url: str):
        """Initialize Discord poster.

        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url

    def post_message(self, message: Dict, channel_name: str = "Reddit") -> bool:
        """Post a Reddit post to Discord.

        Args:
            message: Post dictionary with Reddit post information
            channel_name: Name of the subreddit for display

        Returns:
            True if successful, False otherwise
        """
        # Extract post information
        title = message.get('title', 'Untitled')
        text = message.get('text', '')
        author = message.get('author', '[deleted]')
        permalink = message.get('permalink', '')
        url = message.get('url', '')
        score = message.get('score', 0)
        num_comments = message.get('num_comments', 0)
        is_self = message.get('is_self', False)
        flair = message.get('link_flair_text', '')
        is_nsfw = message.get('over_18', False)
        is_spoiler = message.get('spoiler', False)

        # Truncate long self-text
        if text and len(text) > 300:
            text = text[:297] + "..."

        # Build description
        description_parts = []
        if text:
            description_parts.append(text)
        elif not is_self:
            description_parts.append(f"[Link Post]({url})")

        description = "\n".join(description_parts) if description_parts else "_No text content_"

        # Determine embed color based on post type
        color = 16729344  # Reddit orange by default
        if is_nsfw:
            color = 16711680  # Red for NSFW
        elif is_spoiler:
            color = 8421504  # Gray for spoiler

        # Create embed for better formatting
        embed = {
            "title": title[:256],  # Discord title limit
            "description": description,
            "color": color,
            "url": permalink,
            "fields": [
                {
                    "name": "Author",
                    "value": f"u/{author}",
                    "inline": True
                },
                {
                    "name": "Score",
                    "value": f"\u2B06\uFE0F {score}",
                    "inline": True
                },
                {
                    "name": "Comments",
                    "value": f"\U0001F4AC {num_comments}",
                    "inline": True
                }
            ],
            "footer": {
                "text": f"r/{channel_name}"
            }
        }

        # Add flair if present
        if flair:
            embed["fields"].append({
                "name": "Flair",
                "value": flair,
                "inline": True
            })

        # Add NSFW/Spoiler warnings
        warnings = []
        if is_nsfw:
            warnings.append("NSFW")
        if is_spoiler:
            warnings.append("Spoiler")
        if warnings:
            embed["fields"].append({
                "name": "⚠️ Warnings",
                "value": " | ".join(warnings),
                "inline": False
            })

        payload = {
            "embeds": [embed]
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error posting to Discord: {e}")
            return False

    def post_batch(self, messages: list, channel_name: str = "Reddit") -> int:
        """Post multiple Reddit posts to Discord.

        Args:
            messages: List of post dictionaries
            channel_name: Name of the subreddit for display

        Returns:
            Number of successfully posted messages
        """
        success_count = 0
        for msg in messages:
            if self.post_message(msg, channel_name):
                success_count += 1
            # Small delay to avoid rate limiting
            import time
            time.sleep(0.5)

        return success_count

    def post_keyword_match(self, item: Dict, channel_name: str = "Reddit", item_type: str = "post") -> bool:
        """Post a keyword-matched post or comment to Discord.

        Args:
            item: Post or comment dictionary with keyword match information
            channel_name: Name of the subreddit for display
            item_type: Either "post" or "comment"

        Returns:
            True if successful, False otherwise
        """
        import time

        # Extract common information
        author = item.get('author', '[deleted]')
        permalink = item.get('permalink', '')
        matched_keywords = item.get('matched_keywords', [])
        match_location = item.get('match_location', [])

        # Determine color based on item type
        color = 16753920  # Orange for keyword matches

        if item_type == "comment":
            # Comment format
            text = item.get('text', '')
            post_title = item.get('post_title', 'Unknown Post')
            post_url = item.get('post_url', '')
            score = item.get('score', 0)

            # Truncate long comments
            if text and len(text) > 300:
                text = text[:297] + "..."

            embed = {
                "title": f"🔍 Keyword Match: Comment in r/{channel_name}",
                "description": text,
                "color": color,
                "url": permalink,
                "fields": [
                    {
                        "name": "Matched Keywords",
                        "value": ", ".join(f"`{kw}`" for kw in matched_keywords),
                        "inline": False
                    },
                    {
                        "name": "Post",
                        "value": f"[{post_title}]({post_url})" if post_url else post_title,
                        "inline": False
                    },
                    {
                        "name": "Author",
                        "value": f"u/{author}",
                        "inline": True
                    },
                    {
                        "name": "Score",
                        "value": f"⬆️ {score}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"r/{channel_name} • Comment"
                }
            }
        else:
            # Post format (similar to regular post but with keyword highlight)
            title = item.get('title', 'Untitled')
            text = item.get('text', '')
            url = item.get('url', '')
            score = item.get('score', 0)
            num_comments = item.get('num_comments', 0)
            is_self = item.get('is_self', False)
            flair = item.get('link_flair_text', '')

            # Truncate long self-text
            if text and len(text) > 300:
                text = text[:297] + "..."

            # Build description
            description_parts = []
            if text:
                description_parts.append(text)
            elif not is_self:
                description_parts.append(f"[Link Post]({url})")

            description = "\n".join(description_parts) if description_parts else "_No text content_"

            embed = {
                "title": f"🔍 {title[:230]}",  # Leave room for emoji
                "description": description,
                "color": color,
                "url": permalink,
                "fields": [
                    {
                        "name": "Matched Keywords",
                        "value": ", ".join(f"`{kw}`" for kw in matched_keywords),
                        "inline": False
                    },
                    {
                        "name": "Location",
                        "value": ", ".join(match_location),
                        "inline": False
                    },
                    {
                        "name": "Author",
                        "value": f"u/{author}",
                        "inline": True
                    },
                    {
                        "name": "Score",
                        "value": f"⬆️ {score}",
                        "inline": True
                    },
                    {
                        "name": "Comments",
                        "value": f"💬 {num_comments}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"r/{channel_name} • Post"
                }
            }

            if flair:
                embed["fields"].insert(1, {
                    "name": "Flair",
                    "value": flair,
                    "inline": True
                })

        payload = {
            "embeds": [embed]
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error posting keyword match to Discord: {e}")
            return False

    def post_keyword_batch(self, items: list, channel_name: str = "Reddit", item_type: str = "post") -> int:
        """Post multiple keyword matches to Discord.

        Args:
            items: List of post or comment dictionaries with keyword matches
            channel_name: Name of the subreddit for display
            item_type: Either "post" or "comment"

        Returns:
            Number of successfully posted items
        """
        import time
        success_count = 0
        for item in items:
            if self.post_keyword_match(item, channel_name, item_type):
                success_count += 1
            # Small delay to avoid rate limiting
            time.sleep(0.5)

        return success_count
