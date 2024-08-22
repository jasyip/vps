# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: GPL-2.0-only

ARG GO_BUILDER_VERSION
ARG DISTROLESS_SUFFIX
FROM golang:${GO_BUILDER_VERSION} AS builder-base

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add gcc make mold libc-dev fortify-headers

FROM builder-base AS builder-other

ARG BUSYBOX_VERSION
ARG CFLAGS
ARG LDFLAGS

WORKDIR /usr/local/src/busybox
RUN wget -qO - "https://busybox.net/downloads/busybox-${BUSYBOX_VERSION}.tar.bz2" | \
      tar -xjof - --strip-components 1 && \
    sed -i 's/\(^\|[^[:alnum:]_-]\)-static\($\|[^[:alnum:]=_-]\)/\1-static-pie\2/' Makefile.flags && \
    make allnoconfig && \
    sleep 1 && \
    sed -i 's/^.*\(CONFIG_\(STATIC\|INSTALL_NO_USR\|DESKTOP\|LONG_OPTS\|SH_IS_NONE\|WGET\|FEATURE_WGET_LONG_OPTIONS\|FEATURE_WGET_TIMEOUT\)\)[ =].*$/\1=y/' .config && \
    sed -i 's/^.*\(CONFIG_SH_IS_ASH\)[ =].*$/\1=n/' .config && \
    sed -i 's%^.*\(CONFIG_PREFIX\)[ =].*$%\1="/busybox"%' .config && \
    sed -i "s%^.*\(CONFIG_EXTRA_CFLAGS\)[ =].*$%\1=\"$CFLAGS\"%" .config && \
    sed -i "s%^.*\(CONFIG_EXTRA_LDFLAGS\)[ =].*$%\1=\"$LDFLAGS\"%" .config

RUN --mount=target=healthcheck.c,source=healthcheck.c \
    mold -run make busybox && make install && \
    exec cc $CFLAGS -s -static-pie -o /healthcheck healthcheck.c


FROM builder-base AS builder

WORKDIR /usr/local/src/authelia

ARG AUTHELIA_VERSION
RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    wget -qO - "https://github.com/authelia/authelia/archive/refs/tags/v${AUTHELIA_VERSION}.tar.gz" | \
      tar -xzof - --strip-components 1 $(printf "authelia-${AUTHELIA_VERSION}/%s " api cmd internal go.mod go.sum) && \
    mv api internal/server/public_html/api && \
    wget -qO - "https://github.com/authelia/authelia/releases/download/v${AUTHELIA_VERSION}/authelia-v${AUTHELIA_VERSION}-public_html.tar.gz" | \
      tar -C internal/server -xzof - && \
    exec go mod download

ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_CXXFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    go build -buildmode=pie -trimpath -ldflags="-s -w -linkmode=external -extldflags=-static-pie" ./cmd/authelia && \
    mkdir -p /var/lib/authelia/notifications /app && \
    chown -R 65532:65532 /var/lib/authelia


FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

USER root

COPY --from=builder /usr/local/src/authelia/authelia /app/
COPY --from=builder-other /busybox/bin/wget /usr/sbin/
COPY --from=builder-other /healthcheck /app/
COPY --from=builder --chown=nonroot:nonroot /app /app
COPY --from=builder --chown=nonroot:nonroot /var/lib/authelia /var/lib/authelia

COPY ./healthcheck.env /app/.healthcheck.env
COPY ./configuration.yml /etc/authelia.yml

USER nonroot

ENTRYPOINT ["/app/authelia"]
EXPOSE 9959
ENV X_AUTHELIA_CONFIG="/etc/authelia.yml"
ENV X_AUTHELIA_HEALTHCHECK=1
HEALTHCHECK --interval=30s --timeout=3s --start-period=1m CMD /app/healthcheck
VOLUME /var/lib/authelia/notifications
