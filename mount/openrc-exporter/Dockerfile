ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder

WORKDIR /go/src/exporter
ARG CFLAGS
ARG LDFLAGS
ARG OPENRC_EXPORTER_VERSION

RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add gcc mold libc-dev fortify-headers openrc-dev openrc-static && \
    wget -qO - "https://git.sr.ht/~tomleb/openrc-exporter/archive/${OPENRC_EXPORTER_VERSION}.tar.gz" | \
        tar -xzf - --strip-components 1 && \
    cd cmd/openrc-exporter && \
    exec go mod download

RUN --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build,sharing=private \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec mold -run go build -ldflags="-s -w -linkmode=external -extldflags=-static-pie" -trimpath -buildmode=pie -o /openrc-exporter ./cmd/openrc-exporter

FROM scratch

COPY --from=builder /openrc-exporter /

COPY <<EOF /etc/passwd
nobody:x:65534:65534:nobody:/:/sbin/nologin
EOF

USER nobody

VOLUME /run/openrc /etc/conf.d /etc/init.d
ENTRYPOINT ["/openrc-exporter"]
EXPOSE 9816
