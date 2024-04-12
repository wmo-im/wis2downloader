# wis2-downloader

Note: the previous version of the downloader, including the frontend, has been moved to: https://github.com/wmo-im/wis2-downloader-gui

## Description

Flask based Python application to subscribe and download data from the WIS2.0 network.

## Usage

### Installation

```bash
pip install https://github.com/wmo-im/wis2-downloader/archive/main.zip
```

### Configuration

Configuration is set via a `config.json` file with the following contents

```json
{
    "broker_url": "replace with url of the global broker, e.g. globalbroker.meteo.fr",
    "broker_port": "replace with the port to use on the global broker, e.g. 443",
    "username": "username to use on the global broker, default everyone",
    "password": "password to use on the global broker, default everyone",
    "protocol": "transport protocol to use, either tcp or websockets",
    "topics": {"initial topic 1": "associated download folder", ...},
    "download_dir": "default base download directory",
    "flask_host": "127.0.0.1",
    "flask_port": 5000,
    "download_workers": 1,
    "save_logs": false,
    "log_dir": "default base directory for logs to be saved"
}
```

### Running

```
wis2downloader --config <path to configuration file>
```

### Adding subscriptions
Subscriptions can be added via a GET request to the `./add` endpoint on the flask app, e.g.:

```bash
curl http://localhost:8080/add?topic=cache/a/wis2/%2B/data/core/weather/%23&target=example_data
```

- `topic` specifies the topic to subscribe to. Special characters (+, #) need to be url encoded.
`+` = `%2B`, `#` = `%23`.
- `target` specifies the directory to save the downloads to, relative to `download_dir` from `config.json`. Defaults to the topic is missing. 

The list of active subscriptions should be returned as a json object.

### Deleting subscriptions
Subscriptions are deleted via a GET request to `./delete`, e.g.:

```bash
curl http://localhost:8080/delete?topic=cache/a/wis2/%2B/data/core/weather/%23
```

The list of active subscriptions should be returned as a json object.
### Listing subscriptions
Subscriptions are listed via a GET request to `./list`, e.g.:

```bash
curl http://localhost:8080/list
```

The list of active subscriptions should be returned as a json object.

### Viewing download metrics
Prometheus metrics for the downloader are found via a GET request to `./metrics`, e.g.:

```bash
curl http://localhost:8080/metrics
```

usage: wis2downloader [-h] [--config CONFIG]

WIS2 Downloader app configuration

options:
  -h, --help       show this help message and exit
  --config CONFIG  Path to the Flask app configuration file