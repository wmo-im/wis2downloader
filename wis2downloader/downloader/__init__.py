from abc import ABC, abstractmethod
import urllib3
from urllib.parse import urlsplit
import hashlib
import base64
import os
from datetime import datetime as dt
from pathlib import Path
import enum

from wis2downloader import shutdown
from wis2downloader.log import LOGGER, setup_logger
from wis2downloader.queue import BaseQueue
from wis2downloader.metrics import DOWNLOADED_BYTES, DOWNLOADED_FILES, FAILED_DOWNLOADS

from typing import Callable


class BaseDownloader(ABC):

    @abstractmethod
    def start(self):
        """Start the download worker to
        process messages from the queue indefinitely"""
        pass

    @abstractmethod
    def process_job(self, job):
        """Process a single job from the queue"""
        pass

    @abstractmethod
    def get_hash_info(self, job):
        """Extract the hash value and function from the job
        to be used for verification later"""
        pass

    @abstractmethod
    def get_download_link(self, job):
        """Extract the download link from the job"""
        pass

    @abstractmethod
    def extract_filename(self, _url, job):
        """Extract the filename from the download link"""
        pass

    @abstractmethod
    def validate_data(self, data, expected_hash, hash_function):
        """Validate the hash and size of the downloaded data against
        the expected values"""
        pass

    @abstractmethod
    def save_file(self, data, target, filename, filesize, download_start):
        """Save the downloaded data to disk"""


def get_todays_date():
    """
    Returns today's date in the format yyyy/mm/dd.
    """
    today = dt.now()
    yyyy = f"{today.year:04}"
    mm = f"{today.month:02}"
    dd = f"{today.day:02}"
    return yyyy, mm, dd


class VerificationMethods(enum.Enum):
    sha256 = 'sha256'
    sha384 = 'sha384'
    sha512 = 'sha512'
    sha3_256 = 'sha3_256'
    sha3_384 = 'sha3_384'
    sha3_512 = 'sha3_512'


class DownloadWorker(BaseDownloader):
    def __init__(self, queue: BaseQueue, basepath: str = "."):
        self.http = urllib3.PoolManager()
        self.queue = queue
        self.basepath = Path(basepath)

    def start(self):
        LOGGER.info("Starting download worker")
        while not shutdown.is_set():
            # First get the job from the queue
            job = self.queue.dequeue()
            if job.get('shutdown', None):
                break

            self.process_job(job)

            self.queue.task_done()

    def process_job(self, job):
        yyyy, mm, dd = get_todays_date()
        output_dir = self.basepath / yyyy / mm / dd

        # Add target to output directory
        output_dir = output_dir / job.get("target", ".")

        # Get information about the job for verification later
        expected_hash, hash_function = self.get_hash_info(job)
        expected_size = job.get('payload', {}).get('content', {}).get('size')

        # Get the download link and update status
        _url, update = self.get_download_link(job)

        # Extract the filename from the download link
        filename = self.extract_filename(_url, job)

        if filename is None:
            LOGGER.info(f"Could not extract filename from {_url}")
            return

        target = output_dir / filename
        # Create parent dir if it doesn't exist
        target.parent.mkdir(parents=True, exist_ok=True)

        # Only download if file doesn't exist or is an update
        if (target.is_file()) and (not update):
            LOGGER.info(f"Skipping download of {filename}, already exists")
            return

        download_start = dt.now()

        # Download the file
        response = None
        try:
            response = self.http.request('GET', _url)
            # Get the filesize in KB
            filesize = len(response.data)
            # Increment metrics
            DOWNLOADED_BYTES.inc(filesize)
            DOWNLOADED_FILES.inc()
        except Exception as e:
            LOGGER.error(f"Error downloading {_url}")
            LOGGER.error(e)
            # Increment failed download counter
            FAILED_DOWNLOADS.inc()
            return

        if response is None:
            return

        # Use the hash function to determine whether to save the data
        save_data = self.validate_data(
            response.data, expected_hash, hash_function, expected_size)

        if not save_data:
            LOGGER.warning(f"Download {filename} failed verification, discarding")  # noqa
            # Increment failed download counter
            FAILED_DOWNLOADS.inc()
            return

        # Now save
        self.save_file(response.data, target, filename,
                       filesize, download_start)

    def get_hash_info(self, job):
        expected_hash = job.get('payload', {}).get(
            'properties', {}).get('integrity', {}).get('hash')
        hash_method = job.get('payload', {}).get(
            'properties', {}).get('integrity', {}).get('method')

        hash_function = None

        # Check if hash method is known using our enumumeration of hash methods
        if hash_method in VerificationMethods._member_names_:
            method = VerificationMethods[hash_method].value
            hash_function = hashlib.new(method)

        return expected_hash, hash_function

    def get_download_link(self, job):
        links = job.get('payload', {}).get('links', [])
        _url = None
        update = False
        for link in links:
            if link.get('rel') == 'update':
                _url = link.get('href')
                update = True
                break
            elif link.get('rel') == 'canonical':
                _url = link.get('href')
                break

        return _url, update

    def extract_filename(self, _url, job):
        if _url is None:
            LOGGER.info(f"No download link found in job {job}")
            return None
        path = urlsplit(_url).path
        return os.path.basename(path)

    def validate_data(self, data, expected_hash, hash_function, expected_size):
        if None in (expected_hash, hash_function,
                    hash_function):
            return True

        hash_value = hash_function(data).digest()
        hash_value = base64.b64encode(hash_value).decode()
        if (hash_value != expected_hash) or (len(data) != expected_size):
            return False

        return True

    def save_file(self, data, target, filename, filesize, download_start):
        try:
            target.write_bytes(data)
            download_end = dt.now()
            download_time = download_end - download_start
            download_seconds = round(download_time.total_seconds(), 2)
            LOGGER.info(
                f"Downloaded {filename} of size {filesize} bytes in {download_seconds} seconds")  # noqa
        except Exception as e:
            LOGGER.error(f"Error saving to disk: {target}")
            LOGGER.error(e)
