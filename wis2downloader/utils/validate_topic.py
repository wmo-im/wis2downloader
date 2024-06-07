from pywis_topics.topics import TopicHierarchy
from pywis_topics.bundle import sync_bundle

from wis2downloader.log import LOGGER, setup_logger

def validate_topic(topic) -> tuple:
    """
    Validates the topic using pywis-topics.

    Args:
        topic (str): The topic to validate.

    Returns:
        tuple (bool, str): The validation result and an error message.
    """
    no_topic_error = "No topic was provided. Please provide a valid topic"

    if topic is None or len(topic) == 0:
        LOGGER.error(no_topic_error)
        return False, no_topic_error

    # Use pywis-topics to validate the topic: strict=False allows for wildcards
    sync_bundle()
    th = TopicHierarchy()
    is_valid = th.validate(topic, strict=False)

    bad_topic_error = "Invalid topic. It should not contain special characters, backslashes, or escape codes"  # noqa

    if not is_valid:
        LOGGER.error(bad_topic_error)
        return False, bad_topic_error

    return True, ""