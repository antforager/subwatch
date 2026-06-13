"""Keyword matching and filtering module."""
import re
from typing import List, Dict, Optional, Iterable
import os
import json


class KeywordMatcher:
    """Match content against configured keywords."""

    # Fields checked against the blacklist. The blacklist is the final authority,
    # so it screens every field that is rendered into Discord and could carry the
    # unwanted phrase (body text, flair, author, and the linked URL).
    POST_BLACKLIST_FIELDS = ('title', 'text', 'link_flair_text', 'url', 'author')
    COMMENT_BLACKLIST_FIELDS = ('text', 'post_title', 'author')

    def __init__(self, config_file: str = "keywords.json"):
        """Initialize keyword matcher.

        Args:
            config_file: Path to keywords configuration file
        """
        self.config_file = config_file
        self.keywords = []
        self.blacklist = []
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
                self.keywords = self._clean_terms(config.get('keywords', []), 'keywords')
                self.blacklist = self._clean_terms(config.get('blacklist', []), 'blacklist')
                self.case_sensitive = config.get('case_sensitive', False)
                self.search_posts = config.get('search_posts', True)
                self.search_comments = config.get('search_comments', True)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading keyword config: {e}")

    @staticmethod
    def _clean_terms(terms, label: str) -> List[str]:
        """Keep only non-empty string terms, warning about anything dropped.

        This prevents a malformed config (a number, null, or a bare string
        instead of a list) from crashing matching at runtime.
        """
        if not isinstance(terms, list):
            print(f"Warning: '{label}' in config is not a list; ignoring it")
            return []

        cleaned = []
        for term in terms:
            if isinstance(term, str) and term.strip():
                cleaned.append(term)
            else:
                print(f"Warning: ignoring invalid {label} entry: {term!r}")
        return cleaned

    @staticmethod
    def _build_pattern(term: str) -> str:
        """Build a whole-word/phrase regex for term.

        Plain \\b...\\b anchors fail when a term begins or ends with a
        non-word character (e.g. '#ad'), because \\b only fires at a
        word/non-word transition. We instead assert "no adjacent word
        character" only on the side where the term itself is a word
        character, so punctuation-bounded terms still match.
        """
        prefix = r'(?<!\w)' if re.match(r'\w', term) else ''
        suffix = r'(?!\w)' if re.search(r'\w$', term) else ''
        return prefix + re.escape(term) + suffix

    def _find_matches(self, text: str, terms: List[str]) -> List[str]:
        """Return every term that appears in text as a whole word/phrase.

        Args:
            text: Text to search
            terms: Terms to look for

        Returns:
            List of matched terms (empty if none)
        """
        if not text or not terms:
            return []

        flags = 0 if self.case_sensitive else re.IGNORECASE
        return [term for term in terms
                if re.search(self._build_pattern(term), text, flags=flags)]

    def matches_keyword(self, text: str) -> List[str]:
        """Check if text contains any configured keywords.

        Args:
            text: Text to search

        Returns:
            List of matched keywords (empty if no matches)
        """
        return self._find_matches(text, self.keywords)

    def blacklisted_phrase(self, *texts: str) -> Optional[str]:
        """Return the first blacklisted phrase found across texts, or None.

        Args:
            texts: One or more text fields to screen

        Returns:
            The matched blacklist phrase, or None if nothing matched
        """
        for text in texts:
            found = self._find_matches(text, self.blacklist)
            if found:
                return found[0]
        return None

    def _is_blacklisted(self, item: Dict, fields: Iterable[str]) -> bool:
        """Check the given item fields against the blacklist, logging any hit.

        Args:
            item: Post or comment dictionary
            fields: Field names to screen

        Returns:
            True if any field matched the blacklist
        """
        blocked = self.blacklisted_phrase(*(item.get(f, '') for f in fields))
        if blocked:
            label = (item.get('title') or item.get('text', ''))[:60]
            print(f"  Blacklist: suppressed '{label}' (matched '{blocked}')")
            return True
        return False

    def remove_blacklisted_posts(self, posts: List[Dict]) -> List[Dict]:
        """Drop any posts matching the blacklist (regardless of keywords).

        Use this to enforce the blacklist on streams that are not keyword
        filtered, so suppressed content never reaches Discord through any path.

        Args:
            posts: List of post dictionaries

        Returns:
            Posts with blacklisted entries removed
        """
        if not self.blacklist:
            return posts
        return [post for post in posts
                if not self._is_blacklisted(post, self.POST_BLACKLIST_FIELDS)]

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
            # Blacklist takes final authority — skip post if any field matches
            if self._is_blacklisted(post, self.POST_BLACKLIST_FIELDS):
                continue

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
            # Blacklist takes final authority — screen the comment body and the
            # title of the post it belongs to.
            if self._is_blacklisted(comment, self.COMMENT_BLACKLIST_FIELDS):
                continue

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
