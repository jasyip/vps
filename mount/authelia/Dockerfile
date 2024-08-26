ARG GO_BUILDER_VERSION
ARG DISTROLESS_SUFFIX
FROM golang:${GO_BUILDER_VERSION} AS builder-base

SHELL ["/bin/sh", "-eCuxo", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add gpg gpg-agent ccache gcc make mold libc-dev fortify-headers; \
    find /usr/lib/ccache/bin -type l -exec ln -s \{\} /usr/local/bin \;

COPY ccache.conf /etc/

FROM builder-base AS builder-other

ARG BUSYBOX_VERSION
ARG CFLAGS
ARG LDFLAGS

WORKDIR /usr/local/src/busybox
RUN --mount=target=busybox-setup.sh,ro,source=busybox-setup.sh \
    --mount=target=busybox-config.sh,ro,source=busybox-config.sh \
    . busybox-setup.sh

RUN --mount=type=cache,target=/var/ccache \
    --mount=target=healthcheck.c,source=healthcheck.c \
    --network=none \
    mold -run make busybox; make install; \
    exec cc $CFLAGS -s -static-pie -o /healthcheck healthcheck.c


FROM builder-base AS builder

WORKDIR /usr/local/src/authelia

ARG AUTHELIA_VERSION
RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    wget -O - "https://github.com/authelia/authelia/archive/refs/tags/v${AUTHELIA_VERSION}.tar.gz" | \
      tar -xzof - --strip-components 1 $(printf "authelia-${AUTHELIA_VERSION}/%s " api cmd internal go.mod go.sum); \
    HTML_URL="https://github.com/authelia/authelia/releases/download/v${AUTHELIA_VERSION}/authelia-v${AUTHELIA_VERSION}-public_html.tar.gz"; \
    wget -O - "$HTML_URL" | tee >(tar -C internal/server -xzof -) | \
      sha256sum -c <(wget -O - "${HTML_URL}.sha256" | awk '{print $1 " -"}'); \
    mv -f api/* -t internal/server/public_html/api; \
    mkdir -p /var/lib/authelia/notifications /app; \
    exec go mod download

ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/var/ccache \
    --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_CXXFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec go build -buildmode=pie -trimpath -ldflags="-s -w -linkmode=external -extldflags=-static-pie" ./cmd/authelia


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
