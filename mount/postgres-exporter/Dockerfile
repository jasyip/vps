ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add gcc mold libc-dev fortify-headers

WORKDIR /go/src/exporter
ARG POSTGRES_EXPORTER_VERSION

RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    wget -qO - "https://github.com/prometheus-community/postgres_exporter/archive/refs/tags/${POSTGRES_EXPORTER_VERSION}.tar.gz" | \
        tar -xzof - --strip-components 1 && \
    cd cmd/postgres_exporter && \
    exec go mod download

ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec mold -run go build -ldflags="-s -w -linkmode=external -extldflags=-static-pie" -trimpath -buildmode=pie -o /postgres-exporter ./cmd/postgres_exporter


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
