ARG POSTGRES_EXPORTER_VERSION
FROM prometheuscommunity/postgres-exporter:$POSTGRES_EXPORTER_VERSION

COPY postgres_exporter.yml ./

VOLUME /run/postgresql
