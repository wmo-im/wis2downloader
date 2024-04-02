from abc import ABC, abstractmethod
import urllib3
from urllib.parse import urlsplit
import base64
import os
from datetime import datetime as dt
import logging

LOGGER = logging.getLogger(__name__)


class BaseDownloader(ABC):

    @abstractmethod
    def download(self, url: str, save_path: str):
        """Download a file from a URL to a specified save path"""
        pass

    @abstractmethod
    def verify_download(self, file_path: str, expected_hash: str, hash_function: function) -> bool: # noqa
        """Verify the downloaded file's integrity by comparing its hash to the expected hash"""
        pass


class Downloader(BaseDownloader):
    def __init__(self):
        self.http = urllib3.PoolManager()

    def download(self, url: str, save_path: str):
        path = urlsplit(url).path
        filename = os.path.basename(path)
        LOGGER.info(f"Attempting to download {filename}")

        # If file already in output directory, do not download
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

    def verify_download(self, file_path: str, expected_hash: str, hash_function: function) -> bool: # noqa
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
                LOGGER.warning(f"File {file_path} verification failed. Expected {expected_hash}, got {hash_value_base64}.") # noqa
                return False
        except Exception as e:
            LOGGER.error(f"Error verifying download for {file_path}: {e}")
            return False
