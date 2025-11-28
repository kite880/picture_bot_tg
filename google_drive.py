"""Google Drive integration for Picture Bot."""

import os
import logging
from pathlib import Path
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)

# Scopes for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class GoogleDriveManager:
    """Manages access to Google Drive files."""

    def __init__(self, credentials_file: str, folder_id: str):
        """
        Initialize Google Drive manager.

        Args:
            credentials_file: Path to service account JSON key
            folder_id: Google Drive folder ID to sync from
        """
        self.credentials_file = credentials_file
        self.folder_id = folder_id
        self.service = None
        self.images = []

        if not os.path.exists(credentials_file):
            raise FileNotFoundError(f"Credentials file not found: {credentials_file}")

        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive."""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_file, scopes=SCOPES
            )
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive authenticated successfully")
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive: {e}")
            raise

    def _get_image_extensions(self) -> set:
        """Get supported image extensions."""
        return {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    def load_images(self) -> bool:
        """Load all images from Google Drive folder."""
        try:
            # Query for image files in the folder
            query = f"'{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType)',
                pageSize=1000
            ).execute()

            files = results.get('files', [])

            # Filter for image files
            self.images = []
            image_extensions = self._get_image_extensions()

            for file in files:
                # Check if it's an image by extension
                name = file['name'].lower()
                if any(name.endswith(ext) for ext in image_extensions):
                    self.images.append({
                        'id': file['id'],
                        'name': file['name'],
                    })

            logger.info(f"Loaded {len(self.images)} images from Google Drive")
            return len(self.images) > 0

        except Exception as e:
            logger.error(f"Failed to load images from Google Drive: {e}")
            return False

    def get_image_list(self) -> list:
        """Get list of image names."""
        return [img['name'] for img in self.images]

    def download_image(self, file_id: str, file_name: str, output_path: str) -> bool:
        """
        Download image from Google Drive.

        Args:
            file_id: Google Drive file ID
            file_name: File name
            output_path: Local path to save file

        Returns:
            True if successful, False otherwise
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_path = os.path.join(output_path, file_name)

            with open(file_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

            logger.debug(f"Downloaded: {file_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to download {file_name}: {e}")
            return False

    def get_image_by_name(self, name: str) -> dict:
        """Get image info by name."""
        for img in self.images:
            if img['name'] == name:
                return img
        return None

    def get_random_image(self) -> dict:
        """Get a random image from the folder."""
        import random
        if not self.images:
            return None
        return random.choice(self.images)
