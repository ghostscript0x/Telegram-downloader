import asyncio
import time
import os
from aiogram import Router, types, F
from aiogram.filters import Command
from downloader import downloader, extract_video_info, download_image, get_image_info
from utils import is_valid_url, is_image_url, cleanup_file
from config import RATE_LIMIT

router = Router()

# Rate limiting: user_id -> list of timestamps
user_rates = {}

# Active downloads: user_id -> {'url': str, 'task': Task}
active_downloads = {}

# User history: user_id -> list of {'url': str, 'type': str, 'timestamp': float}
user_history = {}

def check_rate_limit(user_id: int) -> bool:
    """
    Check if user is within rate limit.
    """
    now = time.time()
    if user_id not in user_rates:
        user_rates[user_id] = []
    
    # Remove timestamps older than 1 minute
    user_rates[user_id] = [t for t in user_rates[user_id] if now - t < 60]
    
    if len(user_rates[user_id]) >= RATE_LIMIT:
        return False
    
    user_rates[user_id].append(now)
    return True


def make_progress_cb(message: types.Message, loop, throttle: float = 1.5):
    """
    Return a progress callback that accepts a dict or string and edits `message` with
    an inline progress bar. Edits are throttled to `throttle` seconds.
    """
    last = {'time': 0.0, 'percent': -1.0}

    async def _edit(text: str):
        try:
            await message.edit_text(text)
        except Exception:
            pass

    def cb(data):
        now = time.time()
        # Backwards compatibility: allow string messages
        if isinstance(data, str):
            text = data
            percent = None
        else:
            status = data.get('status')
            if status == 'downloading':
                percent = float(data.get('percent') or 0.0)
                p = max(0.0, min(100.0, percent))
                bar_len = 25
                filled = int((p / 100.0) * bar_len)
                bar = '▰' * filled + '▱' * (bar_len - filled)
                speed = data.get('speed', 'N/A')
                eta = data.get('eta', 'N/A')
                text = f"📥 Downloading: [{bar}] {p:5.1f}% | ⚡ Speed: {speed} | ⏱️ ETA: {eta}"
            elif status == 'finished':
                percent = 100.0
                text = "✅ Download finished, processing..."
            elif status == 'info':
                percent = None
                text = f"ℹ️ {data.get('message', '')}"
            else:
                percent = None
                text = f"🔄 {str(data)}"

        # Throttle edits: if within throttle window and percent change < 1%, skip
        if now - last['time'] < throttle:
            try:
                if percent is None:
                    return
                if abs(percent - last['percent']) < 1.0:
                    return
            except Exception:
                return

        last['time'] = now
        if percent is not None:
            last['percent'] = percent

        asyncio.run_coroutine_threadsafe(_edit(text), loop)

    return cb

@router.message(Command("start"))
async def start_command(message: types.Message):
    """
    Handle /start command.
    """
    await message.reply(
        "Welcome to the Downloader Bot!\n\n"
        "Send me a URL for videos (YouTube, TikTok, Facebook, etc.) or images, "
        "and I'll download it for you.\n\n"
        "For videos, choose your preferred quality when prompted.\n\n"
        "Commands: /history (view downloads), /health (bot status).\n\n"
        "Created by GhostScript."
    )

@router.message(Command("history"))
async def history_command(message: types.Message):
    """
    Handle /history command.
    """
    user_id = message.from_user.id
    if user_id not in user_history or not user_history[user_id]:
        await message.reply("No download history.")
        return
    
    text = "Your recent downloads (last 5):\n"
    buttons = []
    recent = user_history[user_id][-5:]
    for i, item in enumerate(recent):
        ago = time.time() - item['timestamp']
        ago_str = f"{int(ago // 60)}m ago" if ago < 3600 else f"{int(ago // 3600)}h ago"
        text += f"{i+1}. {item['type'].capitalize()}: {item['url'][:50]}... ({ago_str})\n"
        buttons.append(types.InlineKeyboardButton(text=f"Re-download {i+1}", callback_data=f"redownload_{i}"))
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.reply(text, reply_markup=keyboard)

