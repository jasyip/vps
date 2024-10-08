ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder

SHELL ["/bin/sh", "-eCuxo", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add gcc mold libc-dev fortify-headers

WORKDIR /go/src/exporter
ARG POSTGRES_EXPORTER_VERSION

RUN wget -O - "https://github.com/prometheus-community/postgres_exporter/archive/refs/tags/v${POSTGRES_EXPORTER_VERSION}.tar.gz" | \
        tar -xzo --strip-components 1 $(printf "postgres_exporter-${POSTGRES_EXPORTER_VERSION}/%s " cmd collector config go.mod go.sum)

RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    cd cmd/postgres_exporter; \
    exec go mod download

ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec go build -ldflags="-s -w -linkmode=external -extldflags=-static-pie" -trimpath -buildmode=pie -o /postgres-exporter ./cmd/postgres_exporter


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
