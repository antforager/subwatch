"""Keyword matching and filtering module."""
import re
from typing import List, Dict, Set
import os
import json


class KeywordMatcher:
    """Match content against configured keywords."""

    def __init__(self, config_file: str = "keywords.json"):
        """Initialize keyword matcher.

        Args:
            config_file: Path to keywords configuration file
        """
        self.config_file = config_file
        self.keywords = []
        self.case_sensitive = False
        self.search_posts = True
        self.search_comments = True
        self._load_config()

    def _load_config(self):
        """Load keyword configuration from file."""
        if not os.path.exists(self.config_file):
            print(f"Warning: Keyword config file '{self.config_file}' not found")
            return

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.keywords = config.get('keywords', [])
                self.case_sensitive = config.get('case_sensitive', False)
                self.search_posts = config.get('search_posts', True)
                self.search_comments = config.get('search_comments', True)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading keyword config: {e}")

    def matches_keyword(self, text: str) -> List[str]:
        """Check if text contains any configured keywords.

        Args:
            text: Text to search

        Returns:
            List of matched keywords (empty if no matches)
        """
        if not text or not self.keywords:
            return []

        matches = []
        search_text = text if self.case_sensitive else text.lower()

        for keyword in self.keywords:
            search_keyword = keyword if self.case_sensitive else keyword.lower()

            # Use word boundaries for better matching
            # This prevents matching "antgear" in "merchantgear"
            pattern = r'\b' + re.escape(search_keyword) + r'\b'

            if re.search(pattern, search_text, flags=0 if self.case_sensitive else re.IGNORECASE):
                matches.append(keyword)

        return matches

    def filter_posts(self, posts: List[Dict]) -> List[Dict]:
        """Filter posts that match keywords.

        Args:
            posts: List of post dictionaries

        Returns:
            List of posts with keyword matches, including 'matched_keywords' field
        """
        if not self.search_posts or not self.keywords:
            return []

        matching_posts = []
        for post in posts:
            # Check title and text
            title_matches = self.matches_keyword(post.get('title', ''))
            text_matches = self.matches_keyword(post.get('text', ''))

            all_matches = list(set(title_matches + text_matches))

            if all_matches:
                post_copy = post.copy()
                post_copy['matched_keywords'] = all_matches
                post_copy['match_location'] = []
                if title_matches:
                    post_copy['match_location'].append('title')
                if text_matches:
                    post_copy['match_location'].append('body')
                matching_posts.append(post_copy)

        return matching_posts

    def filter_comments(self, comments: List[Dict]) -> List[Dict]:
        """Filter comments that match keywords.

        Args:
            comments: List of comment dictionaries

        Returns:
            List of comments with keyword matches, including 'matched_keywords' field
        """
        if not self.search_comments or not self.keywords:
            return []

        matching_comments = []
        for comment in comments:
            matches = self.matches_keyword(comment.get('text', ''))

            if matches:
                comment_copy = comment.copy()
                comment_copy['matched_keywords'] = matches
                comment_copy['match_location'] = ['comment']
                matching_comments.append(comment_copy)

        return matching_comments

    def get_keywords(self) -> List[str]:
        """Get the list of configured keywords.

        Returns:
            List of keyword strings
        """
        return self.keywords.copy()
