"""
YouTube video downloader using yt-dlp.
Optimized for slow networks with retries and timeouts.
Supports up to 2GB files with Pyrogram!
"""
import asyncio
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import yt_dlp

from config.settings import (
    DOWNLOAD_PATH,
    MAX_VIDEO_RESOLUTION,
    DOWNLOAD_TIMEOUT,
    DOWNLOAD_RETRIES,
    TELEGRAM_FILE_SIZE_LIMIT
)
from utils.logger import logger


@dataclass
class VideoInfo:
    """Video metadata container."""
    id: str
    title: str
    duration: int  # seconds
    uploader: str
    thumbnail: Optional[str]
    url: str
    is_available: bool = True
    error_message: Optional[str] = None


@dataclass
class DownloadResult:
    """Download result container."""
    success: bool
    file_path: Optional[Path] = None
    file_size: int = 0
    title: str = ""
    duration: int = 0
    error_message: Optional[str] = None


class YouTubeDownloader:
    """
    YouTube downloader with yt-dlp.
    Handles slow networks, retries, and resolution limits.
    Now supports up to 2GB files with Pyrogram MTProto!
    """
    
    def __init__(
        self,
        download_path: Path = DOWNLOAD_PATH,
        max_resolution: int = MAX_VIDEO_RESOLUTION,
        timeout: int = DOWNLOAD_TIMEOUT,
        retries: int = DOWNLOAD_RETRIES
    ):
        self.download_path = download_path
        self.max_resolution = max_resolution
        self.timeout = timeout
        self.retries = retries
        
        # Ensure download directory exists
        self.download_path.mkdir(parents=True, exist_ok=True)
    
    def _get_ydl_opts(self, output_template: str) -> Dict[str, Any]:
        """
        Get yt-dlp options optimized for stability and quality.
        
        Now supports higher resolutions since Pyrogram allows 2GB uploads!
        
        Args:
            output_template: Output file path template
            
        Returns:
            yt-dlp options dict
        """
        return {
            # Output
            'outtmpl': output_template,
            # Format selection strategy (order matters):
            # 1. Try best quality mp4 up to max resolution
            # 2. Try combined streams for reliability  
            # 3. Separate streams with merge (higher quality)
            # 4. Fallback to whatever works
            'format': (
                f'bestvideo[height<={self.max_resolution}][ext=mp4]+bestaudio[ext=m4a]/'  # Best quality mp4
                f'bestvideo[height<={self.max_resolution}]+bestaudio/'  # Best quality any format
                f'best[height<={self.max_resolution}][ext=mp4][vcodec!=none][acodec!=none]/'  # Combined mp4
                f'best[height<={self.max_resolution}][vcodec!=none][acodec!=none]/'  # Any combined
                f'best[height<={self.max_resolution}]/best'  # Ultimate fallback
            ),
            'merge_output_format': 'mp4',
            
            # CRITICAL: Headers to avoid 403 Forbidden
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            },
            
            # Network - optimized for reliability
            'retries': 10,
            'fragment_retries': 10,
            'file_access_retries': 5,
            'extractor_retries': 5,
            'socket_timeout': 60,
            'http_chunk_size': 10485760,  # 10MB chunks
            
            # Throttling protection
            'sleep_interval': 0.5,
            'max_sleep_interval': 3,
            'sleep_interval_requests': 1,
            
            # Reliability
            'ignoreerrors': False,
            'no_warnings': False,
            'quiet': False,
            'no_color': True,
            'geo_bypass': True,
            
            # Connection settings
            'nocheckcertificate': True,
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'overwrites': True,
            
            # Force IPv4
            'source_address': '0.0.0.0',
            
            # Extract flat to avoid some API calls
            'extract_flat': False,
            
            # Postprocessing
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            
            # Metadata
            'writethumbnail': False,
            'writesubtitles': False,
        }
    
    async def get_info(self, url: str) -> VideoInfo:
        """
        Get video information without downloading.
        
        Args:
            url: YouTube URL
            
        Returns:
            VideoInfo object with metadata
        """
        opts = {
            'quiet': True,
            'no_warnings': True,
            'no_color': True,
            'socket_timeout': 15,
            'retries': 2,
        }
        
        def _extract():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        try:
            loop = asyncio.get_event_loop()
            info = await asyncio.wait_for(
                loop.run_in_executor(None, _extract),
                timeout=30
            )
            
            if not info:
                return VideoInfo(
                    id="", title="", duration=0, uploader="",
                    thumbnail=None, url=url, is_available=False,
                    error_message="Could not fetch video info"
                )
            
            return VideoInfo(
                id=info.get('id', ''),
                title=info.get('title', 'Unknown'),
                duration=info.get('duration', 0) or 0,
                uploader=info.get('uploader', 'Unknown'),
                thumbnail=info.get('thumbnail'),
                url=url,
                is_available=True
            )
            
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            if 'private' in error_msg:
                msg = "Video is private"
            elif 'unavailable' in error_msg:
                msg = "Video is unavailable"
            elif 'age' in error_msg:
                msg = "Video is age-restricted"
            elif 'copyright' in error_msg:
                msg = "Video blocked due to copyright"
            else:
                msg = "Video cannot be accessed"
            
            logger.error(f"Video info error: {e}")
            return VideoInfo(
                id="", title="", duration=0, uploader="",
                thumbnail=None, url=url, is_available=False,
                error_message=msg
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting video info: {url}")
            return VideoInfo(
                id="", title="", duration=0, uploader="",
                thumbnail=None, url=url, is_available=False,
                error_message="Request timed out"
            )
            
        except Exception as e:
            logger.error(f"Unexpected error getting info: {e}")
            return VideoInfo(
                id="", title="", duration=0, uploader="",
                thumbnail=None, url=url, is_available=False,
                error_message="Failed to get video info"
            )
    
    async def download(self, url: str, video_id: str) -> DownloadResult:
        """
        Download video from YouTube.
        
        Args:
            url: YouTube URL
            video_id: Video ID for filename
            
        Returns:
            DownloadResult with file path or error
        """
        # Generate unique filename
        output_template = str(self.download_path / f"{video_id}_%(id)s.%(ext)s")
        opts = self._get_ydl_opts(output_template)
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    # Get the actual output filename
                    filename = ydl.prepare_filename(info)
                    # Ensure mp4 extension
                    filename = Path(filename).with_suffix('.mp4')
                    return info, filename
                return None, None
        
        try:
            logger.info(f"Starting download: {url}")
            
            loop = asyncio.get_event_loop()
            info, filename = await asyncio.wait_for(
                loop.run_in_executor(None, _download),
                timeout=self.timeout
            )
            
            if not info or not filename:
                return DownloadResult(
                    success=False,
                    error_message="Download failed - no output"
                )
            
            file_path = Path(filename)
            
            # Check if file exists (yt-dlp might add different extension)
            if not file_path.exists():
                # Try to find the actual file
                pattern = f"{video_id}_*"
                matches = list(self.download_path.glob(pattern))
                if matches:
                    file_path = matches[0]
                else:
                    return DownloadResult(
                        success=False,
                        error_message="Downloaded file not found"
                    )
            
            file_size = file_path.stat().st_size
            
            # Check Telegram size limit
            if file_size > TELEGRAM_FILE_SIZE_LIMIT:
                # Delete oversized file
                file_path.unlink()
                return DownloadResult(
                    success=False,
                    error_message=f"Video too large ({file_size // (1024*1024)}MB). Telegram limit is 50MB."
                )
            
            logger.info(f"Download complete: {file_path.name} ({file_size // 1024}KB)")
            
            return DownloadResult(
                success=True,
                file_path=file_path,
                file_size=file_size,
                title=info.get('title', 'Video'),
                duration=info.get('duration', 0) or 0
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Download timeout after {self.timeout}s: {url}")
            return DownloadResult(
                success=False,
                error_message="Download timed out. Try a shorter video."
            )
            
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            logger.error(f"yt-dlp error: {e}")
            
            if 'ffmpeg' in error_msg:
                msg = "Server error: ffmpeg not available"
            elif 'private' in error_msg:
                msg = "Video is private"
            elif 'unavailable' in error_msg:
                msg = "Video is unavailable"
            else:
                msg = "Download failed. Try another video."
            
            return DownloadResult(success=False, error_message=msg)
            
        except Exception as e:
            logger.error(f"Unexpected download error: {e}")
            return DownloadResult(
                success=False,
                error_message="Download failed. Please try again."
            )


# Global downloader instance
downloader = YouTubeDownloader()
