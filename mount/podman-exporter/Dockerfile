ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder


RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add gcc mold libc-dev fortify-headers linux-headers btrfs-progs-dev

WORKDIR /go/src/exporter
ARG PODMAN_EXPORTER_VERSION

RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    apk add gcc mold libc-dev fortify-headers linux-headers btrfs-progs-dev && \
    wget -qO - "https://github.com/containers/prometheus-podman-exporter/archive/refs/tags/${PODMAN_EXPORTER_VERSION}.tar.gz" | \
        tar -xzof - --strip-components 1 && \
    exec go mod download

ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec mold -run go build -ldflags="-s -w -linkmode=external -extldflags=-static-pie" -trimpath -buildmode=pie  --tags containers_image_openpgp -o /podman-exporter .


FROM scratch

COPY --from=builder /podman-exporter /

COPY <<EOF /etc/passwd
nobody:x:65534:65534:nobody:/:/sbin/nologin
EOF

USER nobody

VOLUME /run/podman
ENTRYPOINT ["/podman-exporter"]
CMD ["-n", "-s", "-v"]
ENV XDG_CONFIG_HOME=/

EXPOSE 9882
