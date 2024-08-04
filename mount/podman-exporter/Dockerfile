ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder

ARG PODMAN_EXPORTER_VERSION
WORKDIR /go/src/exporter

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    wget -qO - "https://github.com/containers/prometheus-podman-exporter/archive/refs/tags/${PODMAN_EXPORTER_VERSION}.tar.gz" | \
        tar -xzf - --strip-components 1 && \
    CGO_ENABLED=0 go build -buildmode=pie -trimpath -ldflags="-s -w" --tags containers_image_openpgp -o /podman-exporter . && \
    rm -rf *


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
