# The WIS2 Downloader
### The backend tool for subscribing to the latest data on the WIS2 network.

<a href="https://github.com/wmo-im/wis2-downloader/blob/main/LICENSE" alt="License" ><img src="https://img.shields.io/badge/License-Apache_2.0-blue"></img></a>

The WIS2 Downloader is a Flask-based Python application that allows you to connect to a WIS2 Global Broker, manage subscriptions to topic hierarchies, and configure their associated download directories.

**Note**: This repository does *not* contain the desktop application GUI that can be used to aid maintenance of subscriptions and explore Global Discovery Catalogues. <a href="https://github.com/wmo-im/wis2-downloader-gui">The WIS2 Downloader GUI can be found here.</a>

## Features

- **Dynamic Subscription Management**: Quickly add or remove subscriptions ad hoc without needing to restart the service or change configuration files.
- **Monitor Download Statistics**: Access the Prometheus metrics through the `/metrics` endpoint, ideal for <a href="https://prometheus.io/docs/visualization/grafana/">Grafana visualization</a>.
- **Multi-Threading Support**: Configure the number of download workers for more efficient data downloading.

## Demo
![backend-demo](https://github.com/wmo-im/wis2-downloader/assets/47696929/f9eb9eb3-07bd-49df-9714-61d952000f2e)

*The GET requests are demonstrated here using <a href="https://www.postman.com/">Postman</a>, but the terminal or your browser will suffice too.*

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
    "broker_url": "replace with url of the global broker, e.g. globalbroker.meteo.fr",
    "broker_port": "replace with the port to use on the global broker, e.g. 443",
    "username": "username to use on the global broker, default everyone",
    "password": "password to use on the global broker, default everyone",
    "protocol": "transport protocol to use, either tcp or websockets",
    "topics": {"initial topic 1": "associated download folder", ...},
    "download_dir": "default base download directory",
    "flask_host": "127.0.0.1",
    "flask_port": 8080,
    "download_workers": 1,
    "save_logs": false,
    "log_dir": "default base directory for logs to be saved"
}
```

This will be used when starting the WIS2 Downloader service.

### 3. Running

In your terminal, run:

```
wis2downloader --config <path to configuration file>
```

The Flask application should now be running. If you need to stop the application, you can do so in the terminal with `Ctrl+C`.

## Maintaining and Monitoring Subscriptions

### Adding subscriptions
Subscriptions can be added via a GET request to the `./add` endpoint on the Flask app, with the following form:

```bash
curl http://<flask-host>:<flask-port>/add?topic=<topic-name>&target=<download-directory>
```

- `topic` specifies the topic to subscribe to. *Special characters (+, #) must be URL encoded, i.e. `+` = `%2B`, `#` = `%23`.*
- `target` specifies the directory to save the downloads to, relative to `download_dir` from `config.json`. *If this is not provided, the directory will default to that of the topic hierarchy.*

For example:
```bash
curl http://localhost:8080/add?topic=cache/a/wis2/%2B/data/core/weather/%23&target=example_data
```

The list of active subscriptions should be returned as a JSON object.

### Deleting subscriptions
Subscriptions are deleted similarly via a GET request to the `./delete` endpoint, with the following form:
```bash
curl http://<flask-host>:<flask-port>/delete?topic=<topic-name>
```

For example:
```bash
curl http://localhost:8080/delete?topic=cache/a/wis2/%2B/data/core/weather/%23
```

The list of active subscriptions should be returned as a JSON object.
### Listing subscriptions
Subscriptions are listed via a GET request to `./list`:

```bash
curl http://<flask-host>:<flask-port>/list
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
