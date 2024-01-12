ARG PROMETHEUS_VERSION
FROM prom/prometheus:${PROMETHEUS_VERSION}

HEALTHCHECK CMD wget -q --spider localhost:9090/-/healthy || exit 1

CMD        [ "--config.file=/etc/prometheus/prometheus.yml", \
             "--storage.tsdb.path=/prometheus", \
             "--web.console.libraries=/usr/share/prometheus/console_libraries", \
             "--web.console.templates=/usr/share/prometheus/consoles", \
             "--enable-feature=memory-snapshot-on-shutdown" ]

COPY *.yml /etc/prometheus/
