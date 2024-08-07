import re

from wis2downloader.log import LOGGER


def validate_target(target) -> tuple:
    """
    Validates the target path by searching for any non-whitelisted characters.

    Args:
        target (str): The target path to validate.

    Returns:
        tuple (bool, str): The validation result and an error message.
    """
    # Early return for topic hierarchy target
    if target == "$TOPIC":
        return True, ""

    # Allowed characters
    allowed_chars = "A-Za-z0-9/_-"

    # Bad characters are the negation of the allowed characters
    bad_chars = re.compile(f'[^{allowed_chars}]')

    bad_target_error = "Invalid target"

    if bad_chars.search(target):
        LOGGER.warning("Invalid target passed to add_subscription")
        return False, bad_target_error

    return True, ""
