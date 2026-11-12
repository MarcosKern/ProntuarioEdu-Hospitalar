FROM quay.io/keycloak/keycloak:26.8.2@sha256:c68e286cacd87b942ac1939a0a1481461109d6acd3a57dc496969a319a76bbf0

ENV KC_DB=mysql KC_HEALTH_ENABLED=true
RUN /opt/keycloak/bin/kc.sh build
RUN mkdir -p /opt/keycloak/data/import
COPY --chmod=0555 docker/keycloak/healthcheck.sh /opt/keycloak/bin/prontuario-healthcheck
CMD ["start", "--optimized", "--import-realm"]
