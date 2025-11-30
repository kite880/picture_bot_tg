import os
import logging
import random
from datetime import time
from pathlib import Path
from config import Config
from history import HistoryManager
from google_drive import GoogleDriveManager
from telegram import Bot, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = Bot(token=Config.BOT_TOKEN)

# Initialize history manager
history_manager = HistoryManager()

# Google Drive manager (if using Google Drive)
google_drive_manager = None

# Available images
available_images = []

# Current send interval in minutes (can be changed at runtime)
current_send_interval = 60  # Default 1 hour in minutes


def load_images():
    """Load all images from configured source."""
    global available_images, google_drive_manager

    if Config.IMAGE_SOURCE == "google_drive":
        return load_images_from_google_drive()
    else:
        return load_images_from_local()


def load_images_from_local():
    """Load images from local folder."""
    global available_images

    if not Config.IMAGES_PATH or not os.path.exists(Config.IMAGES_PATH):
        logger.error(f"Images path not found: {Config.IMAGES_PATH}")
        return False

    images_path = Path(Config.IMAGES_PATH)

    available_images = [
        str(f) for f in images_path.iterdir()
        if f.is_file() and f.suffix.lower() in Config.IMAGE_EXTENSIONS
    ]

    if not available_images:
        logger.error(f"No images found in {Config.IMAGES_PATH}")
        return False

    logger.info(f"Loaded {len(available_images)} images from {Config.IMAGES_PATH}")
    return True


def load_images_from_google_drive():
    """Load images from Google Drive."""
    global available_images, google_drive_manager

    try:
        google_drive_manager = GoogleDriveManager(
            Config.GOOGLE_DRIVE_CREDENTIALS,
            Config.GOOGLE_DRIVE_FOLDER_ID
        )

        if not google_drive_manager.load_images():
            logger.error("Failed to load images from Google Drive")
            return False

        available_images = google_drive_manager.get_image_list()
        logger.info(f"Loaded {len(available_images)} images from Google Drive")
        return True

    except Exception as e:
        logger.error(f"Error loading images from Google Drive: {e}")
        return False


def get_random_image():
    """Get a random image that hasn't been sent before."""
    # Filter out images that have been sent
    unsent_images = history_manager.get_unsent_images(available_images)

    if not unsent_images:
        # If all images have been sent
        logger.warning("All images have been sent! No more unsent images available.")
        stats = history_manager.get_stats()
        logger.warning(f"Total images sent so far: {stats['total_sent']}")
        return None

    selected_image = random.choice(unsent_images)
    return selected_image


async def send_image(chat_id):
    """Send a random image to the specified chat."""
    try:
        image_name = get_random_image()

        if not image_name:
            logger.error("No unsent images available")
            return False

        # For Google Drive, download the image first
        if Config.IMAGE_SOURCE == "google_drive":
            image_path = await download_image_from_google_drive(image_name)
            if not image_path:
                logger.error(f"Failed to download image: {image_name}")
                return False
        else:
            image_path = image_name

        with open(image_path, 'rb') as image_file:
            await bot.send_photo(chat_id=chat_id, photo=image_file)
            # Add to history after successful send
            history_manager.add_image(image_name)
            logger.info(f"Image sent: {image_name}")

            # Clean up cache for Google Drive images
            if Config.IMAGE_SOURCE == "google_drive":
                try:
                    os.remove(image_path)
                    logger.debug(f"Cache cleaned: {image_name}")
                except Exception as e:
                    logger.warning(f"Failed to clean cache: {e}")

            return True

    except TelegramError as e:
        logger.error(f"Telegram error: {e}")
        return False
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