@router.message(Command("health"))
async def health_command(message: types.Message):
    """
    Handle /health command to check bot status.
    """
    from main import start_time
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    uptime = f"{hours}h {minutes}m"
    await message.reply(f"✅ Bot is healthy!\n⏱️ Uptime: {uptime}\n🔧 Active downloads: {len(active_downloads)}")

async def process_single_url(message: types.Message, url: str):
    """
    Process a single URL for download.
    """
    user_id = message.from_user.id
    
    if user_id in active_downloads:
        await message.reply("You already have a download in progress. Please wait for it to complete.")
        return
    
    # Check if it's an image URL
    if is_image_url(url):
        # Get image info
        info = await asyncio.get_event_loop().run_in_executor(None, get_image_info, url)
        info_text = "Image info:\n"
        if info.get('content_type'):
            info_text += f"Type: {info['content_type']}\n"
        if info.get('size'):
            size_mb = info['size'] / (1024 * 1024)
            info_text += f"Size: {size_mb:.2f} MB"
        await message.reply(info_text)
        
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="Cancel", callback_data="cancel")]])
        status_msg = await message.reply("Downloading image...", reply_markup=cancel_keyboard)
        filepath = None
        try:
            loop = asyncio.get_running_loop()
            task = loop.run_in_executor(None, download_image, url)
            active_downloads[user_id] = {'url': url, 'task': task}
            filepath = await task
            await message.bot.send_photo(message.chat.id, types.FSInputFile(filepath))
            await status_msg.edit_text("Image downloaded!")
        except asyncio.CancelledError:
            await status_msg.edit_text("Download cancelled.")
        except ValueError as e:
            await status_msg.edit_text(f"Error: {str(e)}")
        except Exception as e:
            await status_msg.edit_text("An unexpected error occurred.")
        finally:
            if user_id in active_downloads:
                del active_downloads[user_id]
            if filepath:
                cleanup_file(filepath)
        return
    
    if 'pinterest' in url.lower():
        # Auto download with best quality for Pinterest
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="Cancel", callback_data="cancel")]])
        status_msg = await message.reply("Downloading from Pinterest...", reply_markup=cancel_keyboard)
        filepath = None
        try:
            loop = asyncio.get_running_loop()
            progress_callback = make_progress_cb(status_msg, loop)
            task = asyncio.create_task(downloader.download_video(url, 'video', 'best', progress_callback))
            active_downloads[user_id] = {'url': url, 'task': task}
            filepath, info = await task
            title = info.get('title', 'Pinterest video')
            await message.bot.send_video(message.chat.id, types.FSInputFile(filepath), caption=title)
            await status_msg.edit_text("Download complete!")
            # Add to history
            if user_id not in user_history:
                user_history[user_id] = []
            user_history[user_id].append({
                'url': url,
                'type': 'video',
                'timestamp': time.time()
            })
            user_history[user_id] = user_history[user_id][-10:]
        except asyncio.CancelledError:
            await status_msg.edit_text("Download cancelled.")
        except ValueError as e:
            await status_msg.edit_text(f"Error: {str(e)}")
        except Exception as e:
            await status_msg.edit_text("An unexpected error occurred.")
        finally:
            if user_id in active_downloads:
                del active_downloads[user_id]
            if filepath:
                cleanup_file(filepath)
        return
    
    # Analyze video formats
    status_msg = await message.reply("Analyzing available formats...")
    
    try:
        info = await asyncio.get_event_loop().run_in_executor(None, extract_video_info, url)

        # Show video info
        title = info.get('title', 'Unknown')
        duration = info.get('duration')
        if duration:
            dur_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
        else:
            dur_str = 'Unknown'
        formats = info.get('formats', [])
        has_video = any(fmt.get('vcodec') != 'none' for fmt in formats)
        has_audio = any(fmt.get('acodec') != 'none' for fmt in formats)
        info_text = f"Video info:\nTitle: {title}\nDuration: {dur_str}\nHas video: {has_video}, Has audio: {has_audio}"
        await status_msg.edit_text(info_text)

        # Wait a bit or proceed
        await asyncio.sleep(2)  # Give user time to see info

        # Check for available video and audio (already have has_video, has_audio)

        buttons = []
        if has_video:
            buttons.append(types.InlineKeyboardButton(text="Video", callback_data="video_best"))
        if has_audio:
            buttons.append(types.InlineKeyboardButton(text="Audio (MP3)", callback_data="audio_mp3"))

        if not buttons:
            await status_msg.edit_text("No downloadable formats found for this video.")
            return

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
        await status_msg.edit_text("Choose type:", reply_markup=keyboard)

        # Store URL for later use
        active_downloads[user_id] = {'url': url, 'task': None}
        
    except Exception as e:
        await status_msg.edit_text(f"Error analyzing video: {str(e)}")

