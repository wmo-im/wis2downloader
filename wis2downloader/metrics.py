from prometheus_client import Counter, Gauge, generate_latest, REGISTRY


QUEUE_SIZE = Gauge(
    'queue_size', 'Current size of the job queue')
DOWNLOADED_BYTES = Counter(
    'downloaded_bytes', 'Total number of downloaded bytes')
DOWNLOADED_FILES = Counter(
    'downloaded_files', 'Total number of downloaded files')
FAILED_DOWNLOADS = Counter(
    'failed_downloads', 'Total number of failed downloads')
