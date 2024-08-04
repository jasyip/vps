ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder-base


RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add g++ libc-dev make bash gettext pkgconfig mold

FROM builder-base AS builder-yq

WORKDIR /usr/local/src/yq

ARG YQ_VERSION
RUN --mount=type=cache,target=/go/pkg/mod \
    wget -qO - "https://github.com/mikefarah/yq/archive/refs/tags/v${YQ_VERSION}.tar.gz" | \
      tar -xzf - --strip-components 1 && \
    exec go mod download

ARG CFLAGS="-O2 -march=native -pipe -D_FORTIFY_SOURCE=2 -ftrivial-auto-var-init=pattern -fstack-protector-strong -fstack-clash-protection -fcf-protection=full -fuse-ld=mold -flto -fPIE -pie"
ARG LDFLAGS="-Wl,-O1,--sort-common,-z,relro,-z,now"

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_CFLAGS="$CFLAGS" CGO_CXXFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec mold -run go build -buildmode=pie -trimpath -ldflags="-s -w -linkmode=external -extldflags=-static-pie" .

FROM builder-base AS builder

ARG CFLAGS="-O2 -march=native -pipe -D_FORTIFY_SOURCE=2 -ftrivial-auto-var-init=pattern -fstack-protector-strong -fstack-clash-protection -fcf-protection=full -fuse-ld=mold -flto -fPIE -pie"
ARG LDFLAGS="-Wl,-O1,--sort-common,-z,relro,-z,now"
ARG RE2_VERSION
WORKDIR /usr/local/src/re2
RUN wget -qO - "https://github.com/google/re2/archive/refs/tags/${RE2_VERSION}.tar.gz" | \
      tar -xzf - --strip-components 1
RUN CXXFLAGS="$CFLAGS" exec mold -run make static-install

WORKDIR /usr/local/src/crowdsec


ARG CROWDSEC_VERSION
RUN --mount=type=cache,target=/go/pkg/mod \
    wget -qO - "https://github.com/crowdsecurity/crowdsec/archive/refs/tags/${CROWDSEC_VERSION}.tar.gz" | \
      tar -xzf - --strip-components 1 && \
    exec go mod download

RUN --mount=type=cache,target=/go/pkg/mod \
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

ARG DISTROLESS_SUFFIX
FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:debug-nonroot


USER root
COPY --from=builder-yq /usr/local/src/yq/yq /usr/local/bin/
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /etc/crowdsec /staging/etc/crowdsec
COPY --from=builder /usr/local/src/crowdsec/docker/config.yaml /staging/etc/crowdsec/
COPY --chmod=444 ./docker_start.sh /
COPY ./config.yaml.local /staging/etc/crowdsec/
COPY ./acquis.d /staging/etc/crowdsec/acquis.d

SHELL ["/busybox/sh", "-c"]

RUN mkdir -p /staging/etc/crowdsec/acquis.d \
             /staging/var/lib/crowdsec \
             /etc/crowdsec \
             /var/lib/crowdsec/data && \
    chown -R nonroot:nonroot /etc/crowdsec /var/lib/crowdsec /staging && \
    yq -n '.url="http://0.0.0.0:8080"' | install -m600 -o nonroot -g nonroot /dev/stdin /staging/etc/crowdsec/local_api_credentials.yaml && \
    yq eval -i '.plugin_config.group = "nogroup"' /staging/etc/crowdsec/config.yaml

USER nonroot


EXPOSE 6060
HEALTHCHECK CMD wget -q --spider localhost:8080/health || exit 1
ENTRYPOINT ["sh", "/docker_start.sh"]
VOLUME /etc/crowdsec /var/lib/crowdsec/data /var/log