@router.message(F.text)
async def handle_url(message: types.Message):
    """
    Handle incoming URLs. Supports single or multiple URLs.
    """
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Split by newlines or spaces
    potential_urls = text.replace('\n', ' ').split()
    urls = [u for u in potential_urls if is_valid_url(u)]
    
    if not urls:
        await message.reply("Please send valid URLs.")
        return
    
    # Limit to 5 URLs per message
    urls = urls[:5]
    
    for url in urls:
        if not check_rate_limit(user_id):
            await message.reply(f"Rate limit exceeded for {url}. You can send up to {RATE_LIMIT} URLs per minute.")
            continue
        await process_single_url(message, url)
    
    # Check if it's an image URL
    if is_image_url(url):
        # Get image info
        info = await asyncio.get_event_loop().run_in_executor(None, get_image_info, url)
        info_text = "Image info:\n"
        if info.get('content_type'):
            info_text += f"Type: {info['content_type']}\n"
        if info.get('size'):
            size_mb = info['size'] / (1024 * 1024)
            info_text += f"Size: {size_mb:.2f} MB"
        await message.reply(info_text)
        
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="Cancel", callback_data="cancel")]])
        status_msg = await message.reply("Downloading image...", reply_markup=cancel_keyboard)
        filepath = None
        try:
            loop = asyncio.get_running_loop()
            task = loop.run_in_executor(None, download_image, url)
            active_downloads[user_id] = {'url': url, 'task': task}
            filepath = await task
            await message.bot.send_photo(message.chat.id, types.FSInputFile(filepath))
            await status_msg.edit_text("Image downloaded!")
        except asyncio.CancelledError:
            await status_msg.edit_text("Download cancelled.")
        except ValueError as e:
            await status_msg.edit_text(f"Error: {str(e)}")
        except Exception as e:
            await status_msg.edit_text("An unexpected error occurred.")
        finally:
            if user_id in active_downloads:
                del active_downloads[user_id]
            if filepath:
                cleanup_file(filepath)
        return
    
    if 'pinterest' in url.lower():
        # Auto download with best quality for Pinterest
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="Cancel", callback_data="cancel")]])
        status_msg = await message.reply("Downloading from Pinterest...", reply_markup=cancel_keyboard)
        filepath = None
        try:
            loop = asyncio.get_running_loop()
            progress_callback = make_progress_cb(status_msg, loop)
            task = asyncio.create_task(downloader.download_video(url, 'video', 'best', progress_callback))
            active_downloads[user_id] = {'url': url, 'task': task}
            filepath, info = await task
            title = info.get('title', 'Pinterest video')
            await message.bot.send_video(message.chat.id, types.FSInputFile(filepath), caption=title)
            await status_msg.edit_text("Download complete!")
        except ValueError as e:
            await status_msg.edit_text(f"Error: {str(e)}")
        except Exception as e:
            await status_msg.edit_text("An unexpected error occurred.")
        finally:
            if user_id in active_downloads:
                del active_downloads[user_id]
            if filepath:
                cleanup_file(filepath)
    else:
        # Analyze video formats
        status_msg = await message.reply("Analyzing available formats...")
        
        try:
            info = await asyncio.get_event_loop().run_in_executor(None, extract_video_info, url)

            # Show video info
            title = info.get('title', 'Unknown')
            duration = info.get('duration')
            if duration:
                dur_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
            else:
                dur_str = 'Unknown'
            formats = info.get('formats', [])
            has_video = any(fmt.get('vcodec') != 'none' for fmt in formats)
            has_audio = any(fmt.get('acodec') != 'none' for fmt in formats)
            info_text = f"Video info:\nTitle: {title}\nDuration: {dur_str}\nHas video: {has_video}, Has audio: {has_audio}"
            await status_msg.edit_text(info_text)

            # Wait a bit or proceed
            await asyncio.sleep(2)  # Give user time to see info

            # Check for available video and audio (already have has_video, has_audio)

            buttons = []
            if has_video:
                buttons.append(types.InlineKeyboardButton(text="Video", callback_data="video_best"))
            if has_audio:
                buttons.append(types.InlineKeyboardButton(text="Audio (MP3)", callback_data="audio_mp3"))

            if not buttons:
                await status_msg.edit_text("No downloadable formats found for this video.")
                return

            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
            await status_msg.edit_text("Choose type:", reply_markup=keyboard)

            # Store URL for later use
            active_downloads[user_id] = {'url': url, 'task': None}
            
        except Exception as e:
            await status_msg.edit_text(f"Error analyzing video: {str(e)}")