async def download_image_from_google_drive(image_name: str) -> str:
    """Download image from Google Drive. Returns local path."""
    try:
        # Create cache directory if it doesn't exist
        cache_dir = Config.GOOGLE_DRIVE_CACHE_DIR
        os.makedirs(cache_dir, exist_ok=True)

        # Get image info from Google Drive manager
        image_info = google_drive_manager.get_image_by_name(image_name)
        if not image_info:
            logger.error(f"Image not found in Google Drive: {image_name}")
            return None

        # Download the image
        local_path = os.path.join(cache_dir, image_name)
        success = google_drive_manager.download_image(
            image_info['id'],
            image_name,
            cache_dir
        )

        if success:
            return local_path
        else:
            return None

    except Exception as e:
        logger.error(f"Error downloading image from Google Drive: {e}")
        return None


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with keyboard buttons."""
    keyboard = [
        [KeyboardButton("📊 Статистика"), KeyboardButton("🖼️ Отправить сейчас")],
        [KeyboardButton("⚙️ Интервал"), KeyboardButton("🔄 Сбросить историю")],
        [KeyboardButton("ℹ️ Справка")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Привет! Я бот для отправки картинок.\n\n"
        "Выбери действие из кнопок ниже:",
        reply_markup=reply_markup
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    stats = history_manager.get_stats()
    unsent = history_manager.get_unsent_images(available_images)

    message = (
        "📊 Статистика:\n\n"
        f"Всего картинок в папке: {len(available_images)}\n"
        f"Отправлено картинок: {stats['total_sent']}\n"
        f"Осталось неотправленных: {len(unsent)}\n"
    )

    if len(available_images) > 0:
        percentage = (stats['total_sent'] / len(available_images)) * 100
        message += f"Прогресс: {percentage:.1f}%"

    await update.message.reply_text(message)


async def cmd_reset_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset_history command."""
    cleared_count = history_manager.reset_history()
    await update.message.reply_text(
        f"🔄 История сброшена!\n"
        f"Удалено {cleared_count} записей о отправленных картинках.\n"
        f"Теперь все картинки считаются новыми."
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "ℹ️ Справка по командам:\n\n"
        "/start - главное меню\n"
        "/stats - показать статистику отправок\n"
        "/send_now - отправить одну картинку сейчас\n"
        "/reset_history - сбросить всю историю отправок\n"
        "/help - эта справка\n\n"
        "Бот автоматически отправляет картинки по расписанию.\n"
        "Картинки не повторяются, пока вы не сбросите историю."
    )
    await update.message.reply_text(help_text)


