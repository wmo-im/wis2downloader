# The WIS2 Downloader
### The backend tool for subscribing to the latest data on the WIS2 network.

<div align="center">

  <a href="https://github.com/wmo-im/wis2downloader/blob/main/LICENSE" alt="License" ><img src="https://img.shields.io/badge/License-Apache_2.0-blue" alt="License Badge"></img></a>
  [![Super-Linter](https://github.com/wmo-im/wis2downloader/actions/workflows/test-code-quality.yml/badge.svg)](https://github.com/marketplace/actions/super-linter)
  ![Unit-Tests](https://github.com/wmo-im/wis2downloader/actions/workflows/unit-tests.yml/badge.svg)
  ![Update-GHCR](https://github.com/wmo-im/capvalidator/actions/workflows/update-ghcr.yml/badge.svg)

</div>

The WIS2 Downloader is a Flask-based Python application that allows you to connect to a WIS2 Global Broker, manage subscriptions to topic hierarchies, and configure their associated download directories.

## Features

- **Dynamic Subscription Management**: Quickly add or remove subscriptions ad hoc without needing to restart the service or change configuration files.
- **Monitor Download Statistics**: Access the Prometheus metrics through the `/metrics` endpoint, ideal for <a href="https://prometheus.io/docs/visualization/grafana/">Grafana visualization</a>.
- **Multi-Threading Support**: Configure the number of download workers for more efficient data downloading.

## Getting Started

### 1. Installation

__NOTE__: The downloader has not yet been uploaded to PyPI and needs to be installed directly from GitHub:

```bash
pip install https://github.com/wmo-im/wis2downloader/archive/main.zip
```

This will install the version from the main development branch.

### 2. Configuration

Create a file `config.json` in your local directory that conforms with the following schema:

```yaml
schema:
  type: object
  properties:
    base_url:
      type: string
      description:
        Base URL for the wis2downloader service. 
      example: http://localhost:5050
    broker_hostname:
      type: string
      description: The hostname of the global broker to subscribe to.
      example: globalbroker.meteo.fr
    broker_password:
      type: string
      description: The password to use when connecting to the specified global broker.      
      example: everyone
    broker_port:
      type: number
      description: The port the global broker is using for the specified protocol.
      example: 443
    broker_protocol:
      type: string
      description: The protocol (websockets or tcp) to use when connecting to the global broker.
      example: websockets
    broker_username:
      type: string
      description: The username to use when connecting to the global broker.
      example: everyone
    download_workers:
      type: number
      description: The number of download worker threads to spawn.
      example: 1
    download_dir:
      type: string
      description: The path to download data to on the server/computer running the wis2downloader.
      example: ./downloads
    flask_host:
      type: string
      description: Network interface on which flask should listen when run in dev mode.
      example: 0.0.0.0
    flask_port:
      type: number
      description: The port on which flask should listen when run in dev mode.
      example: 5050
    log_level:
      type: string
      description: Log level to use
      example: DEBUG
    log_path:
      type: string
      description: Path to write log files to.
      example: ./logs
    min_free_space:
      type: number
      description: 
        Minimum free space (GB) to leave on download volume / disk after download.
        Files exceeding limit will not be saved.
      example: 10
    save_logs:
      type: boolean
      description: Write log files to disk (true) or stdout (false)
      example: false
    mqtt_session_info:
      type: string
      description: 
        File to save session information (active subscriptions and MQTT client id) to. 
        Used to persist subscriptions on restart.
      example: mqtt_session.json
    validate_topics:
      type: boolean
      description: Whether to validate the specified topic against the published WIS2 topic hierarchy.
      example: true
```

An example is given below:

```json
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
```

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

*Windows (PowersShell)*
```
$env:WIS2DOWNLOADER_CONFIG = <path_to_your_config_file>
```

2. Start the downloader

*Dev mode (Windows and Linux)*

```bash
wis2downloader
```

*Using gunicorn (Linux only)*
```
gunicorn --bind 0.0.0.0:5050 -w 1 wis2downloader.app:app
```

**Note**: Only one worker is supported due to the downloader spawning additional threads and persistence of MQTT
connections.

The Flask application should now be running. If you need to stop the application, you can do so in the terminal 
with `Ctrl+C`.

## Maintaining and Monitoring Subscriptions

The API defintion of the downloader can be found at the `/swagger` endpoint, when run locally see
http://localhost:5050/swagger. this includes the ability to try out the different end points.

### Adding subscriptions
Subscriptions can be added via a POST request to the `/subscriptions` endpoint.
The request body should be JSON-encoded and adhere to the following schema: 

```yaml
schema:
  type: object
  properties:
    topic:
      type: string
      description: The WIS2 topic to subscribe to
      example: cache/a/wis2/+/data/core/weather/surface-based-observations/#
    target:
      type: string
      description: Sub directory to save data to
      example: surface-obs
  required:
    - topic
```

In this example all notifications published to the `surface-based-observations` topic from any WIS2 centre will be 
subscribed to, with the downloaded data written to the `surface-obs` subdirectory of the `download_dir`. 

Notes:
1. If the `target` is not specified it will default to the topic the data are published on.
1. The `+` wild card is used to specify any match at a single level, matching as WIS2 centre in the above example.
1. The `#` wild card matches any topic at or below the level it occurs. In the above example any topic published below 
cache/a/wis2/+/data/core/weather/surface-based-observations will be matched.

#### Example CURL command:

```bash
curl -X 'POST' \
  'http://127.0.0.1:5050/subscriptions' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
      "topic": "cache/a/wis2/+/data/core/weather/surface-based-observations/#",
      "target": "surface-obs"
  }'
```

### Deleting subscriptions
Subscriptions are deleted via a DELETE request to the `/subscriptions/{topic}` endpoint where `{topic}` is the topic 
to unsubscribe from. 

#### Example CURL command

```bash
curl -X DELETE http://localhost:5050/subscriptions/cache/a/wis2/%2B/data/core/weather/%23
```

This cancels the `cache/a/wis2/+/data/core/weather/#` subscription. Note the need to url encode the `+` (`%2B`) 
and `#` (`%23`) symbols.

### Listing subscriptions
Current subscriptions can listed via a GET request to `/subscriptions` end point.

#### Example CURL command

```bash
curl http://localhost:5050/subscriptions
```

The list of active subscriptions should be returned as a JSON object.

### Viewing download metrics
Prometheus metrics for the downloader are found via a GET request to the `/metrics` end point.

#### Example CURL command

```bash
curl http://localhost:5050/metrics
```

## Bugs and Issues

All bugs, enhancements and issues are managed on [GitHub](https://github.com/wmo-im/wis2downloader/issues).

## Contact

* [Rory Burke](https://github.com/RoryPTB)
* [David Berry](https://github.com/david-i-berry)
