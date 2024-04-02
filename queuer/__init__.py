from abc import ABC, abstractmethod
from queue import Queue


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


class SimpleQueue(BaseQueue):
    def __init__(self):
        self._queue = Queue()

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
