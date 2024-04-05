from abc import ABC, abstractmethod
import logging
from queue import Queue
import time

from wis2downloader import shutdown
from wis2downloader.log import LOGGER, setup_logger


class BaseQueue(ABC):

    @abstractmethod
    def enqueue(self, item):
        """Add an item to the queue"""
        pass

    @abstractmethod
    def dequeue(self):
        """Remove and return an item from the queue"""
        pass

    @abstractmethod
    def size(self) -> int:
        """Return the number of items in the queue"""
        pass

    @abstractmethod
    def task_done(self):
        """Indicate that a formerly enqueued task is complete"""
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """Check if the queue is empty"""
        pass

    @abstractmethod
    def is_active(self) -> bool:
        """
        Function that returns whether the queue is active
        """
        pass


class QMonitor:
    def __init__(self, _queue: BaseQueue, period:int = 60):
        while not shutdown.is_set():
            LOGGER.info(f"Queue size: {_queue.size()}")
            time.sleep(period)

class SimpleQueue(BaseQueue):
    def __init__(self):
        self._queue = Queue()
        self.active = True

    def enqueue(self, item):
        self._queue.put(item)

    def dequeue(self):
        return self._queue.get()

    def size(self) -> int:
        return self._queue.qsize()

    def task_done(self):
        self._queue.task_done()

    def is_empty(self) -> bool:
        return self._queue.empty()

    # Todo - always active, change to use flag that can be toggled
    def is_active(self):
        return self.active



class RedisQueue(BaseQueue):
    pass
