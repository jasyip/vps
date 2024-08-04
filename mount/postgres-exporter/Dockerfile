ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder

ARG POSTGRES_EXPORTER_VERSION
WORKDIR /go/src/exporter
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    wget -qO - "https://github.com/prometheus-community/postgres_exporter/archive/refs/tags/${POSTGRES_EXPORTER_VERSION}.tar.gz" | \
        tar -xzf - --strip-components 1 && \
    CGO_ENABLED=0 go build -buildmode=pie -trimpath -ldflags="-s -w" -o /postgres-exporter ./cmd/postgres_exporter && \
    rm -rf *


FROM scratch

COPY --from=builder /postgres-exporter /

COPY <<EOF /etc/passwd
nobody:x:65534:65534:nobody:/:/sbin/nologin
EOF

USER nobody

COPY postgres_exporter.yml ./

ENTRYPOINT ["/postgres-exporter"]
VOLUME ["/run/postgresql"]
EXPOSE 9187
