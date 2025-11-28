"""Module for managing sent images history."""

import json
import os
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

HISTORY_FILE = "sent_history.json"


class HistoryManager:
    """Manages history of sent images."""

    def __init__(self):
        """Initialize history manager."""
        self.history_file = Path(HISTORY_FILE)
        self.sent_images = self._load_history()

    def _load_history(self) -> set:
        """Load sent images from history file."""
        if not self.history_file.exists():
            logger.info("History file not found, creating new one")
            return set()

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Support both old format (list) and new format (dict)
                if isinstance(data, dict):
                    images = set(data.get('images', []))
                else:
                    images = set(data)
                logger.info(f"Loaded history of {len(images)} sent images")
                return images
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading history: {e}")
            return set()

    def _save_history(self):
        """Save sent images to history file."""
        try:
            data = {
                'images': list(self.sent_images),
                'last_updated': datetime.now().isoformat(),
                'total_count': len(self.sent_images)
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"History saved ({len(self.sent_images)} images)")
        except IOError as e:
            logger.error(f"Error saving history: {e}")

    def add_image(self, image_path: str):
        """Add image to sent history."""
        self.sent_images.add(str(image_path))
        self._save_history()
        logger.debug(f"Image added to history: {os.path.basename(image_path)}")

    def is_sent(self, image_path: str) -> bool:
        """Check if image has been sent before."""
        return str(image_path) in self.sent_images

    def get_unsent_images(self, available_images: list) -> list:
        """Get list of images that haven't been sent."""
        unsent = [img for img in available_images if not self.is_sent(img)]
        return unsent

    def get_stats(self) -> dict:
        """Get statistics about sent images."""
        return {
            'total_sent': len(self.sent_images),
            'history_file': str(self.history_file)
        }

    def reset_history(self):
        """Reset all history."""
        old_count = len(self.sent_images)
        self.sent_images.clear()
        self._save_history()
        logger.info(f"History reset! Cleared {old_count} entries")
        return old_count

    def remove_image(self, image_path: str) -> bool:
        """Remove specific image from history."""
        if str(image_path) in self.sent_images:
            self.sent_images.remove(str(image_path))
            self._save_history()
            logger.info(f"Removed from history: {os.path.basename(image_path)}")
            return True
        return False
