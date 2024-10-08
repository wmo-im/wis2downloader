FROM python:3.12-slim-bookworm
ARG USER_ID=12135

SHELL ["/bin/bash", "-c"]
# default ENV / config
ENV DOWNLOAD_BROKER_HOST "globalbroker.meteo.fr"
ENV DOWNLOAD_BROKER_PORT 443
ENV DOWNLOAD_BROKER_USERNAME "everyone"
ENV DOWNLOAD_BROKER_PASSWORD "everyone"
ENV DOWNLOAD_BROKER_TRANSPORT "websockets"
ENV DOWNLOAD_DIR "/home/wis2downloader/app/data/downloads"
ENV DOWNLOAD_MIN_FREE_SPACE_GB 1
ENV DOWNLOAD_RETENTION_PERIOD_HOURS 24
ENV DOWNLOAD_VALIDATE_TOPICS "false"
ENV DOWNLOAD_WORKERS 8
ENV LOG_PATH "/home/wis2downloader/app/logs"
ENV WIS2DOWNLOADER_CONFIG "/home/wis2downloader/app/config/config.json"


# Update, upgrade packages and install / clean up
RUN apt-get update && \
    apt-get upgrade && \
    apt-get install -y gettext-base=0.21-12 curl=7.88.1-10+deb12u6 cron=3.0pl1-162 git=1:2.39.2-1.1 && \
    rm -rf /var/lib/apt/lists/*

# Now setup python env and default user
RUN useradd -l -u "$USER_ID" wis2downloader

USER wis2downloader
WORKDIR /home/wis2downloader

USER wis2downloader

RUN python3.12 -m venv /home/wis2downloader/.venv && \
    echo "source /home/wis2downloader/.venv/bin/activate" >> .bashrc && \
    echo "" >> .bashrc

# install python dependencies
RUN source /home/wis2downloader/.venv/bin/activate && \
    python -m pip install --no-cache-dir gunicorn==23.0.0 requests==2.32.3 build==1.2.1 && \
    python -m pip install --no-cache-dir pyopenssl==24.2.1 --upgrade

USER root
# Now copy files
COPY . /home/wis2downloader/tmp
COPY ./docker/config/. /home/wis2downloader/app/config
COPY ./docker/entrypoint.sh /home/wis2downloader/app/entrypoint.sh
COPY ./docker/clean_downloads.cron /home/wis2downloader/app/clean_downloads.cron
COPY ./docker/clean_downloads.py /home/wis2downloader/app/clean_downloads.py

# set ownership / permisssions
RUN chown -R wis2downloader /home/wis2downloader/tmp && \
    chown -R wis2downloader /home/wis2downloader/app && \
    chmod +x /home/wis2downloader/app/entrypoint.sh && \
    chmod 600 /home/wis2downloader/app/clean_downloads.py && \
    chmod 600 /home/wis2downloader/app/clean_downloads.cron

USER wis2downloader
WORKDIR /home/wis2downloader/tmp
RUN source /home/wis2downloader/.venv/bin/activate && \
    python -m pip install --no-cache-dir .
# clean up \
WORKDIR /home/wis2downloader/
RUN rm -R /home/wis2downloader/tmp

# Set the working directory to /app
WORKDIR /home/wis2downloader
RUN crontab ./app/clean_downloads.cron

# Add healthcheck
HEALTHCHECK --interval=1m --timeout=3s \
  CMD curl -f http://localhost:5000/subscriptions || exit 1

ENTRYPOINT [ "/home/wis2downloader/app/entrypoint.sh" ]
# Run wis2downloader when the container launches
CMD ["/bin/bash", "-c", "gunicorn --bind 0.0.0.0:5000 --workers 1 wis2downloader.app:app"]