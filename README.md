# wis2-downloader

Note: previous version of the downloader, including frontend, has been moved to: https://github.com/wmo-im/wis2-downloader-gui

## Description

Flask based python application to subscribe and download data from the WIS2.0.

## Usage

### Isntallation

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
    "topics": {},
    "download_dir": "default base download directory",
    "flask_host": "127.0.0.1",
    "flask_port": 5000,
    "download_workers": 1
}
```

### Running

```
wis2downloader --config config.json
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