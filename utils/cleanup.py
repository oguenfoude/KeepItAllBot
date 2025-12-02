"""
Cleanup utilities for temporary files.
"""
import asyncio
import os
import time
from pathlib import Path
from typing import Optional
from utils.logger import logger
from config.settings import DOWNLOAD_PATH, CLEANUP_AFTER_MINUTES


def delete_file(file_path: Path | str) -> bool:
    """
    Delete a file safely.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if deleted, False otherwise
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            logger.info(f"Deleted file: {path.name}")
            return True
    except Exception as e:
        logger.error(f"Failed to delete {file_path}: {e}")
    return False


def cleanup_old_files(
    directory: Path = DOWNLOAD_PATH,
    max_age_minutes: int = CLEANUP_AFTER_MINUTES
) -> int:
    """
    Delete files older than max_age_minutes.
    
    Args:
        directory: Directory to clean
        max_age_minutes: Maximum file age in minutes
        
    Returns:
        Number of files deleted
    """
    deleted = 0
    cutoff = time.time() - (max_age_minutes * 60)
    
    try:
        for file_path in directory.iterdir():
            if file_path.is_file():
                try:
                    if file_path.stat().st_mtime < cutoff:
                        file_path.unlink()
                        deleted += 1
                        logger.info(f"Cleanup: deleted stale file {file_path.name}")
                except Exception as e:
                    logger.error(f"Cleanup: failed to delete {file_path}: {e}")
    except Exception as e:
        logger.error(f"Cleanup: error scanning directory: {e}")
    
    return deleted


async def periodic_cleanup(
    interval_minutes: int = 10,
    directory: Path = DOWNLOAD_PATH,
    max_age_minutes: int = CLEANUP_AFTER_MINUTES
) -> None:
    """
    Background task to periodically clean up old files.
    
    Args:
        interval_minutes: How often to run cleanup
        directory: Directory to clean
        max_age_minutes: Maximum file age
    """
    logger.info(f"Starting periodic cleanup (every {interval_minutes} min)")
    
    while True:
        try:
            await asyncio.sleep(interval_minutes * 60)
            deleted = cleanup_old_files(directory, max_age_minutes)
            if deleted > 0:
                logger.info(f"Periodic cleanup: removed {deleted} files")
        except asyncio.CancelledError:
            logger.info("Periodic cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}")


def get_directory_size(directory: Path = DOWNLOAD_PATH) -> int:
    """
    Get total size of files in directory.
    
    Args:
        directory: Directory to measure
        
    Returns:
        Total size in bytes
    """
    total = 0
    try:
        for file_path in directory.iterdir():
            if file_path.is_file():
                total += file_path.stat().st_size
    except Exception as e:
        logger.error(f"Error getting directory size: {e}")
    return total
