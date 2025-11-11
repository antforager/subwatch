"""State management for tracking last check timestamp."""
import os
import json
from typing import Optional, Dict


class StateManager:
    """Manage persistent state for the monitor."""

    def __init__(self, state_file: str = "last_check.json"):
        """Initialize state manager.

        Args:
            state_file: Path to the state file (JSON format)
        """
        self.state_file = state_file
        self._state = self._load_state()

    def _load_state(self) -> Dict[str, float]:
        """Load state from file.

        Returns:
            Dictionary mapping subreddit names to timestamps
        """
        if not os.path.exists(self.state_file):
            return {}

        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (ValueError, IOError, json.JSONDecodeError) as e:
            print(f"Error reading state file: {e}")
            return {}

    def _save_state(self) -> bool:
        """Save current state to file.

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self._state, f, indent=2)
            return True
        except IOError as e:
            print(f"Error writing state file: {e}")
            return False

    def get_last_check(self, subreddit: str) -> Optional[float]:
        """Get the timestamp of the last check for a specific subreddit.

        Args:
            subreddit: Name of the subreddit

        Returns:
            Unix timestamp of last check, or None if no previous check
        """
        return self._state.get(subreddit)

    def save_last_check(self, subreddit: str, timestamp: float) -> bool:
        """Save the timestamp of the last check for a specific subreddit.

        Args:
            subreddit: Name of the subreddit
            timestamp: Unix timestamp to save

        Returns:
            True if successful, False otherwise
        """
        self._state[subreddit] = timestamp
        return self._save_state()

    def reset(self, subreddit: Optional[str] = None) -> bool:
        """Reset the state for a specific subreddit or all subreddits.

        Args:
            subreddit: Name of the subreddit to reset, or None to reset all

        Returns:
            True if successful, False otherwise
        """
        try:
            if subreddit:
                # Reset specific subreddit
                if subreddit in self._state:
                    del self._state[subreddit]
                    return self._save_state()
                return True
            else:
                # Reset all - delete the file
                if os.path.exists(self.state_file):
                    os.remove(self.state_file)
                self._state = {}
                return True
        except IOError as e:
            print(f"Error resetting state: {e}")
            return False
