ARG GRAFANA_VERSION
FROM grafana/grafana-oss:${GRAFANA_VERSION}

USER root
RUN apk del --no-cache --no-network curl musl-utils
USER "$GF_UID"

HEALTHCHECK CMD wget -q --spider localhost:3000/api/health || exit 1

COPY grafana.ini /etc/grafana/
