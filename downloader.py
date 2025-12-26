import asyncio
import os
import shutil
import yt_dlp
import requests
from config import TEMP_DIR, MAX_FILE_SIZE
from utils import get_file_size, cleanup_file

def extract_video_info(url: str) -> dict:
    """
    Extract video information without downloading.
    """
    with yt_dlp.YoutubeDL({
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extract_flat': False
    }) as ydl:
        return ydl.extract_info(url, download=False)

class VideoDownloader:
    def __init__(self):
        self.temp_dir = TEMP_DIR

    async def download_video(self, url: str, format_type: str = 'video', quality: str = '720p', progress_callback=None) -> tuple[str, dict]:
        """
        Download video from URL asynchronously.
        Returns (filepath, info_dict) or raises exception.
        progress_callback: function to call with progress message
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_sync, url, format_type, quality, progress_callback)

    def _download_sync(self, url: str, format_type: str, quality: str, progress_callback=None) -> tuple[str, dict]:
        """
        Synchronous download function.
        """
        # Determine format and postprocessing based on type
        if format_type == 'audio':
            format_str = 'bestaudio/best'
        else:
            # Use best format which includes both video and audio
            format_str = 'best'

        # If ffmpeg is not available, fallback to a single-file download to avoid merge errors
        has_ffmpeg = shutil.which('ffmpeg') is not None
        if format_type != 'audio' and not has_ffmpeg:
            # Notify via progress callback if provided (structured message)
            if progress_callback:
                try:
                    progress_callback({
                        'status': 'info',
                        'message': 'ffmpeg not found — falling back to single-file download. Install ffmpeg to enable merged best video+audio.'
                    })
                except Exception:
                    pass
            format_str = 'best'

        os.makedirs(self.temp_dir, exist_ok=True)
        output_template = os.path.join(self.temp_dir, '%(title)s.%(ext)s')

        def progress_hook(d):
            try:
                status = d.get('status')
                if status == 'downloading' and progress_callback:
                    percent_str = d.get('_percent_str') or d.get('percent') or '0%'
                    # normalize percent to float
                    try:
                        percent_val = float(str(percent_str).strip().replace('%', ''))
                    except Exception:
                        percent_val = 0.0

                    speed = d.get('_speed_str', d.get('speed')) or 'N/A'
                    eta = d.get('_eta_str', d.get('eta')) or 'N/A'

                    progress_callback({
                        'status': 'downloading',
                        'percent': percent_val,
                        'percent_str': f"{percent_val:.1f}%",
                        'speed': speed,
                        'eta': eta,
                    })
                elif status == 'finished' and progress_callback:
                    # finished downloading a part (video/audio), merging/postprocessing may follow
                    progress_callback({'status': 'finished'})
            except Exception:
                pass

        ydl_opts = {
            'format': format_str,
            'outtmpl': output_template,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'progress_hooks': [progress_hook] if progress_callback else [],
            'prefer_ffmpeg': True,
        }

        # Add merge output format for video to ensure final file is playable (mp4)
        if format_type == 'video' and has_ffmpeg:
            ydl_opts['merge_output_format'] = 'mp4'

        # Add postprocessor to convert audio to mp3 when requested
        if format_type == 'audio' and quality == 'mp3':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        try:
            # Snapshot files present before download so we can identify newly created files
            try:
                before_files = set(os.listdir(self.temp_dir))
            except Exception:
                before_files = set()

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # Determine the produced file by looking for new files in temp_dir
                filepath = None
                try:
                    after_files = set(os.listdir(self.temp_dir))
                    new_files = [f for f in after_files - before_files if not f.endswith('.part')]
                    new_paths = [os.path.join(self.temp_dir, f) for f in new_files]
                    # If multiple new files (video+audio parts), pick the largest one
                    if new_paths:
                        filepath = max(new_paths, key=os.path.getsize)
                except Exception:
                    filepath = None

                # Fallback: try yt-dlp's prepare_filename and previous matching logic
                if not filepath:
                    try:
                        filename = ydl.prepare_filename(info)
                        base = os.path.splitext(filename)[0]
                        candidates = [os.path.join(self.temp_dir, f) for f in os.listdir(self.temp_dir) if f.startswith(os.path.basename(base))]
                        candidates = [c for c in candidates if not c.endswith('.part')]
                        if candidates:
                            filepath = max(candidates, key=os.path.getsize)
                    except Exception:
                        filepath = None

                if not filepath:
                    raise ValueError('Could not determine downloaded file path')

                # Check file size
                size = get_file_size(filepath)
                if size > MAX_FILE_SIZE:
                    cleanup_file(filepath)
                    raise ValueError(f"File size ({size} bytes) exceeds limit ({MAX_FILE_SIZE // (1024*1024*1024)}GB)")

                return filepath, info
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "Sign in to confirm" in error_msg or "cookies" in error_msg.lower():
                raise ValueError("This video requires authentication (age-restricted or bot-protected). Unable to download.")
            elif "Requested format is not available" in error_msg or "Unknown format code" in error_msg:
                # Retry with best available format
                ydl_opts['format'] = 'best' if format_type == 'video' else 'bestaudio'
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                             info = ydl.extract_info(url, download=True)
                             filename = ydl.prepare_filename(info)
                             base = os.path.splitext(filename)[0]
                             filepath = filename
                             try:
                                 candidates = [os.path.join(self.temp_dir, f) for f in os.listdir(self.temp_dir) if f.startswith(os.path.basename(base))]
                                 candidates = [c for c in candidates if not c.endswith('.part')]
                                 if candidates:
                                     filepath = max(candidates, key=os.path.getsize)
                             except Exception:
                                 pass

                             size = get_file_size(filepath)
                             if size > MAX_FILE_SIZE:
                                 cleanup_file(filepath)
                                 raise ValueError(f"File size ({size} bytes) exceeds limit ({MAX_FILE_SIZE // (1024*1024*1024)}GB)")

                             return filepath, info
                except Exception as retry_e:
                    raise ValueError(f"Download failed even with fallback format: {str(retry_e)}")
            else:
                raise ValueError(f"Download failed: {error_msg}")
        except Exception as e:
            raise ValueError(f"Unexpected error: {str(e)}")

def get_image_info(url: str) -> dict:
    """
    Get basic info about an image URL.
    """
    try:
        response = requests.head(url, timeout=5)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        size = response.headers.get('content-length')
        if size:
            size = int(size)
        return {'content_type': content_type, 'size': size}
    except Exception:
        return {}

def download_image(url: str) -> str:
    """
    Download image from URL.
    Returns filepath or raises exception.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise ValueError("URL does not point to an image")
        
        # Get filename
        from urllib.parse import urlparse
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename or '.' not in filename:
            ext = content_type.split('/')[-1] if '/' in content_type else 'jpg'
            filename = f'image.{ext}'
        
        filepath = os.path.join(TEMP_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Check size
        size = get_file_size(filepath)
        if size > MAX_FILE_SIZE:
            cleanup_file(filepath)
            raise ValueError(f"Image size ({size} bytes) exceeds Telegram limit ({MAX_FILE_SIZE} bytes)")
        
        return filepath
    except requests.RequestException as e:
        raise ValueError(f"Failed to download image: {str(e)}")

# Global instance
downloader = VideoDownloader()