"""
Telegram bot message handlers (Pyrogram version).
Detects YouTube URLs and enqueues downloads automatically.
"""
from pyrogram import Client, filters
from pyrogram.types import Message

from core.queue_manager import queue_manager, DownloadJob
from utils.validators import extract_urls_from_text, normalize_youtube_url
from utils.rate_limiter import rate_limiter
from utils.logger import logger


def register_handlers(app: Client) -> None:
    """Register all message handlers."""
    
    @app.on_message(filters.command("start") & filters.private)
    async def start_command(client: Client, message: Message):
        """Handle /start command."""
        user = message.from_user
        logger.info(f"Start command from user {user.id} ({user.username})")
        
        welcome_text = (
            f"👋 Hi {user.first_name}!\n\n"
            "I can download YouTube videos for you.\n\n"
            "Just send me any YouTube link and I'll download it!\n\n"
            "📝 **Supported:**\n"
            "• youtube.com/watch?v=...\n"
            "• youtu.be/...\n"
            "• YouTube Shorts\n\n"
            "⚡ **Max resolution:** 1080p\n"
            "📦 **Max file size:** 2GB (!)\n\n"
            "🚀 _Powered by Pyrogram_"
        )
        
        await message.reply_text(welcome_text)
    
    @app.on_message(filters.command("help") & filters.private)
    async def help_command(client: Client, message: Message):
        """Handle /help command."""
        help_text = (
            "📖 **How to use:**\n\n"
            "1. Copy a YouTube video link\n"
            "2. Send it to me\n"
            "3. Wait for the download\n"
            "4. Get your video!\n\n"
            "⚙️ **Limits:**\n"
            "• Max 20 downloads per hour\n"
            "• Max resolution: 1080p\n"
            "• Max file size: 2GB\n\n"
            "❓ Having issues? Try a different video or wait a bit."
        )
        
        await message.reply_text(help_text)
    
    @app.on_message(filters.text & filters.private)
    async def handle_message(client: Client, message: Message):
        """Handle incoming messages, detect YouTube URLs."""
        if not message.text:
            return
        
        # Skip commands
        if message.text.startswith("/"):
            return
        
        user = message.from_user
        text = message.text
        
        # Extract YouTube URLs from message
        urls = extract_urls_from_text(text)
        
        if not urls:
            # No YouTube URLs found, ignore silently
            return
        
        logger.info(f"URLs detected from user {user.id}: {urls}")
        
        # Check rate limit
        if not rate_limiter.is_allowed(user.id):
            reset_time = rate_limiter.get_reset_time(user.id)
            minutes = reset_time // 60
            await message.reply_text(
                f"⏳ Too many requests. Please wait {minutes} minutes."
            )
            return
        
        # Process first URL only (to avoid spam)
        url = urls[0]
        normalized_url = normalize_youtube_url(url)
        
        if not normalized_url:
            await message.reply_text("❌ Invalid YouTube URL")
            return
        
        # Record request for rate limiting
        rate_limiter.record_request(user.id)
        
        # Create download job
        job = DownloadJob(
            user_id=user.id,
            chat_id=message.chat.id,
            message_id=message.id,
            url=normalized_url
        )
        
        # Add to queue
        position = await queue_manager.add_job(job)
        
        # Notify user
        if position > 1:
            await message.reply_text(
                f"⏳ Added to queue (position {position}). Please wait..."
            )
        else:
            await message.reply_text("⏳ Processing your video...")
        
        remaining = rate_limiter.get_remaining(user.id)
        logger.info(f"Job queued: user={user.id}, remaining={remaining}")
