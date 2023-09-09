ARG PROMETHEUS_VERSION
FROM prom/prometheus:${PROMETHEUS_VERSION}

HEALTHCHECK CMD wget -q --spider localhost:9090/-/healthy || exit 1

COPY *.yml /etc/prometheus/
