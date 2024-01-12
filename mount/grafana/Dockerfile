ARG GRAFANA_VERSION
FROM grafana/grafana-oss:${GRAFANA_VERSION}

ARG GF_UID="472"
USER root
RUN apk del --no-cache --no-network curl libc-utils musl-utils
USER "$GF_UID"

HEALTHCHECK CMD wget -q --spider localhost:3000/api/health || exit 1

COPY grafana.ini /etc/grafana/
