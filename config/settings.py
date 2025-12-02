"""
Configuration settings loaded from environment variables.
Pyrogram version - supports 2GB uploads!
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Telegram API credentials (required for Pyrogram)
API_ID = os.getenv("API_ID", "")
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Download settings
MAX_VIDEO_RESOLUTION = int(os.getenv("MAX_VIDEO_RESOLUTION", "1080"))  # Higher now!
DOWNLOAD_PATH = Path(os.getenv("DOWNLOAD_PATH", str(BASE_DIR / "downloads")))
CONCURRENT_DOWNLOADS = int(os.getenv("CONCURRENT_DOWNLOADS", "3"))
CLEANUP_AFTER_MINUTES = int(os.getenv("CLEANUP_AFTER_MINUTES", "30"))

# Rate limiting
MAX_DOWNLOADS_PER_USER = int(os.getenv("MAX_DOWNLOADS_PER_USER", "20"))
RATE_LIMIT_WINDOW_MINUTES = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "60"))

# Telegram file size limit - NOW 2GB with Pyrogram!
TELEGRAM_FILE_SIZE_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB

# Network settings
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "1800"))  # 30 minutes
DOWNLOAD_RETRIES = int(os.getenv("DOWNLOAD_RETRIES", "5"))

# Ensure paths exist
DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

# Logs path
LOGS_PATH = BASE_DIR / "logs"
LOGS_PATH.mkdir(parents=True, exist_ok=True)
