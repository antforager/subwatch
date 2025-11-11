#!/usr/bin/env python3
"""Main script for Reddit to Discord monitor."""
import os
import time
import sys
import json
from dotenv import load_dotenv

from reddit_monitor import RedditMonitor
from discord_poster import DiscordPoster
from state_manager import StateManager
from keyword_matcher import KeywordMatcher


def load_subreddit_config(config_file: str = "subreddits.json") -> list:
    """Load subreddit configuration from JSON file.

    Args:
        config_file: Path to the configuration file

    Returns:
        List of subreddit configuration dictionaries
    """
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found")
        print("Please create subreddits.json with your subreddit-webhook mappings")
        sys.exit(1)

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            # Filter only enabled subreddits
            return [sub for sub in config if sub.get('enabled', True)]
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading configuration file: {e}")
        sys.exit(1)


def main():
    """Main function to run the monitor."""
    # Load environment variables
    load_dotenv()

    # Get Reddit API credentials
    reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
    reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    reddit_user_agent = os.getenv('REDDIT_USER_AGENT', 'Discord Monitor Bot')
    check_interval = int(os.getenv('CHECK_INTERVAL', '300'))

    # Validate Reddit credentials
    if not reddit_client_id:
        print("Error: REDDIT_CLIENT_ID not set in .env file")
        sys.exit(1)
    if not reddit_client_secret:
        print("Error: REDDIT_CLIENT_SECRET not set in .env file")
        sys.exit(1)

    # Load subreddit configuration
    subreddit_configs = load_subreddit_config()

    if not subreddit_configs:
        print("Error: No enabled subreddits found in subreddits.json")
        sys.exit(1)

    # Initialize state manager
    state = StateManager()

    # Initialize keyword matcher
    keyword_matcher = KeywordMatcher()
    keywords_enabled = len(keyword_matcher.get_keywords()) > 0

    if keywords_enabled:
        print(f"Keyword monitoring enabled: {', '.join(keyword_matcher.get_keywords())}")
    else:
        print("Keyword monitoring disabled (no keywords configured)")

    # Initialize monitors for each subreddit
    monitors = []
    for config in subreddit_configs:
        subreddit_name = config.get('subreddit')
        webhook_url = config.get('webhook_url')
        monitor_posts = config.get('monitor_posts', True)
        monitor_keywords = config.get('monitor_keywords', False)
        keyword_webhook_url = config.get('keyword_webhook_url', '')

        if not subreddit_name or not webhook_url:
            print(f"Warning: Invalid configuration entry: {config}")
            continue

        # Create monitor and poster for this subreddit
        monitor = RedditMonitor(reddit_client_id, reddit_client_secret, reddit_user_agent, subreddit_name)
        poster = DiscordPoster(webhook_url)

        # Test connection
        if not monitor.test_connection():
            print(f"Warning: Failed to connect to r/{subreddit_name}, skipping...")
            continue

        # Create keyword poster if keyword monitoring is enabled
        keyword_poster = None
        if monitor_keywords and keywords_enabled and keyword_webhook_url:
            keyword_poster = DiscordPoster(keyword_webhook_url)

        monitors.append({
            'subreddit': subreddit_name,
            'monitor': monitor,
            'poster': poster,
            'monitor_posts': monitor_posts,
            'monitor_keywords': monitor_keywords,
            'keyword_poster': keyword_poster
        })

        monitoring_status = []
        if monitor_posts:
            monitoring_status.append("posts")
        if monitor_keywords and keyword_poster:
            monitoring_status.append("keywords")

        print(f"✓ Configured r/{subreddit_name} ({', '.join(monitoring_status)})")

    if not monitors:
        print("Error: No valid subreddit monitors could be initialized")
        sys.exit(1)

    print(f"\nMonitoring {len(monitors)} subreddit(s)")
    print(f"Check interval: {check_interval} seconds")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            # Check each subreddit
            for item in monitors:
                subreddit_name = item['subreddit']
                monitor = item['monitor']
                poster = item['poster']
                monitor_posts = item['monitor_posts']
                monitor_keywords = item['monitor_keywords']
                keyword_poster = item['keyword_poster']

                # Get last check timestamps for this subreddit
                last_check_posts = state.get_last_check(f"{subreddit_name}_posts")
                last_check_comments = state.get_last_check(f"{subreddit_name}_comments")

                # Monitor regular posts
                if monitor_posts:
                    if last_check_posts:
                        print(f"[r/{subreddit_name}] Checking for new posts...")
                    else:
                        print(f"[r/{subreddit_name}] First run - checking recent posts...")

                    # Fetch new posts
                    posts = monitor.get_posts_since(last_check_posts)

                    if posts:
                        print(f"[r/{subreddit_name}] Found {len(posts)} new post(s)")

                        # Post to Discord
                        success_count = poster.post_batch(posts, subreddit_name)
                        print(f"[r/{subreddit_name}] Posted {success_count}/{len(posts)} post(s) to Discord")

                        # Update last check timestamp to the most recent post
                        latest_ts = max(post['ts'] for post in posts)
                        state.save_last_check(f"{subreddit_name}_posts", latest_ts)
                    else:
                        print(f"[r/{subreddit_name}] No new posts")

                # Monitor for keywords
                if monitor_keywords and keyword_poster and keywords_enabled:
                    if last_check_comments:
                        print(f"[r/{subreddit_name}] Checking for keyword matches...")
                    else:
                        print(f"[r/{subreddit_name}] First keyword check...")

                    # Fetch posts and comments for keyword matching
                    recent_posts = monitor.get_posts_since(last_check_comments)
                    recent_comments = monitor.get_comments_since(last_check_comments)

                    # Filter for keyword matches
                    matched_posts = keyword_matcher.filter_posts(recent_posts)
                    matched_comments = keyword_matcher.filter_comments(recent_comments)

                    total_matches = len(matched_posts) + len(matched_comments)

                    if total_matches > 0:
                        print(f"[r/{subreddit_name}] Found {total_matches} keyword match(es) ({len(matched_posts)} posts, {len(matched_comments)} comments)")

                        # Post keyword matches to Discord
                        if matched_posts:
                            success = keyword_poster.post_keyword_batch(matched_posts, subreddit_name, "post")
                            print(f"[r/{subreddit_name}] Posted {success}/{len(matched_posts)} matched post(s)")

                        if matched_comments:
                            success = keyword_poster.post_keyword_batch(matched_comments, subreddit_name, "comment")
                            print(f"[r/{subreddit_name}] Posted {success}/{len(matched_comments)} matched comment(s)")

                        # Update timestamp based on most recent item
                        all_items = recent_posts + recent_comments
                        if all_items:
                            latest_ts = max(item['ts'] for item in all_items)
                            state.save_last_check(f"{subreddit_name}_comments", latest_ts)
                    else:
                        print(f"[r/{subreddit_name}] No keyword matches")

                        # Still update timestamp if we checked anything
                        all_items = recent_posts + recent_comments
                        if all_items:
                            latest_ts = max(item['ts'] for item in all_items)
                            state.save_last_check(f"{subreddit_name}_comments", latest_ts)

            # Wait for next check
            print(f"\nNext check in {check_interval} seconds...\n")
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\nStopping monitor...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
