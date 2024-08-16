FROM eclipse-mosquitto
COPY entrypoint.sh /docker-entrypoint.sh
COPY ./config /mosquitto/config

RUN chown mosquitto:mosquitto /mosquitto/config/password.txt && \
    chmod 700 /mosquitto/config/password.txt

RUN chown mosquitto:mosquitto /mosquitto/config/acl.conf && \
    chmod 700 /mosquitto/config/acl.conf

RUN chown mosquitto:mosquitto /mosquitto/config/mosquitto.conf && \
    chmod 700 /mosquitto/config/mosquitto.conf

