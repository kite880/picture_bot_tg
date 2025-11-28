"""Configuration module for Picture Bot."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class."""

    # Telegram Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    # Image source: local or google_drive
    IMAGE_SOURCE = os.getenv("IMAGE_SOURCE", "local")

    # Local Images
    IMAGES_PATH = os.getenv("IMAGES_PATH")

    # Google Drive
    GOOGLE_DRIVE_CREDENTIALS = os.getenv("GOOGLE_DRIVE_CREDENTIALS", "credentials.json")
    GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    GOOGLE_DRIVE_CACHE_DIR = os.getenv("GOOGLE_DRIVE_CACHE_DIR", "./image_cache")

    # Schedule
    SEND_INTERVAL = int(os.getenv("SEND_INTERVAL", 2))
    START_HOUR = int(os.getenv("START_HOUR", 9))
    END_HOUR = int(os.getenv("END_HOUR", 21))

    # Supported image extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    @staticmethod
    def is_valid():
        """Check if configuration is valid."""
        errors = []

        if not Config.BOT_TOKEN or Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            errors.append("BOT_TOKEN not configured in .env file")

        if not Config.CHAT_ID:
            errors.append("CHAT_ID not set in .env file")

        # Validate based on image source
        if Config.IMAGE_SOURCE == "local":
            if not Config.IMAGES_PATH or Config.IMAGES_PATH == "/path/to/your/images/folder":
                errors.append("IMAGES_PATH not configured in .env file")
            elif not os.path.exists(Config.IMAGES_PATH):
                errors.append(f"Images path does not exist: {Config.IMAGES_PATH}")

        elif Config.IMAGE_SOURCE == "google_drive":
            if not Config.GOOGLE_DRIVE_FOLDER_ID or Config.GOOGLE_DRIVE_FOLDER_ID == "your_folder_id_here":
                errors.append("GOOGLE_DRIVE_FOLDER_ID not configured in .env file")
            if not os.path.exists(Config.GOOGLE_DRIVE_CREDENTIALS):
                errors.append(f"Google Drive credentials file not found: {Config.GOOGLE_DRIVE_CREDENTIALS}")
        else:
            errors.append(f"Invalid IMAGE_SOURCE: {Config.IMAGE_SOURCE}. Use 'local' or 'google_drive'")

        if Config.SEND_INTERVAL <= 0:
            errors.append("SEND_INTERVAL must be greater than 0")

        if Config.START_HOUR < 0 or Config.START_HOUR > 23:
            errors.append("START_HOUR must be between 0 and 23")

        if Config.END_HOUR < 0 or Config.END_HOUR > 23:
            errors.append("END_HOUR must be between 0 and 23")

        if Config.START_HOUR >= Config.END_HOUR:
            errors.append("START_HOUR must be less than END_HOUR")

        return len(errors) == 0, errors

    @staticmethod
    def get_validation_errors():
        """Get validation errors."""
        is_valid, errors = Config.is_valid()
        return errors


if __name__ == "__main__":
    is_valid, errors = Config.is_valid()

    if is_valid:
        print("✓ Configuration is valid")
        print(f"Bot Token: {Config.BOT_TOKEN[:10]}...")
        print(f"Chat ID: {Config.CHAT_ID}")
        print(f"Images Path: {Config.IMAGES_PATH}")
        print(f"Send Interval: {Config.SEND_INTERVAL} hours")
        print(f"Schedule: {Config.START_HOUR}:00 - {Config.END_HOUR}:00")
    else:
        print("✗ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
