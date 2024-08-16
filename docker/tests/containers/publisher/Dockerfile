FROM python:3.11-slim-bookworm

# Update / upgrade
RUN apt-get update && \
    apt-get upgrade

# install python dependencies
RUN python -m pip install pywis-pubsub
COPY ./config /pywis-pubsub/config

CMD ["bash"]
