from flask import Flask, request
import socket
import json
import os
import sys
import time
import threading
import argparse
import logging
from wis2downloader.subscriber import MQTTSubscriber
from wis2downloader.queuer import SimpleQueue
from wis2downloader.downloader import DownloadWorker

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)
LOGGER = logging.getLogger(__name__)


def find_open_port():
    """
    To avoid port conflicts, this function finds an open port
    dynamically for the Flask app to use.
    """
    # Create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to a random aviailable port
    # (0 means the OS will choose a random port for us)
    s.bind(('127.0.0.1', 0))

    # Get the port number
    port = s.getsockname()[1]

    # Close the socket
    s.close()

    return port


def log_queue_size():
    """
    This logs the queue size once every minute.
    """
    queue = SimpleQueue()
    while True:
        LOGGER.info(f"Queue size: {queue.size()}")
        time.sleep(60)


def create_app(subscriber: MQTTSubscriber, subscriptions: dict, download_dir: str):
    """
    Starts the Flask app server and enables
    the addition or deletion of topics to the
    concurrent susbcription.
    It also spawns multiple download workers to
    handle the downloading and verification of the data.

    Args:
        subscriber (MQTTSubscriber): _description_,
        subscriptions (dict): _description_,
        download_dir (str): _description_
    """
    LOGGER.debug("Creating Flask app...")

    # Create the Flask app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    # Set the number of worker threads to the
    # number of CPUs available - 2
    num_workers = os.cpu_count() - 2

    # Start the download workers for each thread
    for _ in range(num_workers):
        t = threading.Thread(
            target=DownloadWorker(), args=(SimpleQueue(), subscriptions),
            daemon=True
        )
        t.start()

    # Enable adding, deleting, or listing subscriptions
    @app.route('/wis2/subscriptions/add')
    def add_subscription():
        topic = request.args.get('topic')
        return subscriber.add_subscription(topic, download_dir)

    @app.route('/wis2/subscriptions/delete')
    def delete_subscription():
        topic = request.args.get('topic')
        return subscriber.delete_subscription(topic)

    @app.route('/wis2/subscriptions/list')
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
    parser = argparse.ArgumentParser(
        description="WIS2 Downloader app configuration")
    parser.add_arugment(
        "--config", default="config.json",
        help="Path to the Flask app configuration file"
    )
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    broker_url = config.get("broker_url", "globalbroker.meteo.fr")
    broker_port = config.get("broker_port", 443)
    username = config.get("username", "everyone")
    password = config.get("password", "everyone")
    protocol = config.get("protocol", "websockets")
    topics = config.get("topics", [])
    download_dir = config.get("download_dir", ".")
    flask_host = config.get("flask_host", "127.0.0.1"),
    flask_port = config.get("flask_port", find_open_port())

    # Start MQTT subscriber thread
    subscriber = MQTTSubscriber(
        broker_url, broker_port, username, password, protocol
    )
    mqtt_thread = threading.Thread(
        target=subscriber.client.loop_forever, daemon=True)
    mqtt_thread.start()

    # Start a queue thread that logs every minute
    queue_logger_thread = threading.Thread(
        target=log_queue_size,
        daemon=True
    )
    queue_logger_thread.start()

    # Build a dictionary for the topic - save path mapping
    subscriptions = {t: download_dir for t in topics}

    # Start the Flask app
    try:
        app = create_app(subscriber=subscriber,
                         subscriptions=subscriptions,
                         download_dir=download_dir)
    except Exception as e:
        LOGGER.error(f"Error creating Flask app: {e}")

    app.run(host=flask_host, port=flask_port, debug=True, use_reloader=False)

    # Add topics already in the configuration
    # to the subscription
    for topic in subscriptions:
        save_path = subscriptions[topic]
        subscriber.add_subscription(topic, save_path)


if __name__ == '__main__':
    main()
