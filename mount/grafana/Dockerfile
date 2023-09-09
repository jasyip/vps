ARG GRAFANA_VERSION
FROM grafana/grafana-oss:${GRAFANA_VERSION}

HEALTHCHECK CMD wget -q --spider localhost:3000/api/health || exit 1

COPY grafana.ini /etc/grafana/
