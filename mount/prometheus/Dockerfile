ARG GO_BUILDER_VERSION
ARG DISTROLESS_SUFFIX
FROM golang:${GO_BUILDER_VERSION} AS builder-base

SHELL ["/bin/sh", "-eCuxo", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add gpg gpg-agent ccache gcc make mold libc-dev fortify-headers patch; \
    find /usr/lib/ccache/bin -type l -exec ln -s \{\} /usr/local/bin \;

COPY ccache.conf /etc/

FROM builder-base AS builder-other

ARG BUSYBOX_VERSION
ARG CFLAGS
ARG LDFLAGS

WORKDIR /usr/local/src/busybox
RUN --mount=target=busybox-setup.sh,source=busybox-setup.sh \
    --mount=target=busybox-config.sh,source=busybox-config.sh \
    . busybox-setup.sh

RUN --mount=type=cache,target=/var/ccache \
    --mount=target=wget-wrap.c,source=wget-wrap.c \
    --network=none \
    mold -run make -j$(nproc) busybox; \
    make install; \
    exec cc $CFLAGS $LDFLAGS -s -static-pie -o /wget-wrap wget-wrap.c

FROM builder-base AS builder

ARG PROMETHEUS_VERSION
WORKDIR /usr/local/src/prometheus

RUN --mount=target=/busybox-compat.patch,source=busybox-compat.patch \
    --mount=target=/pre-built.patch,source=pre-built.patch \
    --mount=target=/static-pie.patch,source=static-pie.patch \
    wget -O - "https://github.com/prometheus/prometheus/archive/refs/tags/v${PROMETHEUS_VERSION}.tar.gz" | \
      tar -xzof - --strip-components 1; \
    BASE_URL="https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}"; \
    wget -O - "${BASE_URL}/prometheus-web-ui-${PROMETHEUS_VERSION}.tar.gz" | \
      tee >(tar -C web/ui -xzof -) | \
          sha256sum -c <(wget -O - "$BASE_URL/sha256sums.txt" | \
                           awk '$2 ~ /^prometheus-web-ui.*\.tar\.gz$/ {print $1 " -"}'); \
    echo /*.patch | xargs -n 1 patch -p0 -i && \
    exec make promu

RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    exec go mod download

ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" exec make build


FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

USER root

COPY --from=builder-other /busybox/bin/wget /wget-wrap /usr/sbin/
COPY --from=builder /usr/local/src/prometheus/prometheus /usr/local/src/prometheus/promtool /usr/bin/
COPY --from=builder usr/local/src/prometheus/console_libraries /usr/share/prometheus/console_libraries
COPY --from=builder usr/local/src/prometheus/consoles /usr/share/prometheus/consoles


RUN --mount=target=/lib/ld-musl-x86_64.so.1,source=/lib/ld-musl-x86_64.so.1,from=builder \
    --mount=target=/usr/sbin/busybox,source=/bin/busybox,from=builder \
     ["busybox", "sh", "-eCuxo", "pipefail", "-c", \
      "busybox ln -s /usr/share/prometheus/console_libraries /usr/share/prometheus/consoles /etc/prometheus; \
      busybox mkdir /prometheus; \
      busybox chown nonroot:nonroot /prometheus; \
      " \
     ]

COPY *.yml /etc/prometheus/

USER nonroot
EXPOSE 9090

VOLUME ["/prometheus"]
ENTRYPOINT ["prometheus"]

CMD        [ "--config.file=/etc/prometheus/prometheus.yml", \
             "--storage.tsdb.path=/prometheus", \
             "--web.console.libraries=/usr/share/prometheus/console_libraries", \
             "--web.console.templates=/usr/share/prometheus/consoles", \
             "--enable-feature=memory-snapshot-on-shutdown" ]

HEALTHCHECK CMD ["wget-wrap", "-q", "--spider", "localhost:9090/-/healthy"]
