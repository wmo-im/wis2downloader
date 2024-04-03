from abc import ABC, abstractmethod
import urllib3
from urllib.parse import urlsplit
import hashlib
import base64
import os
from datetime import datetime as dt
from pathlib import Path
import logging
from wis2downloader.queuer import BaseQueue

LOGGER = logging.getLogger(__name__)


class BaseDownloader(ABC):

    @abstractmethod
    def start(self):
        """Start the download worker to
        process messages from the queue indefinitely"""
        pass

    @abstractmethod
    def download(self, url: str, save_path: str):
        """Download a file from a URL to a specified save path"""
        pass

    @abstractmethod
    def verify_download(self, file_path: str, expected_hash: str, hash_function: function) -> bool:  # noqa
        """Verify the downloaded file's integrity by comparing its hash to the expected hash"""
        pass


class DownloadWorker(BaseDownloader):
    def __init__(self, queue: BaseQueue, subscriptions: dict = {}):
        self.http = urllib3.PoolManager()
        self.queue = queue
        self.subscriptions = subscriptions
        self.running = False

    def start(self):
        self.running = True
        while self.running:
            LOGGER.debug(f"Messages in queue: {self.queue.size()}")
            job = self.queue.dequeue()

            # Get the hash and hash function from the job
            expected_hash = job.get('payload', {}).get(
                'properties', {}).get('integrity', {}).get('hash')
            method = job.get('payload', {}).get(
                'properties', {}).get('integrity', {}).get('method')
            hash_function = getattr(hashlib, method, None)

            def get_todays_date():
                """
                Returns today's date in the format yyyy/mm/dd.
                """
                today = dt.now()
                yyyy = f"{today.year:04}"
                mm = f"{today.month:02}"
                dd = f"{today.day:02}"

                return f"{yyyy}/{mm}/{dd}"

            def handle_directory():
                """
                Creates the required directory
                for each downloaded file to be saved to.
                """
                topic = job.get('topic')
                base = self.subscriptions.get(topic, None)
                base_path = Path(base)

                dataid = job.get('payload', {}).get(
                    'properties', {}).get('dataid')
                dataid_no_colons = dataid.replace(":", "")
                dataid_path = Path(dataid_no_colons)

                today = get_todays_date()

                # Create the directory path
                save_directory = Path(base_path, today, dataid_path)
                save_directory.parent.mkdir(parents=True, exist_ok=True)

                return save_directory

            save_path = handle_directory()
            LOGGER.debug(f"Directory created at: {save_path}")

            # Now download the files
            links = job.get('payload', {}).get('links', [])

            for link in links:
                if link.get('rel') == 'canonical':
                    url = link.get('href')
                    self.download(url. save_path)
                    self.verify_download(
                        save_path, expected_hash, hash_function)

            self.queue.task_done()

    def download(self, url: str, save_path: str):
        path = urlsplit(url).path
        filename = os.path.basename(path)
        LOGGER.info(f"Attempting to download {filename}")

        # If file already in output directory, do not download
        # Note: Since the data id is unique every 24
        # hours, and the save path includes the
        # current date, this uniqueness check is
        # equivalent to checking if the data id has
        # already been downloaded today.
        if save_path.is_file():
            LOGGER.info(f"File {filename} already downloaded. Skipping.")
            return

        download_start = dt.now()

        try:
            response = self.http.request('GET', url)
            # Get the filesize in KB
            filesize = len(response.data) / 1024
        except Exception as e:
            LOGGER.error(f"Error downloading {url}")
            LOGGER.error(e)

        try:
            save_path.write_bytes(response.data)
            download_end = dt.now()
            download_time = download_end - download_start
            LOGGER.info(f"Downloaded {filename} of size {round(filesize, 2)}KB in {round(download_time, 2)} seconds")  # noqa
            response.release_conn()
        except Exception as e:
            LOGGER.error(f"Error saving to disk: {save_path}/{filename}")
            LOGGER.error(e)

    def verify_download(self, file_path: str, expected_hash: str, hash_function: function) -> bool:  # noqa
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
                hash_value = hash_function(file_content).digest()
            # Encode the hash to Base64
            hash_value_base64 = base64.b64encode(hash_value).decode('utf-8')

            if hash_value_base64 == expected_hash:
                LOGGER.debug(f"File {file_path} verified successfully.")
                return True
            else:
                LOGGER.warning(f"File {file_path} verification failed. Expected {expected_hash}, got {hash_value_base64}.")  # noqa
                return False
        except Exception as e:
            LOGGER.error(f"Error verifying download for {file_path}: {e}")
            return False
