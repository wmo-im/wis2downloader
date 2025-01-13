#checkov:skip=CKV_DOCKER_2:No healthcheck, dockerfile only used in testing
#checkov:skip=CKV_DOCKER_3
FROM python:3.11-slim-bookworm

# Update / upgrade
RUN apt-get update && \
    apt-get upgrade -y

# install python dependencies
RUN python -m pip install --no-cache-dir pywis-pubsub==0.7.2
COPY ./config /pywis-pubsub/config

CMD ["bash"]
