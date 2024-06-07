import json
import os
from pathlib import Path

def load_config(args=None):
    if args:
        config_file = args.config
    else:
        config_file = os.getenv('WIS2DOWNLOADER_CONFIG')
    config_file = Path(config_file)

    print(config_file)

    if config_file is None:
        raise RuntimeError("No configuration specified")

    with open(config_file) as fh:
        _config = json.load(fh)

    return _config
