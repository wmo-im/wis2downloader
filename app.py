from flask import Flask, request
import socket
import json
import logging
import os
import sys
import time
import paho.mqtt.client as mqtt
from pathlib import Path
import queue
import ssl
import threading
import urllib3
from urllib.parse import urlsplit
import argparse
from datetime import datetime as dt
import hashlib
import base64

# LOGGER
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)
LOGGER = logging.getLogger(__name__)