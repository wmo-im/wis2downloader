import argparse
import json
import os
import threading
from datetime import datetime as dt

from flask import Flask, request

from wis2downloader import shutdown
from wis2downloader.log import LOGGER, setup_logger
from wis2downloader.subscriber import MQTTSubscriber, BaseSubscriber
from wis2downloader.queue import SimpleQueue, QMonitor
from wis2downloader.downloader import DownloadWorker
import re


def validate_topic(topic) -> bool:
    """
    Validate the topic for special characters, backslashes,
    or escape codes.

    Args:
        topic (str): The topic to validate.

    Returns:
        bool: True if the topic is valid, False otherwise.
    """
    # Pattern for characters not allowed in topic (special characters except #)
    bad_chars = re.compile('[@_!$%^&*()<>?|}{~:]')

    bad_topic_error = "Invalid topic. It should not contain special characters, backslashes, or escape codes"  # noqa

    if (bad_chars.search(topic) is not None
            or '\\' in topic or '\n' in topic
            or '\t' in topic or '\r' in topic):
        LOGGER.error(bad_topic_error)
        return False

    return True


def clean_target(target) -> str:
    """
    Cleans the target path by removing special characters.

    Args:
        target (str): The target path to validate.

    Returns:
        str: The sanitised target path.
    """
    # Pattern for special characters
    special_chars = re.compile('[@_!#$%^&*()<>?|}{~:]')

    if special_chars.search(target) is not None:
        # Get unique character offenses to display in warning
        char_matches = set(special_chars.findall(target))
        char_matches_str = ', '.join(char_matches)
        LOGGER.warning(f"Target contains invalid characters ({char_matches_str}), these will be automatically removed")  # noqa
        return special_chars.sub('', target)

    return target


def create_app(subscriber: BaseSubscriber):
    """
    Starts the Flask app server and enables
    the addition or deletion of topics to the
    concurrent subscription.
    It also spawns multiple download workers to
    handle the downloading and verification of the data.

    Args:
        subscriber (BaseSubscriber): A subscriber to listen for new data
            notifications. Any subscriber derived from the base subscriber
            class.
    """
    LOGGER.debug("Creating Flask app...")

    # Create the Flask app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    # Enable adding, deleting, or listing subscriptions
    @app.route('/add')
    def add_subscription():
        topic = request.args.get('topic')
        is_topic_valid = validate_topic(topic)
        if not is_topic_valid:
            return

        target = request.args.get('target')
        if target is None:
            target = "$TOPIC"
        else:
            clean_target(target)

        return subscriber.add_subscription(topic, target)

    @app.route('/delete')
    def delete_subscription():
        topic = request.args.get('topic')
        is_topic_valid = validate_topic(topic)

        if not is_topic_valid:
            return

        return subscriber.delete_subscription(topic)

    @app.route('/list')
    def list_subscriptions():
        return subscriber.list_subscriptions()

    return app


def main():
    """
    Main function to run the Flask app server,
    which uses the WIS2 downloader sub-modules
    (subscriber, queuer, downloader) to download
    the latest data.
    """

    # Get CLI arguments passed (currently path to config.json)
    parser = argparse.ArgumentParser(
        description="WIS2 Downloader app configuration")
    parser.add_argument(
        "--config", default="config.json",
        help="Path to the Flask app configuration file"
    )
    args = parser.parse_args()

    # Now load config settings for downloader
    with open(args.config, "r") as f:
        config = json.load(f)

    # Extract MQTT options
    broker_url = config.get("broker_url", "globalbroker.meteo.fr")
    broker_port = config.get("broker_port", 443)
    username = config.get("username", "everyone")
    password = config.get("password", "everyone")
    protocol = config.get("protocol", "websockets")

    # Download options, i.e. where to write data to, number of workers
    topics = config.get("topics", {})
    download_dir = config.get("download_dir", ".")
    num_workers = config.get("download_workers", 1)

    # Flask options
    flask_host = config.get("flask_host", "127.0.0.1")
    flask_port = config.get("flask_port", 5000)

    # Finally if the user wants to save the logs to a file
    save_logs = config.get("save_logs", False)
    log_dir = config.get("log_dir", ".")

    # Set up logging
    if save_logs:
        # Create log dir if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        current_time = dt.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f'logs_{current_time}.txt')
        setup_logger(loglevel='INFO', logfile=log_file)
    else:
        setup_logger(loglevel='INFO')

    # Now set up the different threads (plus job queue)
    # 1) queue monitor
    # 2) download workers
    # 3) subscriber

    # Create the queue
    jobQ = SimpleQueue()

    # Start the queue monitor
    Q_monitor = threading.Thread(
        target=QMonitor, args=(jobQ,), daemon=True
    )
    Q_monitor.start()

    # Start workers to process the jobs from the queue
    worker_threads = []
    for idx in range(num_workers):
        worker = DownloadWorker(jobQ, download_dir)
        worker_threads.append(
            threading.Thread(target=worker.start, daemon=True)
        )
        worker_threads[idx].start()

    # Now create the MQTT subscriber
    subscriber = MQTTSubscriber(
        broker_url, broker_port, username, password, protocol, jobQ
    )

    # Now spawn subscriber as thread
    mqtt_thread = threading.Thread(
        target=subscriber.start, daemon=True)
    mqtt_thread.start()

    # Add default subscriptions
    for topic, target in topics.items():
        is_topic_valid = validate_topic(topic)
        if not is_topic_valid:
            continue

        # Remove special characters from target
        target = clean_target(target)

        subscriber.add_subscription(topic, target)

    # Now all background jobs / threads should be running, start the flask
    # backend for managing the subscriptions
    try:
        app = create_app(subscriber=subscriber)
    except Exception as e:
        LOGGER.error(f"Error creating Flask app: {e}")

    LOGGER.info(f"Flask host: {flask_host}, flask port: {flask_port}")
    app.run(host=flask_host, port=flask_port,
            debug=True, use_reloader=False)

    # Provided the app.run() call is blocking, the following code will only
    # be executed when the Flask app is stopped

    LOGGER.info("Shutting down")

    # Stop the subscriber first
    subscriber.stop()

    # Signal all other threads to stop
    shutdown.set()

    mqtt_thread.join()
    LOGGER.info("Subscriber thread stopped")

    LOGGER.info("Stopping queue monitor, this may take 60 seconds")
    Q_monitor.join()
    LOGGER.info("Queue monitor stopped")

    for worker in worker_threads:
        LOGGER.info("Shutting down worker threads")
        # If download worker is blocked waiting for a job, send one
        if jobQ.size() == 0:
            jobQ.enqueue({'shutdown': True})
        worker.join()


if __name__ == '__main__':
    main()
