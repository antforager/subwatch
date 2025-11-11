"""Reddit subreddit monitoring module."""
import time
from typing import List, Dict, Optional
import praw
from praw.exceptions import PRAWException


class RedditMonitor:
    """Monitor Reddit subreddit for new posts."""

    def __init__(self, client_id: str, client_secret: str, user_agent: str, subreddit_name: str):
        """Initialize Reddit client.

        Args:
            client_id: Reddit app client ID
            client_secret: Reddit app client secret
            user_agent: User agent string for Reddit API
            subreddit_name: Subreddit name to monitor (without r/)
        """
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.subreddit_name = subreddit_name
        self.subreddit = self.reddit.subreddit(subreddit_name)

    def get_posts_since(self, timestamp: Optional[float] = None) -> List[Dict]:
        """Fetch posts from the subreddit since a given timestamp.

        Args:
            timestamp: Unix timestamp to fetch posts after. If None, fetches recent posts.

        Returns:
            List of post dictionaries with relevant information
        """
        try:
            posts = []

            # Fetch recent posts from the subreddit
            limit = 100 if timestamp else 10

            for submission in self.subreddit.new(limit=limit):
                post_timestamp = submission.created_utc

                # Skip posts older than our last check
                if timestamp and post_timestamp <= timestamp:
                    continue

                # Build post data
                post_data = {
                    'title': submission.title,
                    'text': submission.selftext if submission.is_self else '',
                    'url': submission.url,
                    'permalink': f"https://www.reddit.com{submission.permalink}",
                    'author': str(submission.author) if submission.author else '[deleted]',
                    'ts': post_timestamp,
                    'score': submission.score,
                    'num_comments': submission.num_comments,
                    'is_self': submission.is_self,
                    'link_flair_text': submission.link_flair_text or '',
                    'over_18': submission.over_18,
                    'spoiler': submission.spoiler,
                    'stickied': submission.stickied,
                }

                posts.append(post_data)

            # Sort by timestamp (oldest first)
            posts.sort(key=lambda x: x['ts'])

            return posts

        except PRAWException as e:
            print(f"Error fetching posts from Reddit: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []

    def get_subreddit_name(self) -> str:
        """Get the subreddit name for display purposes.

        Returns:
            Subreddit display name
        """
        try:
            return self.subreddit.display_name
        except PRAWException:
            return self.subreddit_name

    def get_comments_since(self, timestamp: Optional[float] = None) -> List[Dict]:
        """Fetch comments from the subreddit since a given timestamp.

        Args:
            timestamp: Unix timestamp to fetch comments after. If None, fetches recent comments.

        Returns:
            List of comment dictionaries with relevant information
        """
        try:
            comments = []

            # Fetch recent comments from the subreddit
            limit = 100 if timestamp else 10

            for comment in self.subreddit.comments(limit=limit):
                comment_timestamp = comment.created_utc

                # Skip comments older than our last check
                if timestamp and comment_timestamp <= timestamp:
                    continue

                # Skip deleted/removed comments
                if comment.author is None:
                    continue

                # Build comment data
                comment_data = {
                    'text': comment.body,
                    'author': str(comment.author),
                    'ts': comment_timestamp,
                    'score': comment.score,
                    'permalink': f"https://www.reddit.com{comment.permalink}",
                    'post_title': comment.submission.title if hasattr(comment, 'submission') else '',
                    'post_url': f"https://www.reddit.com{comment.submission.permalink}" if hasattr(comment, 'submission') else '',
                }

                comments.append(comment_data)

            # Sort by timestamp (oldest first)
            comments.sort(key=lambda x: x['ts'])

            return comments

        except PRAWException as e:
            print(f"Error fetching comments from Reddit: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []

    def test_connection(self) -> bool:
        """Test if the Reddit connection is working.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to access the subreddit
            _ = self.subreddit.display_name
            return True
        except PRAWException as e:
            print(f"Connection test failed: {e}")
            return False