@router.callback_query(F.data.in_(["video_best", "audio_mp3"]))
async def handle_type_selection(callback: types.CallbackQuery):
    """
    Handle type selection callbacks.
    """
    user_id = callback.from_user.id

    if user_id not in active_downloads:
        await callback.answer("No active download found.")
        return

    data = callback.data
    if data == "video_best":
        format_type = "video"
        quality = "best"
    elif data == "audio_mp3":
        format_type = "audio"
        quality = "mp3"
    else:
        await callback.answer("Invalid selection.")
        return
    
    url = active_downloads[user_id]['url']
    
    await callback.answer()
    
    # Send new message for progress with cancel button
    cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="Cancel", callback_data="cancel")]])
    status_msg = await callback.message.reply("Downloading... This may take a few minutes.", reply_markup=cancel_keyboard)
    
    filepath = None
    try:
        # Set up progress callback (throttled + inline bar)
        loop = asyncio.get_running_loop()
        progress_callback = make_progress_cb(status_msg, loop)

        # Start download task
        task = asyncio.create_task(downloader.download_video(url, format_type, quality, progress_callback))
        active_downloads[user_id]['task'] = task

        filepath, info = await task
        
        # Prepare caption
        title = info.get('title', 'Downloaded video')
        duration = info.get('duration')
        if duration:
            dur = int(duration)
            minutes = dur // 60
            seconds = dur % 60
            title += f" ({minutes}:{seconds:02d})"
        
        # Send the file
        if format_type == 'audio':
            await callback.bot.send_audio(
                callback.message.chat.id,
                types.FSInputFile(filepath),
                caption=title
            )
        else:
            await callback.bot.send_video(
                callback.message.chat.id,
                types.FSInputFile(filepath),
                caption=title
            )
        
        await callback.message.edit_text("Download complete! File sent above.")
        
        # Add to history
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append({
            'url': url,
            'type': format_type,
            'timestamp': time.time()
        })
        user_history[user_id] = user_history[user_id][-10:]
        
    except asyncio.CancelledError:
        await callback.message.edit_text("Download cancelled.")
    except ValueError as e:
        await callback.message.edit_text(f"Error: {str(e)}")
    except Exception as e:
        await callback.message.edit_text(f"An unexpected error occurred: {str(e)}")
    finally:
        # Cleanup
        if user_id in active_downloads:
            task = active_downloads[user_id].get('task')
            if task and not task.done():
                task.cancel()
            del active_downloads[user_id]
        if filepath:
            cleanup_file(filepath)

@router.callback_query(F.data == "cancel")
async def handle_cancel(callback: types.CallbackQuery):
    """
    Handle cancel button.
    """
    user_id = callback.from_user.id
    if user_id in active_downloads:
        task = active_downloads[user_id].get('task')
        if task and not task.done():
            task.cancel()
        del active_downloads[user_id]
        await callback.message.edit_text("Download cancelled.")
    await callback.answer()

@router.callback_query(F.data.startswith("redownload_"))
async def handle_redownload(callback: types.CallbackQuery):
    """
    Handle re-download from history.
    """
    user_id = callback.from_user.id
    try:
        idx = int(callback.data.split('_')[1])
        if user_id in user_history and idx < len(user_history[user_id][-5:]):
            url = user_history[user_id][-5:][idx]['url']
            await process_single_url(callback.message, url)
            await callback.answer("Re-downloading...")
        else:
            await callback.answer("Invalid selection.")
    except Exception:
        await callback.answer("Error.")

