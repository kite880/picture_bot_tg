"""Sync local images folder to Google Drive automatically."""

import os
import logging
import time
from pathlib import Path
from config import Config
from google_drive import GoogleDriveManager
from googleapiclient.http import MediaFileUpload

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class GoogleDriveSync:
    """Sync local folder to Google Drive."""

    def __init__(self, credentials_file: str, folder_id: str, local_path: str):
        """Initialize sync manager."""
        self.credentials_file = credentials_file
        self.folder_id = folder_id
        self.local_path = local_path
        self.gd_manager = GoogleDriveManager(credentials_file, folder_id)
        self.uploaded_files = set()

    def get_local_images(self) -> list:
        """Get list of local image files."""
        if not os.path.exists(self.local_path):
            logger.error(f"Local path not found: {self.local_path}")
            return []

        images_path = Path(self.local_path)
        local_images = [
            f.name for f in images_path.iterdir()
            if f.is_file() and f.suffix.lower() in Config.IMAGE_EXTENSIONS
        ]
        return local_images

    def get_gdrive_images(self) -> list:
        """Get list of images on Google Drive."""
        self.gd_manager.load_images()
        return self.gd_manager.get_image_list()

    def upload_image(self, file_name: str) -> bool:
        """Upload image to Google Drive."""
        try:
            file_path = os.path.join(self.local_path, file_name)

            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False

            # Create file metadata
            file_metadata = {
                'name': file_name,
                'parents': [self.folder_id]
            }

            # Upload file
            media = MediaFileUpload(file_path)
            file = self.gd_manager.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            logger.info(f"Uploaded: {file_name} (ID: {file['id']})")
            return True

        except Exception as e:
            logger.error(f"Failed to upload {file_name}: {e}")
            return False

    def sync_once(self) -> int:
        """Sync local folder to Google Drive once. Returns number of uploaded files."""
        logger.info("Starting sync...")

        local_images = self.get_local_images()
        gdrive_images = self.get_gdrive_images()

        # Find new images
        new_images = [img for img in local_images if img not in gdrive_images]

        if not new_images:
            logger.info("No new images to upload")
            return 0

        logger.info(f"Found {len(new_images)} new images to upload")

        uploaded_count = 0
        for image in new_images:
            if self.upload_image(image):
                uploaded_count += 1

        logger.info(f"Uploaded {uploaded_count}/{len(new_images)} images")
        return uploaded_count

    def sync_loop(self, interval: int = 300):
        """Continuously sync folder. Interval in seconds (default 5 min)."""
        logger.info(f"Starting sync loop (interval: {interval}s)")

        try:
            while True:
                try:
                    self.sync_once()
                except Exception as e:
                    logger.error(f"Error in sync loop: {e}")

                logger.info(f"Next sync in {interval} seconds...")
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Sync stopped by user")


def main():
    """Main function."""
    logger.info("Google Drive Sync Tool")

    # Validate config
    is_valid, errors = Config.is_valid()
    if not is_valid:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return

    if Config.IMAGE_SOURCE != "google_drive":
        logger.error("This tool only works with IMAGE_SOURCE=google_drive")
        return

    if not Config.IMAGES_PATH or not os.path.exists(Config.IMAGES_PATH):
        logger.error(f"Local images path not found: {Config.IMAGES_PATH}")
        return

    # Start sync
    sync = GoogleDriveSync(
        Config.GOOGLE_DRIVE_CREDENTIALS,
        Config.GOOGLE_DRIVE_FOLDER_ID,
        Config.IMAGES_PATH
    )

    # Sync every 5 minutes
    sync.sync_loop(interval=300)


if __name__ == "__main__":
    main()
