"""
Job processor: handles download, send, cleanup workflow.
Pyrogram version - supports up to 2GB uploads!
"""
import asyncio
from pathlib import Path
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError

from core.queue_manager import DownloadJob
from core.downloader import downloader
from utils.cleanup import delete_file
from utils.logger import logger


class JobProcessor:
    """
    Processes download jobs: download -> send -> cleanup.
    Uses Pyrogram for 2GB upload support!
    """
    
    def __init__(self, app: Client):
        self.app = app
        self.status_messages: dict[int, Message] = {}
    
    async def process(self, job: DownloadJob) -> None:
        """
        Process a single download job.
        
        Args:
            job: DownloadJob to process
        """
        file_path: Path | None = None
        
        try:
            # Update status: getting info
            await self._update_status(job, "🔍 Getting video info...")
            
            # Get video info first
            info = await downloader.get_info(job.url)
            
            if not info.is_available:
                await self._send_error(job, f"❌ {info.error_message}")
                return
            
            # Check duration (skip very long videos - 2 hours max now)
            if info.duration > 7200:
                await self._send_error(job, "❌ Video too long (max 2 hours)")
                return
            
            # Update status: downloading
            duration_str = self._format_duration(info.duration)
            await self._update_status(
                job, 
                f"⬇️ Downloading: {info.title[:50]}...\n"
                f"⏱ Duration: {duration_str}\n"
                f"🎬 Quality: up to 1080p"
            )
            
            # Download video
            result = await downloader.download(job.url, str(job.user_id))
            
            if not result.success:
                await self._send_error(job, f"❌ {result.error_message}")
                return
            
            file_path = result.file_path
            file_size_mb = result.file_size / (1024 * 1024)
            
            # Update status: uploading
            await self._update_status(
                job, 
                f"📤 Uploading ({file_size_mb:.1f}MB)...\n"
                f"_This may take a while for large files_"
            )
            
            # Send video with progress
            await self._send_video(job, result)
            
            # Delete status message
            await self._delete_status(job)
            
            logger.info(
                f"Job complete: user={job.user_id}, "
                f"title={result.title[:30]}, "
                f"size={result.file_size // (1024*1024)}MB"
            )
            
        except FloodWait as e:
            logger.warning(f"FloodWait: sleeping for {e.value} seconds")
            await asyncio.sleep(e.value)
            await self._send_error(job, "⚠️ Rate limited. Please try again in a minute.")
            
        except RPCError as e:
            logger.error(f"Telegram RPC error: {e}")
            await self._send_error(job, "❌ Telegram error. Please try again.")
            
        except Exception as e:
            logger.error(f"Processor error: {e}")
            await self._send_error(job, "❌ Something went wrong. Please try again.")
            
        finally:
            # Always cleanup
            if file_path and file_path.exists():
                delete_file(file_path)
    
    async def _update_status(self, job: DownloadJob, text: str) -> None:
        """Update or send status message."""
        try:
            if job.user_id in self.status_messages:
                msg = self.status_messages[job.user_id]
                await msg.edit_text(text)
            else:
                msg = await self.app.send_message(
                    chat_id=job.chat_id,
                    text=text,
                    reply_to_message_id=job.message_id
                )
                self.status_messages[job.user_id] = msg
        except Exception as e:
            logger.warning(f"Failed to update status: {e}")
    
    async def _delete_status(self, job: DownloadJob) -> None:
        """Delete status message."""
        try:
            if job.user_id in self.status_messages:
                await self.status_messages[job.user_id].delete()
                del self.status_messages[job.user_id]
        except Exception:
            pass
    
    async def _send_error(self, job: DownloadJob, message: str) -> None:
        """Send error message to user."""
        try:
            if job.user_id in self.status_messages:
                await self.status_messages[job.user_id].edit_text(message)
                del self.status_messages[job.user_id]
            else:
                await self.app.send_message(
                    chat_id=job.chat_id,
                    text=message,
                    reply_to_message_id=job.message_id
                )
        except Exception as e:
            logger.error(f"Failed to send error: {e}")
    
    async def _send_video(self, job: DownloadJob, result) -> None:
        """Send video file to user with progress tracking."""
        if not result.file_path:
            return
        
        caption = f"📹 {result.title[:200]}"
        if result.duration:
            caption += f"\n⏱ {self._format_duration(result.duration)}"
        
        file_size_mb = result.file_size / (1024 * 1024)
        caption += f"\n📦 {file_size_mb:.1f}MB"
        
        # Progress callback
        last_percent = [0]
        
        async def progress(current, total):
            percent = int(current * 100 / total)
            if percent - last_percent[0] >= 10:  # Update every 10%
                last_percent[0] = percent
                try:
                    await self._update_status(
                        job, 
                        f"📤 Uploading... {percent}%\n"
                        f"({current // (1024*1024)}MB / {total // (1024*1024)}MB)"
                    )
                except Exception:
                    pass
        
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.app.send_video(
                    chat_id=job.chat_id,
                    video=str(result.file_path),
                    caption=caption,
                    reply_to_message_id=job.message_id,
                    supports_streaming=True,
                    progress=progress
                )
                return  # Success!
                
            except FloodWait as e:
                logger.warning(f"FloodWait during upload: {e.value}s")
                await asyncio.sleep(e.value)
                
            except Exception as e:
                logger.warning(f"Upload attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format duration in human readable format."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
