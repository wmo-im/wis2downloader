FROM python:3.12-slim-bookworm

# default ENV / config
ENV DOWNLOAD_DIR /app/data/downloads
ENV DOWNLOAD_BROKER_HOST "globalbroker.meteo.fr"
ENV DOWNLOAD_BROKER_PORT 443
ENV DOWNLOAD_BROKER_USERNAME "everyone"
ENV DOWNLOAD_BROKER_PASSWORD "everyone"
ENV DOWNLOAD_BROKER_TRANSPORT "websockets"
ENV DOWNLOAD_WORKERS 8
ENV DOWNLOAD_MIN_FREE_SPACE_GB 1
ENV DOWNLOAD_VALIDATE_TOPICS "false"
ENV LOG_PATH /app/logs
ENV WIS2DOWNLOADER_CONFIG "/app/config/config.json"

# Update / upgrade
RUN apt-get update && \
    apt-get upgrade && \
    apt-get install -y gettext-base

    # install python dependencies
RUN python -m pip install gunicorn requests wis2downloader

# upgrade certs
RUN python -m pip install pyopenssl --upgrade

# copy all the code to the Docker image
COPY config/. /app/config
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the working directory to /app
WORKDIR /app/config

ENTRYPOINT [ "/entrypoint.sh" ]

# Run wis2downloader when the container launches
CMD ["gunicorn","--bind","0.0.0.0:5000","--pythonpath","/usr/local/lib/python3.12/site-packages/","--workers", "1", "wis2downloader.app:app"]