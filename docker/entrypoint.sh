#!/bin/bash

echo "START /entrypoint.sh"

set -e

# ensure cron is running
service cron start
service cron status

echo "END /entrypoint.sh"

# print the download_dir
echo "Download directory in container: $DOWNLOAD_DIR"
# print the retention period hours
echo "Retention period in hours: $RETENTION_PERIOD_HOURS"

# ensure DOWNLOAD_DIR exists
if [ ! -d $DOWNLOAD_DIR ]; then
    echo "Creating download directory: $DOWNLOAD_DIR"
    mkdir -p $DOWNLOAD_DIR
fi
envsubst < config_template.json > config.json

# print the config
echo "Config:"
cat /app/config.json

exec "$@"
