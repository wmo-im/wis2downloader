import json
from pathlib import Path
import threading
from uuid import uuid4

import click

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from prometheus_client import generate_latest, REGISTRY


from wis2downloader import stop_event
from wis2downloader.downloader import DownloadWorker
from wis2downloader.log import LOGGER, setup_logger
from wis2downloader.queue import SimpleQueue, QMonitor
from wis2downloader.subscriber import MQTTSubscriber, BaseSubscriber
from wis2downloader.utils.validate_target import validate_target
from wis2downloader.utils.validate_topic import validate_topic
from wis2downloader.utils.config import load_config

CONFIG = load_config()


setup_logger(loglevel = 'INFO',
             save = CONFIG['save_logs'],
             log_path = CONFIG['log_path'])

# Create the queue
jobQ = SimpleQueue()

# Now set up the different threads
# 2) download workers
# 3) subscriber

# Start workers to process the jobs from the queue
worker_threads = []
for idx in range(CONFIG['download_workers']):
    worker = DownloadWorker(jobQ, CONFIG['download_dir'],
                            CONFIG['max_disk_usage'])
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_threads.append(worker_thread)
    worker_thread.start()

# Now create the MQTT subscriber
mqtt_session = Path(CONFIG['mqtt_session_info'])
if mqtt_session is None:
    mqtt_session = ".session.json"

mqtt_session = Path(mqtt_session)
if mqtt_session.is_file():
    with open(mqtt_session) as fh:
        session_info = json.load(fh)
        if session_info.get('client_id') is None:
            session_info['client_id'] = str(uuid4())
else:
    session_info = {
        'topics': {},
        'client_id': str(uuid4())
    }

LOGGER.info(session_info)

subscriber = MQTTSubscriber(
    CONFIG['broker_hostname'],
    CONFIG['broker_port'],
    CONFIG['broker_username'],
    CONFIG['broker_password'],
    CONFIG['broker_protocol'],
    jobQ,
    session_info['client_id']
)

# Now spawn subscriber as thread
mqtt_thread = threading.Thread(target=subscriber.start, daemon=True)
mqtt_thread.start()

# Add default subscriptions
for topic, target in session_info['topics'].items():
    is_topic_valid, _ = validate_topic(topic)
    if not is_topic_valid:
        LOGGER.warning(
            "Invalid topic in default config, please check config file")
        continue

    is_target_valid, _ = validate_target(target)
    if not is_target_valid:
        LOGGER.warning(
            "Invalid target in default config, please check config file")
        continue

    subscriber.add_subscription(topic, target)

# Provided the app.run() call is blocking, the following code will only
# be executed when the Flask app is stopped
def shutdown():
    LOGGER.info("Shutting down")

    # Stop the subscriber first
    subscriber.stop()

    # Signal all other threads to stop
    stop_event.set()

    # now join mqtt thread
    mqtt_thread.join()
    LOGGER.info("Subscriber thread stopped")

    for worker in worker_threads:
        LOGGER.info("Shutting down worker threads")
        # If download worker is blocked waiting for a job, send one
        if jobQ.size() == 0:
            jobQ.enqueue({'shutdown': True})
        worker.join()


# Create flask instance
app = Flask(__name__, instance_relative_config=True)
# enable cross origin support
CORS(app)

# Define routes
@app.route('/metrics')
def expose_metrics():
    """
    Expose the Prometheus metrics to be scraped.
    """
    return Response(generate_latest(REGISTRY), mimetype="text/plain")

@app.get('/subscriptions')
@app.route('/subscriptions/list')
def list_subscriptions():
    subs = subscriber.list_subscriptions()
    return Response(response=json.dumps(subs), status=200,
                    mimetype="application/json")

@app.post('/subscriptions')
@app.route('/subscriptions/add')
def add_subscription():
    # Topic validation
    topic = request.args.get('topic')
    is_topic_valid, msg = validate_topic(topic)

    if not is_topic_valid:
        return jsonify({"error": msg}), 400

    # Target validation
    target = request.args.get('target')
    if target in (None, "$TOPIC"):
        target = "$TOPIC"

    is_target_valid, msg = validate_target(target)

    if not is_target_valid:
        return jsonify({"error": msg}), 400

    subs = subscriber.add_subscription(topic, target)

    session_info['topics'][topic] = target

    with open(CONFIG['mqtt_session_info'],'w') as fh:
        json.dump(session_info, fh)

    return Response(response=json.dumps(subs), status=200,
                    mimetype="application/json")

@app.delete('/subscriptions')
@app.route('/subscriptions/delete')
def delete_subscription():
    # Topic validation
    topic = request.args.get('topic')
    is_topic_valid, msg = validate_topic(topic)

    if not is_topic_valid:
        return jsonify({"error": msg}), 400

    subs = subscriber.delete_subscription(topic)

    del session_info['topics'][topic]

    with open(CONFIG['mqtt_session_info'],'w') as fh:
        json.dump(session_info, fh)

    return Response(response=json.dumps(subs), status=200,
                    mimetype="application/json")

@click.command()
@click.pass_context
def run(ctx):
    app.run(debug=True, host=CONFIG['flask_host'], port=CONFIG['flask_port'], use_reloader=False)
    shutdown()


if __name__ == '__main__':  # run locally, for testing
    run()
