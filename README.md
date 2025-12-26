# Telegram Media Downloader Bot

A high-performance Telegram bot for downloading videos and images from online platforms using yt-dlp and Aiogram. Supports batch downloads, history, and cancellation.

## Features

- **Multi-platform support**: YouTube, TikTok, Facebook, Instagram, Twitter (X), Pinterest, and all yt-dlp supported platforms
- **Media types**: Videos (with quality selection: 360p, 720p, 1080p, best) and images (direct download)
- **Asynchronous architecture**: Non-blocking downloads for maximum performance
- **Batch downloads**: Send multiple URLs at once (up to 5 per message)
- **Download management**: Cancel active downloads, view progress with bars
- **User history**: Re-download recent files via /history command
- **Smart file handling**: Automatic size checking against Telegram limits, fallback options
- **Security & Abuse Prevention**:
  - Rate limiting (5 downloads per minute per user)
  - One active download per user
  - Immediate file cleanup after sending
- **User-friendly**: File info previews, progress indicators, error messages, and usage instructions

## Project Structure

```
telegram-downloader/
├── main.py              # Bot entry point
├── handlers.py          # Message and callback handlers
├── downloader.py        # yt-dlp integration
├── utils.py             # Helper functions
├── config.py            # Configuration and constants
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- A Telegram bot token from [@BotFather](https://t.me/botfather)

### Installation

1. **Clone or download the project files** to your local machine.

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variable**:
   - On Windows: `set BOT_TOKEN=your_bot_token_here`
   - On Linux/Mac: `export BOT_TOKEN=your_bot_token_here`

   Replace `your_bot_token_here` with the token you received from BotFather.

4. **Run the bot**:
   ```bash
   python main.py
   ```

The bot will start polling for messages and is ready to use.

## Usage

1. **Start the bot**: Send `/start` to receive usage instructions.
2. **Send URLs**: Paste one or more URLs (videos or images) from supported platforms. Separate multiple URLs with spaces or newlines.
3. **For videos**: Choose quality via inline buttons (360p, 720p, 1080p, best video, or MP3 audio).
4. **For images**: Download starts automatically after info preview.
5. **Manage downloads**: Use the Cancel button during download, or /history to re-download past files.
6. **Receive files**: The bot downloads and sends the media.

## Supported Platforms

All platforms supported by yt-dlp for videos, including:
- YouTube
- TikTok
- Facebook
- Instagram
- Twitter (X)
- Pinterest
- Vimeo
- And many more...

Direct image downloads from any URL with common extensions (.jpg, .png, .gif, etc.).

## Configuration

Edit `config.py` to customize:
- `MAX_FILE_SIZE`: Maximum file size (default: 2GB)
- `RATE_LIMIT`: Downloads per minute per user (default: 5)
- `LOG_LEVEL`: Logging verbosity (default: INFO)

## Performance Notes

- Downloads are handled asynchronously to prevent blocking
- Temporary files are stored in the system temp directory and cleaned up immediately
- No video re-encoding for speed
- SSD-optimized temporary storage

## Security

- No permanent file storage
- Rate limiting prevents abuse
- Downloads are isolated per user
- Sensitive data (bot token) via environment variables

## Troubleshooting

- **Bot not responding**: Check if BOT_TOKEN is set correctly
- **Download fails**: Ensure the URL is valid and the video is publicly accessible
- **File too large**: The bot will automatically attempt lower quality or notify you
- **Rate limit**: Wait a minute before sending another URL

## Creator

Created by GhostScript  
GitHub: [ghostscript0x](https://github.com/ghostscript0x)

## License

This project is for personal use. Follow Telegram's Terms of Service and respect platform policies.