import asyncio
import logging
import time
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, LOG_LEVEL
from handlers import router

start_time = time.time()

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    port = int(os.getenv('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

# Start health server in a thread
threading.Thread(target=run_health_server, daemon=True).start()

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO))

async def main():
    """
    Main entry point for the bot.
    """
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Update bot description
    await bot.set_my_description(
        "A Telegram bot for downloading videos and images from URLs. "
        "Supports platforms like YouTube, TikTok, Instagram, Facebook, and more. "
        "Send URLs to download media easily!\n\nCreated by GhostScript."
    )
    await bot.set_my_short_description("Download videos and images from URLs. Created by GhostScript.")

    # Include handlers
    dp.include_router(router)
    
    # Start polling
    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())