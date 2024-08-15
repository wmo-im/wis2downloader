import pytest
import os
import tempfile
from wis2downloader.app import app

config = """
{
    "base_url": "http://localhost:5050",
    "broker_hostname": "globalbroker.meteo.fr",
    "broker_password": "everyone",
    "broker_port": 443,
    "broker_protocol": "websockets",
    "broker_username": "everyone",
    "download_workers": 1,
    "download_dir": "downloads",
    "flask_host": "0.0.0.0",
    "flask_port": 5050,
    "log_level": "DEBUG",
    "log_path": "logs",
    "min_free_space": 10,
    "mqtt_session_info" : "mqtt_session.json",
    "save_logs": false,
    "validate_topics": true
}
"""


@pytest.fixture(scope='session', autouse=True)
def set_env():
    # Create a temporary file with the config content
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as tp:
        tp.write(config)
        tp.flush()
        os.environ['WIS2DOWNLOADER_CONFIG'] = tp.name


@pytest.fixture()
def client():
    with app.test_client() as client:
        yield client


@pytest.fixture()
def runner():
    return app.test_cli_runner()
