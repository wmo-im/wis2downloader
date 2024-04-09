from abc import ABC, abstractmethod
from fnmatch import fnmatch
import json
from pathlib import Path
import ssl

import paho.mqtt.client as mqtt

from wis2downloader import shutdown
from wis2downloader.log import LOGGER, setup_logger
from wis2downloader.queue import BaseQueue


class BaseSubscriber(ABC):

    @abstractmethod
    def _on_connect(self, client, userdata, flags, rc):
        """Method to handle actions to take on connection to broker"""
        pass

    @abstractmethod
    def _on_disconnect(self, client, userdata, rc):
        """Method to handle actions to take when a connection is lost"""
        pass

    @abstractmethod
    def _on_message(self, client, userdata, msg):
        """Method to handle actions to take when a message is received"""
        pass

    @abstractmethod
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Method to handle actions to take when a subscription is made"""
        pass

    @abstractmethod
    def add_subscription(self, topic: str, save_path: str):
        """Method to add subscription to active subscriptions"""
        pass

    @abstractmethod
    def delete_subscription(self, topic: str):
        """Method to remove subscription from active subscriptions"""
        pass

    @abstractmethod
    def list_subscriptions(self) -> list:
        """Method to return list of active subscriptions"""
        pass

    @abstractmethod
    def start(self):
        """Method to start subscriber, e.g. loop_forever in paho-mqtt"""
        pass

    @abstractmethod
    def stop(self):
        """Method to stop subscriber, e.g. disconnect in paho-mqtt"""
        pass


class MQTTSubscriber(BaseSubscriber):
    def __init__(self, broker: str = "globalbroker.meteo.fr", port: int = 443, uid: str = "everyone", pwd: str = "everyone", protocol: str = "websockets", _queue: BaseQueue = None):

        LOGGER.debug("Initializing MQTT subscriber")

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, transport=protocol)
        self.client.tls_set(ca_certs=None, certfile=None, keyfile=None,
                            cert_reqs=ssl.CERT_REQUIRED,
                            tls_version=ssl.PROTOCOL_TLS,
                            ciphers=None)
        self.client.username_pw_set(uid, pwd)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe

        self.queue = _queue
        self.active_subscriptions = {}

        # Connect to the broker
        LOGGER.info("Connecting...")
        LOGGER.info(f"Host: {broker}, port: {port}")
        self.client.connect(host=broker, port=port)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            LOGGER.info("Connected successfully")
        elif reason_code > 0:
            LOGGER.error(f"Connection failed with error code {reason_code}")

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        if reason_code == 0:
            LOGGER.info("Disconnected successfully")
        elif reason_code > 0:
            LOGGER.error(f"Disconnection failed with error code {reason_code}")

    def _on_message(self, client, userdata, msg):
        # first check shutdown is not set
        if shutdown.is_set():
            self.client.disconnect()
        LOGGER.info(f"Message received under topic {msg.topic}")
        target = self.active_subscriptions.get(msg.topic, {}).get('target')
        # if a wild card is used in the subs target may not match
        if target is None:
            for key, value in self.active_subscriptions.items():
                if fnmatch(msg.topic, value['pattern']):
                    target = value['target']
                    break

        if target == "$TOPIC":
            target = msg.topic

        if "/" in target:
            subdirs = target.split("/")
            target = str(Path(*subdirs))

        if "\\" in target:
            subdirs = target.split("\\")
            target = str(Path(*subdirs))

        job = {
            'topic': msg.topic,
            'payload': json.loads(msg.payload),
            'target': target
        }
        self.queue.enqueue(job)

    def _on_subscribe(self, client, userdata, mid, reason_codes, properties):
        for sub_result in reason_codes:
            if sub_result in [0, 1, 2]:
                LOGGER.info("Subscription to topic successful")
            elif sub_result >= 128:
                LOGGER.error(
                    f"Subscription to topic failed with error code {sub_result}")  # noqa

    def add_subscription(self, topic: str, save_path: str = "."):
        self.client.subscribe(topic)
        self.active_subscriptions[topic] = {
            'target': save_path,
            'pattern': topic.replace("+", "*").replace("#", "*")
        }
        LOGGER.info(f"Subscribing to {topic}")
        return self.active_subscriptions

    def delete_subscription(self, topic: str):
        if topic in self.active_subscriptions:
            self.client.unsubscribe(topic)
            del self.active_subscriptions[topic]
            LOGGER.info(f"Unsubscribing from {topic}")
        else:
            LOGGER.info(f"Topic {topic} not found in active subscriptions")
        return self.active_subscriptions

    def list_subscriptions(self) -> dict:
        return self.active_subscriptions

    def start(self):
        self.client.loop_forever()

    def stop(self):
        self.client.disconnect()
