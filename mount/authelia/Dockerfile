ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder-base

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add gcc make libc-dev mold

FROM builder-base AS builder-other

ARG BUSYBOX_VERSION
ARG CFLAGS="-O2 -march=native -pipe -D_FORTIFY_SOURCE=2 -ftrivial-auto-var-init=pattern -fstack-protector-strong -fstack-clash-protection -fcf-protection=full -flto -fPIE -pie"
ARG LDFLAGS="-Wl,-O1,--sort-common,-z,relro,-z,now"

WORKDIR /usr/local/src/busybox
RUN wget -qO - "https://busybox.net/downloads/busybox-${BUSYBOX_VERSION}.tar.bz2" | \
        tar -xkjf - --strip-components 1 && \
    make allnoconfig && \
    sleep 1 && \
    sed -i 's/^.*CONFIG_\(STATIC\|INSTALL_NO_USR\|DESKTOP\|LONG_OPTS\|SH_IS_NONE\|WGET\|FEATURE_WGET_LONG_OPTIONS\|FEATURE_WGET_TIMEOUT\|USE_PORTABLE_CODE\)[ =].*$/CONFIG_\1=y/' .config && \
    sed -i 's/^.*\(CONFIG_SH_IS_ASH\)[ =].*$/\1=n/' .config && \
    sed -i 's/^.*\(CONFIG_PREFIX\)[ =].*$/\1="\/busybox"/' .config && \
    sed -i "s/^.*\(CONFIG_EXTRA_CFLAGS\)[ =].*$/\1=\"$CFLAGS\"/" .config && \
    sed -i "s/^.*\(CONFIG_EXTRA_LDFLAGS\)[ =].*$/\1=\"$LDFLAGS\"/" .config

RUN --mount=target=healthcheck.c,source=healthcheck.c \
    mold -run make busybox && \
    mold -run make install && \
    exec cc $CFLAGS -s -static-pie -o /healthcheck healthcheck.c


FROM builder-base AS builder

WORKDIR /usr/local/src/authelia

ARG AUTHELIA_VERSION
RUN --mount=type=cache,target=/go/pkg/mod \
    wget -qO - "https://github.com/authelia/authelia/archive/refs/tags/v${AUTHELIA_VERSION}.tar.gz" | \
        tar -xzf - --strip-components 1 $(printf "authelia-${AUTHELIA_VERSION}/%s " api cmd internal go.mod go.sum) && \
    mv api internal/server/public_html/api && \
    wget -qO - "https://github.com/authelia/authelia/releases/download/v${AUTHELIA_VERSION}/authelia-v${AUTHELIA_VERSION}-public_html.tar.gz" | \
        tar -C internal/server -xzf - && \
    exec go mod download

ARG CFLAGS="-O2 -march=native -pipe -D_FORTIFY_SOURCE=2 -ftrivial-auto-var-init=pattern -fstack-protector-strong -fstack-clash-protection -fcf-protection=full -flto -fPIE -pie"
ARG LDFLAGS="-Wl,-O1,--sort-common,-z,relro,-z,now"

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_CXXFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    go build -buildmode=pie -trimpath -ldflags="-s -w -linkmode=external -extldflags=-static-pie" ./cmd/authelia && \
    mkdir -p /var/lib/authelia/notifications /app && \
    chown -R 65532:65532 /var/lib/authelia


ARG DISTROLESS_SUFFIX
FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

USER root

COPY --from=builder /usr/local/src/authelia/authelia /app/
COPY --from=builder-other /busybox/bin/wget /bin/
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
