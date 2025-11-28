#!/usr/bin/env python3
"""Script to check and validate configuration."""

import sys
from config import Config


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f" {text}")
    print(f"{'=' * 60}\n")


def check_config():
    """Check configuration and print results."""
    print_header("Picture Bot - Configuration Check")

    is_valid, errors = Config.is_valid()

    if is_valid:
        print("✓ Configuration is valid!\n")
        print("Current Configuration:")
        print(f"  Bot Token:    {Config.BOT_TOKEN[:20]}...")
        print(f"  Chat ID:      {Config.CHAT_ID}")
        print(f"  Images Path:  {Config.IMAGES_PATH}")
        print(f"  Send Interval: {Config.SEND_INTERVAL} hours")
        print(f"  Schedule:     {Config.START_HOUR}:00 - {Config.END_HOUR}:00")

        # Calculate number of sends per day
        sends_per_day = (Config.END_HOUR - Config.START_HOUR) // Config.SEND_INTERVAL
        print(f"\nSends per day: {sends_per_day}")

        print_header("Setup Complete!")
        print("You can now run: python main.py\n")
        return 0
    else:
        print("✗ Configuration has errors!\n")
        print("Issues found:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")

        print_header("Next Steps")
        print("""1. Open the .env file in your editor
2. Update the missing/invalid configuration values
3. Run this check again to verify

Configuration file: .env
Example values for .env:
  BOT_TOKEN=123456789:ABCDefGHIjklMNOpqrsTUVwxyz
  CHAT_ID=987654321
  IMAGES_PATH=/home/user/my_images
  SEND_INTERVAL=2
  START_HOUR=9
  END_HOUR=21
""")
        return 1


if __name__ == "__main__":
    sys.exit(check_config())
