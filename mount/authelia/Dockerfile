ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder-backend


WORKDIR /usr/local/src/busybox
RUN apk add --no-cache gcc make libc-dev && \
    wget -qO - "https://busybox.net/downloads/busybox-1.36.1.tar.bz2" | \
        tar -xkjf - --strip-components 1 && \
    make allnoconfig && \
    sleep 1 && \
    sed -i 's/^.*CONFIG_\(STATIC\|INSTALL_NO_USR\|DESKTOP\|USE_PORTABLE_CODE\|LONG_OPTS\|SH_IS_NONE\|WGET\|FEATURE_WGET_LONG_OPTIONS\|FEATURE_WGET_TIMEOUT\)[ =].*$/CONFIG_\1=y/' .config && \
    sed -i 's/^.*\(CONFIG_SH_IS_ASH\)[ =].*$/\1=n/' .config && \
    sed -i 's/^.*\(CONFIG_PREFIX\)[ =].*$/\1="\/busybox"/' .config && \
    sed -i 's/^.*\(CONFIG_EXTRA_CFLAGS\)[ =].*$/\1="-Os -s"/' .config && \
    make busybox && \
    make install && \
    apk del --no-cache --no-network make && \
    rm -rf *

COPY healthcheck.c ./

RUN gcc -Os -s -static -o /healthcheck healthcheck.c && \
    apk del --no-cache --no-network libc-dev gcc


WORKDIR /go/src
ARG AUTHELIA_VERSION
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    wget -qO - "https://github.com/authelia/authelia/archive/refs/tags/v${AUTHELIA_VERSION}.tar.gz" | \
        tar -xzf - $(echo api cmd internal go.mod go.sum | xargs -n 1 printf " authelia-${AUTHELIA_VERSION}/%s") && \
    cd "authelia-${AUTHELIA_VERSION}" && \
    mv api internal/server/public_html/api && \
    wget -qO - "https://github.com/authelia/authelia/releases/download/v${AUTHELIA_VERSION}/authelia-v${AUTHELIA_VERSION}-public_html.tar.gz" | \
        tar -C internal/server -xzf - && \
    CGO_ENABLED=0 go build -ldflags="-s -w" -o /go/bin/authelia ./cmd/authelia && \
    mkdir -p /var/lib/authelia/notifications /app && \
    chown -R 65532:65532 /var/lib/authelia && \
    cd .. && rm -r "authelia-${AUTHELIA_VERSION}"


ARG DISTROLESS_SUFFIX
FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

COPY --from=builder-backend /busybox/bin/* /bin/
COPY --from=builder-backend --chown=nonroot:nonroot /app /app
COPY --from=builder-backend /go/bin/authelia /healthcheck /app/
COPY --from=builder-backend --chown=nonroot:nonroot /var/lib/authelia /var/lib/authelia

COPY --chown=nonroot:nonroot ./healthcheck.env /app/.healthcheck.env
COPY ./configuration.yml /etc/authelia.yml

USER nonroot
ENTRYPOINT ["/app/authelia"]
EXPOSE 9959
ENV X_AUTHELIA_CONFIG="/etc/authelia.yml"
ENV X_AUTHELIA_HEALTHCHECK=1
HEALTHCHECK --interval=30s --timeout=3s --start-period=1m CMD /app/healthcheck
VOLUME /var/lib/authelia/notifications
