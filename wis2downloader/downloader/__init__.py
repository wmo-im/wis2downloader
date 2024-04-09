from abc import ABC, abstractmethod
import urllib3
from urllib.parse import urlsplit
import hashlib
import base64
import os
from datetime import datetime as dt
from pathlib import Path
import logging

from wis2downloader import shutdown
from wis2downloader.log import LOGGER, setup_logger
from wis2downloader.queue import BaseQueue

from typing import Callable


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
    def verify_download(self, file_path: str, expected_hash: str, hash_function: Callable) -> bool:  # noqa
        """Verify the downloaded file's integrity by comparing its hash to the expected hash"""
        pass


def get_todays_date():
    """
    Returns today's date in the format yyyy/mm/dd.
    """
    today = dt.now()
    yyyy = f"{today.year:04}"
    mm = f"{today.month:02}"
    dd = f"{today.day:02}"
    # return f"{yyyy}/{mm}/{dd}"
    return yyyy, mm, dd


class DownloadWorker(BaseDownloader):
    def __init__(self, queue: BaseQueue, basepath: str ="."):
        self.http = urllib3.PoolManager()
        self.queue = queue
        self.basepath = Path(basepath)

    def start(self):
        LOGGER.info("Starting download worker")
        while not shutdown.is_set():
            # First get the job from the queue
            job = self.queue.dequeue()
            if job.get('shutdown',None):
                break
            # get the topic
            topic = job.get('topic')

            # append date
            yyyy, mm, dd = get_todays_date()
            output_dir = self.basepath / yyyy / mm / dd

            # now target directory
            output_dir = output_dir / job.get("target", ".")

            # Get the hash and hash function from the job
            expected_hash = job.get('payload', {}).get(
                'properties', {}).get('integrity', {}).get('hash')
            hash_method = job.get('payload', {}).get(
                'properties', {}).get('integrity', {}).get('method')
            hash_function = None
            if hash_method is not None:
                hash_function = getattr(hashlib, hash_method, None)

            # get dataid from payload
            dataid = job.get('payload', {}).get('properties', {}).get('dataid')

            # now search for link to download from
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

            # extract file name from _url
            filename = None
            if _url is not None:
                path = urlsplit(_url).path
                global_cache = urlsplit(_url).hostname
                filename = os.path.basename(path)

            if filename is not None:
                target = output_dir / filename
                # create parent dir if it doesn't exist
                target.parent.mkdir(parents=True, exist_ok=True)
                # check if file exists, if not download
                if (not target.is_file()) or update:
                    #self.download(_url, target)
                    download_start = dt.now()

                    try:
                        response = self.http.request('GET', _url)
                        # Get the filesize in KB
                        filesize = len(response.data)
                    except Exception as e:
                        LOGGER.error(f"Error downloading {_url}")
                        LOGGER.error(e)

                    # validate data
                    save_data = True
                    if None not in (expected_hash, hash_function,
                                    hash_function):
                        hash_value = hash_function(response.data).digest()
                        hash_value = base64.b64encode(hash_value).decode()
                        if hash_value != expected_hash:
                            # don't save if file fails validation
                            save_data = False
                            LOGGER.warning(f"Download {filename} failed verification, discarding")  # noqa

                    # now save
                    if save_data:
                        try:
                            target.write_bytes(response.data)
                            download_end = dt.now()
                            download_time = download_end - download_start
                            LOGGER.info(
                                f"Downloaded {filename} of size {filesize} bytes in {download_time.total_seconds()} seconds")  # noqa
                            response.release_conn()
                        except Exception as e:
                            LOGGER.error(f"Error saving to disk: {target}")
                            LOGGER.error(e)

            self.queue.task_done()




    def download(self, url: str, save_path: Path):
        path = urlsplit(url).path
        filename = os.path.basename(path)
        LOGGER.info(f"Attempting to download {filename}")

        # If file already in output directory, do not download
        # Note: Since the data id is unique every 24
        # hours, and the save path includes the
        # current date, this uniqueness check is
        # equivalent to checking if the data id has
        # already been downloaded today.

        #if save_path.is_file():
        #    LOGGER.info(f"File {filename} already downloaded. Skipping.")
        #    return

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
            LOGGER.error(f"Error saving to disk: {save_path}")
            LOGGER.error(e)

    def verify_download(self, file_path: str, expected_hash: str, hash_function: Callable) -> bool:  # noqa
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
