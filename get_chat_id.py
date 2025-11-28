#!/usr/bin/env python3
"""Helper script to get chat_id from Telegram."""

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("❌ BOT_TOKEN is not configured in .env file")
    print("\nTo get your BOT_TOKEN:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /start and follow the instructions")
    print("3. Create a new bot and copy the token")
    print("4. Add it to .env file: BOT_TOKEN=your_token_here")
    exit(1)

print("=" * 70)
print(" Get Telegram Chat ID")
print("=" * 70)
print()
print("Follow these steps to get your CHAT_ID:\n")

print("1. Open Telegram and start a conversation with your bot")
print("   (search for your bot by name and click 'Start')\n")

print("2. Send any message to the bot (e.g., '/start')\n")

print("3. Open this URL in your browser:")
print(f"   https://api.telegram.org/bot{BOT_TOKEN}/getUpdates\n")

print("4. Look for the response, it should contain something like:")
print("""
{
  "ok": true,
  "result": [
    {
      "update_id": 123456789,
      "message": {
        "message_id": 1,
        "date": 1234567890,
        "chat": {
          "id": 987654321,  <-- This is your CHAT_ID
          "first_name": "Your Name",
          "type": "private"
        },
        ...
      }
    }
  ]
}
""")

print("5. Copy the 'id' value from 'chat'")
print("   (in the example above, it would be: 987654321)\n")

print("6. Add it to .env file:")
print("   CHAT_ID=987654321\n")

print("7. Run the config check:")
print("   python check_config.py\n")

print("8. If everything is OK, run the bot:")
print("   python main.py\n")

print("=" * 70)
