#checkov:skip=CKV_DOCKER_2:No healthcheck, dockerfile only used in testing
#checkov:skip=CKV_DOCKER_3
FROM eclipse-mosquitto:2.0.18
COPY entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

COPY ./config /mosquitto/config

RUN chown mosquitto:mosquitto /mosquitto/config/password.txt && \
    chmod 700 /mosquitto/config/password.txt

RUN chown mosquitto:mosquitto /mosquitto/config/acl.conf && \
    chmod 700 /mosquitto/config/acl.conf

RUN chown mosquitto:mosquitto /mosquitto/config/mosquitto.conf && \
    chmod 700 /mosquitto/config/mosquitto.conf

