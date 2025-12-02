"""
KeepItAllBot - YouTube Video Downloader Telegram Bot
Pyrogram version - supports up to 2GB uploads!

Entry point: initializes bot, queue workers, and starts polling.
"""
import asyncio
from pyrogram import Client, idle

from config.settings import API_ID, API_HASH, BOT_TOKEN, CONCURRENT_DOWNLOADS
from bot.handlers import register_handlers
from core.queue_manager import queue_manager
from core.processor import JobProcessor
from utils.logger import logger


async def main():
    """Main entry point."""
    # Validate credentials
    if not API_ID or not API_HASH:
        logger.error("API_ID and API_HASH not set! Get them from https://my.telegram.org")
        return
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Get it from @BotFather")
        return
    
    logger.info("=" * 50)
    logger.info("Starting KeepItAllBot (Pyrogram - 2GB uploads!)")
    logger.info("=" * 50)
    
    # Create Pyrogram client
    app = Client(
        name="keepitallbot",
        api_id=int(API_ID),
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        workers=CONCURRENT_DOWNLOADS * 2,  # More workers for handling updates
    )
    
    # Register message handlers
    register_handlers(app)
    
    # Start bot
    await app.start()
    logger.info("Bot started successfully!")
    
    # Create processor with bot instance
    processor = JobProcessor(app)
    
    # Set processor for queue
    queue_manager.set_processor(processor.process)
    
    # Start queue workers
    await queue_manager.start()
    logger.info(f"Queue started with {CONCURRENT_DOWNLOADS} workers")
    
    # Keep running
    logger.info("Bot is running... Press Ctrl+C to stop")
    await idle()
    
    # Cleanup
    await queue_manager.stop()
    await app.stop()
    logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
