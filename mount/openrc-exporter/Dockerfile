ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder

SHELL ["/bin/sh", "-eCuxo", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add ccache meson gcc mold pkgconf libc-dev fortify-headers linux-headers linux-pam-dev; \
    find /usr/lib/ccache/bin -type l -exec ln -s \{\} /usr/local/bin \;

COPY ccache.conf /etc/

WORKDIR /usr/local/src/openrc
ARG OPENRC_VERSION
ARG CFLAGS
ARG LDFLAGS
RUN wget -O - "https://github.com/OpenRC/openrc/archive/refs/tags/${OPENRC_VERSION}.tar.gz" | \
      tar -xzo --strip-components 1; \
    meson setup build \
      -Dprefix=/usr/local \
      -Dbuildtype=release \
      -Ddefault_library=static \
      -Doptimization=plain \
      -Db_colorout=always \
      -Dbash-completions=false \
      -Dzsh-completions=false

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    meson compile -C build; \
    meson install -C build --tags devel

WORKDIR /go/src/exporter
ARG OPENRC_EXPORTER_VERSION

RUN wget -O - "https://git.sr.ht/~tomleb/openrc-exporter/archive/${OPENRC_EXPORTER_VERSION}.tar.gz" | \
        tar -xzof - --strip-components 1 $(printf "openrc-exporter-${OPENRC_EXPORTER_VERSION}/%s " cmd pkg go.mod go.sum)

RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    cd cmd/openrc-exporter; \
    exec go mod download


RUN --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    go build -ldflags="-s -w -linkmode=external -extldflags=-static-pie" -trimpath -buildmode=pie -o /openrc-exporter ./cmd/openrc-exporter

FROM scratch

COPY --from=builder /openrc-exporter /

COPY <<EOF /etc/passwd
nobody:x:65534:65534:nobody:/:/sbin/nologin
EOF

USER nobody

VOLUME /run/openrc /etc/conf.d /etc/init.d
ENTRYPOINT ["/openrc-exporter"]
EXPOSE 9816
