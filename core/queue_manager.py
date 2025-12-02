"""
Async queue manager for download jobs.
"""
import asyncio
from dataclasses import dataclass
from typing import Callable, Awaitable, Optional
from config.settings import CONCURRENT_DOWNLOADS
from utils.logger import logger


@dataclass
class DownloadJob:
    """Download job container."""
    user_id: int
    chat_id: int
    message_id: int
    url: str
    status_message_id: Optional[int] = None


class QueueManager:
    """
    Async queue manager with worker pool.
    """
    
    def __init__(self, num_workers: int = CONCURRENT_DOWNLOADS):
        self.num_workers = num_workers
        self.queue: asyncio.Queue[DownloadJob] = asyncio.Queue()
        self.workers: list[asyncio.Task] = []
        self._processor: Optional[Callable[[DownloadJob], Awaitable[None]]] = None
        self._running = False
    
    def set_processor(self, processor: Callable[[DownloadJob], Awaitable[None]]) -> None:
        """
        Set the job processor function.
        
        Args:
            processor: Async function to process each job
        """
        self._processor = processor
    
    async def add_job(self, job: DownloadJob) -> int:
        """
        Add a job to the queue.
        
        Args:
            job: DownloadJob to add
            
        Returns:
            Queue position (1-based)
        """
        await self.queue.put(job)
        position = self.queue.qsize()
        logger.info(f"Job queued: user={job.user_id}, url={job.url}, position={position}")
        return position
    
    async def _worker(self, worker_id: int) -> None:
        """
        Worker coroutine that processes jobs from queue.
        
        Args:
            worker_id: Worker identifier for logging
        """
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Wait for a job with timeout to allow shutdown
                try:
                    job = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                if self._processor:
                    logger.info(f"Worker {worker_id} processing: {job.url}")
                    try:
                        await self._processor(job)
                    except Exception as e:
                        logger.error(f"Worker {worker_id} error: {e}")
                    finally:
                        self.queue.task_done()
                else:
                    logger.warning("No processor set, skipping job")
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} unexpected error: {e}")
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def start(self) -> None:
        """Start worker pool."""
        if self._running:
            return
        
        self._running = True
        logger.info(f"Starting {self.num_workers} queue workers")
        
        for i in range(self.num_workers):
            worker = asyncio.create_task(self._worker(i + 1))
            self.workers.append(worker)
    
    async def stop(self) -> None:
        """Stop worker pool gracefully."""
        logger.info("Stopping queue workers...")
        self._running = False
        
        # Wait for queue to empty (with timeout)
        try:
            await asyncio.wait_for(self.queue.join(), timeout=30)
        except asyncio.TimeoutError:
            logger.warning("Queue did not empty in time")
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()
        logger.info("Queue workers stopped")
    
    @property
    def pending_jobs(self) -> int:
        """Get number of pending jobs."""
        return self.queue.qsize()
    
    @property
    def is_running(self) -> bool:
        """Check if queue is running."""
        return self._running


# Global queue manager instance
queue_manager = QueueManager()
