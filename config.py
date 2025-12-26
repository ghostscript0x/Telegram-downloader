import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Please set the BOT_TOKEN environment variable with your Telegram bot token.")

# Temporary directory for downloads
TEMP_DIR = tempfile.gettempdir()

# Maximum file size for Telegram (50MB for non-premium users, but bots can send larger; adjust as needed)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Rate limiting: max downloads per user per minute
RATE_LIMIT = 5  # downloads per minute

# Logging
LOG_LEVEL = 'INFO'