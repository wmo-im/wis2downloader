from prometheus_client import Counter, Gauge


QUEUE_SIZE = Gauge(
    'queue_size', 'Current size of the job queue')
DOWNLOADED_BYTES = Counter(
    'downloaded_bytes', 'Total number of downloaded bytes',
    ['topic', 'centre_id', 'file_type'])
DOWNLOADED_FILES = Counter(
    'downloaded_files', 'Total number of downloaded files',
    ['topic', 'centre_id', 'file_type'])
FAILED_DOWNLOADS = Counter(
    'failed_downloads', 'Total number of failed downloads',
    ['topic', 'centre_id'])
TOPIC_STATUS = Gauge(
    'topic_subscription_status', 'Subscription status of a given topic',
    ['topic'])
