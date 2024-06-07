# The WIS2 Downloader
### The backend tool for subscribing to the latest data on the WIS2 network.

<a href="https://github.com/wmo-im/wis2-downloader/blob/main/LICENSE" alt="License" ><img src="https://img.shields.io/badge/License-Apache_2.0-blue"></img></a>

The WIS2 Downloader is a Flask-based Python application that allows you to connect to a WIS2 Global Broker, manage subscriptions to topic hierarchies, and configure their associated download directories.

## Features

- **Dynamic Subscription Management**: Quickly add or remove subscriptions ad hoc without needing to restart the service or change configuration files.
- **Monitor Download Statistics**: Access the Prometheus metrics through the `/metrics` endpoint, ideal for <a href="https://prometheus.io/docs/visualization/grafana/">Grafana visualization</a>.
- **Multi-Threading Support**: Configure the number of download workers for more efficient data downloading.

## Getting Started

### 1. Installation
You can install using Pip:

```bash
pip install wis2downloader
```

### 2. Configuration

Create a file `config.json` in your local directory, with the following contents:

```json
{
    "broker_hostname": "globalbroker.meteo.fr",
    "broker_password": "everyone",
    "broker_port": 443,
    "broker_protocol": "websockets",
    "broker_username": "everyone",
    "download_workers": 1,
    "download_dir": "downloads",
    "flask_host": "0.0.0.0",
    "flask_port": 5050,
    "log_path": "logs",
    "max_disk_usage": 10,
    "save_logs": false,
    "mqtt_session_info" : "mqtt_session.json"
}
```

This file is used by the WIS2 downloader and specifies to connect to the WIS2 global broker run by MétéoFrance, 
with one download worker and saves the downloaded files to a folder called downloads relative to the current working 
directory.

### 3. Running

1. Set an environment variable specifying the path to the config.json file.

*Linux (bash)* 
```bash
export WIS2DOWNLOADER_CONFIG=<path_to_your_config_file> 
```

*Windows (Command Prompt)*
```
set WIS2DOWNLOADER_CONFIG=<path_to_your_config_file>
```


2. Start the downloader

*Dev mode (Windows and Linux)*

```bash
wis2downloader
```

*Using gunicorn (Linux only)*
```
gunicorn -w 1 wis2downloader
```

**Note**: Only one worker is supported due to the downloader spawning additional threads and persistence of MQTT
connections.

The Flask application should now be running. If you need to stop the application, you can do so in the terminal 
with `Ctrl+C`.

## Maintaining and Monitoring Subscriptions

The API defintion of the downloader can be found at the `./swagger` endpoint, e.g. when run locally see
http://localhost:5050/swagger

### Adding subscriptions
Subscriptions can be added via a GET request to the `./subscriptions` endpoint on the Flask app, with the following form:

```bash
curl -X POST http://<flask-host>:<flask-port>/subscriptions?topic=<topic-name>&target=<download-directory>
```

- `topic` specifies the topic to subscribe to. *Special characters (+, #) must be URL encoded, i.e. `+` = `%2B`, `#` = `%23`.*
- `target` specifies the directory to save the downloads to, relative to `download_dir` from `config.json`. *If this is not provided, the directory will default to that of the topic hierarchy.*

For example:
```bash
curl -X POST http://localhost:5050/subscriptions?topic=cache/a/wis2/%2B/data/core/weather/%23&target=example_data
```

The list of active subscriptions should be returned as a JSON object.

### Deleting subscriptions
Subscriptions are deleted similarly via a DELETE request to the `./subscriptions` endpoint, with the following form:
```bash
curl -X DELETE http://<flask-host>:<flask-port>/delete?topic=<topic-name>
```

For example:
```bash
curl -X DELETE http://localhost:5050/subscriptions?topic=cache/a/wis2/%2B/data/core/weather/%23
```

The list of active subscriptions should be returned as a JSON object.
### Listing subscriptions
Subscriptions are listed via a GET request to `./subscriptions`:

```bash
curl http://<flask-host>:<flask-port>/subscriptions
```

For example:
```bash
curl http://localhost:5050/subscriptions
```

The list of active subscriptions should be returned as a JSON object.

### Viewing download metrics
Prometheus metrics for the downloader are found via a GET request to `./metrics`, e.g.:

```bash
curl http://<flask-host>:<flask-port>/metrics
```

## Bugs and Issues

All bugs, enhancements and issues are managed on [GitHub](https://github.com/wmo-im/wis2-downloader/issues).

## Contact

* [Rory Burke](https://github.com/RoryPTB)
* [David Berry](https://github.com/david-i-berry)
