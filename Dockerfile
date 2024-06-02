# Use an official Python runtime as a parent image
FROM python:3.9-slim

EXPOSE 5000

# define config variables
ENV DOWNLOAD_DIR /app/downloads
ENV RETENTION_PERIOD_HOURS 24
ENV BROKER_URL "globalbroker.meteo.fr"
ENV BROKER_PORT 443
ENV BROKER_USERNAME "everyone"
ENV BROKER_PASSWORD "everyone"
ENV BROKER_PROTOCOL "websockets"
ENV FLASK_HOST "0.0.0.0"
ENV FLASK_PORT 5000
ENV DOWNLOAD_WORKERS 8
ENV SAVE_LOGS false
ENV LOGS_DIR /app/logs

# update pyopenssl and pin requests and urllib3 to avoid SSL error
RUN pip install pyopenssl --upgrade && pip install requests==2.26.0 urllib3==1.26.0
# install cron and envsubst
RUN apt-get update && apt-get install -y cron gettext-base

# copy all
COPY . /app

# install the latest version of the package
RUN pip install wis2downloader

# Set the working directory to /app
WORKDIR /app

# Copy the clean-script to the Docker image
COPY ./docker/clean.py /app/clean.py

# add wis2box.cron to crontab
COPY ./docker/clean.cron /etc/cron.d/clean.cron

# set permissions for the cron job and install it
RUN chmod 0644 /etc/cron.d/clean.cron && crontab /etc/cron.d/clean.cron

# Copy the entrypoint script to the Docker image
COPY ./docker/entrypoint.sh /entrypoint.sh

# set permissions for the entrypoint script
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]

# Run wis2-downloader when the container launches
CMD ["wis2downloader","--config","/app/config.json"]