async def cmd_send_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /send_now command - send one image immediately."""
    # Get unsent images
    unsent = history_manager.get_unsent_images(available_images)

    if not unsent:
        await update.message.reply_text(
            "⚠️ Нет новых картинок для отправки!\n"
            "Все картинки уже были отправлены.\n\n"
            "Используйте /reset_history для сброса истории."
        )
        return

    # Send image to configured channel (not to personal chat)
    try:
        channel_id = int(Config.CHAT_ID)
    except ValueError:
        channel_id = Config.CHAT_ID

    success = await send_image(channel_id)

    if success:
        await update.message.reply_text("✅ Картинка отправлена в канал!")
    else:
        await update.message.reply_text("❌ Ошибка при отправке картинки")


async def cmd_set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set_interval command - show interval options."""
    keyboard = [
        [KeyboardButton("15 мин"), KeyboardButton("30 мин")],
        [KeyboardButton("45 мин"), KeyboardButton("1 час")],
        [KeyboardButton("Назад")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"⚙️ Текущий интервал: {current_send_interval} минут\n\n"
        "Выбери новый интервал для отправки картинок:",
        reply_markup=reply_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses and text messages."""
    global current_send_interval

    text = update.message.text

    # Handle stats button
    if text == "📊 Статистика":
        await cmd_stats(update, context)

    # Handle send now button
    elif text == "🖼️ Отправить сейчас":
        await cmd_send_now(update, context)

    # Handle reset history button
    elif text == "🔄 Сбросить историю":
        await cmd_reset_history(update, context)

    # Handle help button
    elif text == "ℹ️ Справка":
        await cmd_help(update, context)

    # Handle interval button
    elif text == "⚙️ Интервал":
        await cmd_set_interval(update, context)

    # Handle interval selection
    elif text in ["15 мин", "30 мин", "45 мин", "1 час"]:
        interval_map = {
            "15 мин": 15,
            "30 мин": 30,
            "45 мин": 45,
            "1 час": 60,
        }
        current_send_interval = interval_map[text]
        await update.message.reply_text(
            f"✅ Интервал изменён на {current_send_interval} минут!\n"
            f"Новое расписание будет использоваться со следующей отправки."
        )
        logger.info(f"Send interval changed to {current_send_interval} minutes")

    # Handle back button
    elif text == "Назад":
        await cmd_start(update, context)


async def scheduled_send(context: ContextTypes.DEFAULT_TYPE):
    """Callback for scheduled image sends."""
    try:
        from datetime import datetime

        # Check if current time is within working hours
        current_hour = datetime.now().hour
        if current_hour < Config.START_HOUR or current_hour >= Config.END_HOUR:
            logger.info(f"Outside working hours ({Config.START_HOUR}:00 - {Config.END_HOUR}:00), skipping send")
            return

        channel_id = context.job.data
        logger.info(f"Executing scheduled send to {channel_id}")
        await send_image(channel_id)
    except Exception as e:
        logger.error(f"Error in scheduled send: {e}")


def setup_command_handlers(app: Application):
    """Setup bot command handlers."""
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("send_now", cmd_send_now))
    app.add_handler(CommandHandler("reset_history", cmd_reset_history))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("set_interval", cmd_set_interval))

    # Handle button presses
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Command handlers registered")


async def setup_bot_commands(app: Application):
    """Register commands in Telegram."""
    from telegram import BotCommand

    commands = [
        BotCommand("start", "Главное меню"),
        BotCommand("stats", "Статистика отправок"),
        BotCommand("send_now", "Отправить одну картинку сейчас"),
        BotCommand("set_interval", "Изменить интервал отправок"),
        BotCommand("reset_history", "Сбросить историю отправок"),
        BotCommand("help", "Справка по командам"),
    ]

    try:
        await app.bot.set_my_commands(commands)
        logger.info("Bot commands registered in Telegram")
    except Exception as e:
        logger.error(f"Failed to register commands: {e}")


def setup_schedule(application: Application, chat_id):
    """Setup scheduled image sends using job_queue."""
    job_queue = application.job_queue

    # Convert interval from minutes to seconds
    interval_seconds = current_send_interval * 60

    # Schedule image sends during working hours using run_repeating
    # First send after 1 minute, then every interval_seconds
    job_queue.run_repeating(
        scheduled_send,
        interval=interval_seconds,
        first=60,  # First send after 60 seconds
        data=chat_id,
        name="repeating_image_send"
    )

    logger.info(f"Job queue configured: Send every {current_send_interval} minutes between {Config.START_HOUR}:00 and {Config.END_HOUR}:00")


def main():
    """Main function."""
    logger.info("Starting Picture Bot...")

    # Validate configuration
    is_valid, errors = Config.is_valid()
    if not is_valid:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return

    # Load images
    if not load_images():
        logger.error("Failed to load images")
        return

    # Parse chat_id (can be number or @channel_name)
    try:
        chat_id = int(Config.CHAT_ID)
    except ValueError:
        # It's a channel name like @drunklinked
        chat_id = Config.CHAT_ID

    # Initialize and setup Application
    application = Application.builder().token(Config.BOT_TOKEN).build()

    # Set post_init callback to register commands
    application.post_init = lambda app: setup_bot_commands(app)

    setup_command_handlers(application)

    # Setup job queue for scheduled sends
    setup_schedule(application, chat_id)

    logger.info("Bot connected successfully")
    logger.info("Bot is running... Press Ctrl+C to stop.")

    # Run the bot
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")


if __name__ == "__main__":
    main()
