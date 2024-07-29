import pytest
import os
import tempfile
from wis2downloader.app import create_app

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

tp = tempfile.NamedTemporaryFile(delete=False)
tp.write(config.encode())
tp.close()


def pytest_generate_tests(metafunc):
    os.environ['WIS2DOWNLOADER_CONFIG'] = tp.name


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixtuer()
def runner(app):
    return app.test_cli_runner()
