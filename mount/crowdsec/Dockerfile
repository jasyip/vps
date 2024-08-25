ARG GO_BUILDER_VERSION
ARG DISTROLESS_SUFFIX
FROM golang:${GO_BUILDER_VERSION} AS builder-base

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add moreutils gpg gpg-agent \
       ccache g++ make mold libc-dev fortify-headers \
       bash gettext pkgconfig && \
    find /usr/lib/ccache/bin -type l -exec ln -s \{\} /usr/local/bin \;

COPY ccache.conf /etc/

FROM builder-base AS builder-busybox

WORKDIR /usr/local/src/busybox
ARG BUSYBOX_VERSION
ARG CFLAGS
ARG LDFLAGS

RUN --mount=target=busybox-setup.sh,ro,source=busybox-setup.sh \
    --mount=target=busybox-config.sh,ro,source=busybox-config.sh \
    . busybox-setup.sh

RUN --mount=type=cache,target=/var/ccache \
    --network=none \
    mold -run make busybox && make install

FROM builder-base AS builder-yq

WORKDIR /usr/local/src/yq

ARG YQ_VERSION
RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    wget -qO - "https://github.com/mikefarah/yq/archive/refs/tags/v${YQ_VERSION}.tar.gz" | \
      tar -xzof - --strip-components 1 && \
    exec go mod download

ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/var/ccache \
    --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_CXXFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec mold -run go build -buildmode=pie -trimpath -ldflags="-s -w -linkmode=external -extldflags=-static-pie" .

FROM builder-base AS builder

ARG RE2_VERSION
WORKDIR /usr/local/src/re2
RUN wget -qO - "https://github.com/google/re2/archive/refs/tags/${RE2_VERSION}.tar.gz" | \
      tar -xzof - --strip-components 1

ARG CFLAGS
ARG LDFLAGS
RUN --mount=type=cache,target=/var/ccache \
    --network=none \
    exec mold -run make CXXFLAGS="$CFLAGS" static-install

WORKDIR /usr/local/src/crowdsec


ARG CROWDSEC_VERSION
RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    wget -qO - "https://github.com/crowdsecurity/crowdsec/archive/refs/tags/${CROWDSEC_VERSION}.tar.gz" | \
      tar -xzof - --strip-components 1 && \
    exec go mod download

RUN --mount=type=cache,target=/var/ccache \
    --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    export CFLAGS="$CFLAGS -D_LARGEFILE64_SOURCE" && \
    CGO_CFLAGS="$CFLAGS" CGO_CXXFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec mold -run make release DOCKER_BUILD=1 BUILD_STATIC=1 \
         EXTLDFLAGS="-extldflags=-static-pie -linkmode=external" DISABLE_OPTIMIZATION="-buildmode=pie" \
         BUILD_VERSION="$CROWDSEC_VERSION" PLUGINS="dummy email file http"


RUN ( cd crowdsec-v* && ./wizard.sh --docker-mode ) && \
    cscli hub update && \
    cscli collections install crowdsecurity/linux && \
    cscli parsers install crowdsecurity/whitelists

FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot


USER root
COPY --from=builder-busybox /busybox/bin/busybox /usr/sbin/
COPY --from=builder-yq /usr/local/src/yq/yq /usr/bin/
COPY --from=builder /usr/local/bin /usr/bin
COPY --from=builder /etc/crowdsec /staging/etc/crowdsec
COPY --from=builder /usr/local/src/crowdsec/docker/config.yaml /staging/etc/crowdsec/
COPY --chmod=444 ./docker_start.sh /
COPY ./config.yaml.local /staging/etc/crowdsec/
COPY ./acquis.d /staging/etc/crowdsec/acquis.d

SHELL ["busybox", "sh", "-c"]
RUN --mount=target=/lib/ld-musl-x86_64.so.1,source=/lib/ld-musl-x86_64.so.1,from=builder \
    --mount=target=/usr/sbin/busybox,source=/bin/busybox,from=builder \
    cd /usr/sbin && \
    for i in cat chown cp dirname find grep install ln mkdir readlink sed sh tr true wget; do \
      busybox ln -s busybox "$i" || exit ; \
    done && \
    mkdir -p /staging/etc/crowdsec/acquis.d \
             /staging/var/lib/crowdsec \
             /etc/crowdsec \
             /var/lib/crowdsec/data \
             /var/log/crowdsec && \
    chown -R nonroot:nonroot /etc/crowdsec /var/*/crowdsec /staging && \
    yq -n '.url="http://0.0.0.0:8080"' | install -m600 -o nonroot -g nonroot /dev/stdin /staging/etc/crowdsec/local_api_credentials.yaml && \
    yq eval -i '.plugin_config.group = "nogroup"' /staging/etc/crowdsec/config.yaml

SHELL [""]

USER nonroot


EXPOSE 6060
HEALTHCHECK CMD wget -q --spider localhost:8080/health || exit 1
ENTRYPOINT ["sh", "/docker_start.sh"]
VOLUME /etc/crowdsec /var/lib/crowdsec/data /var/log/crowdsec
