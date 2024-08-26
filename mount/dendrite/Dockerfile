# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: GPL-2.0-only

ARG GO_BUILDER_VERSION
ARG DISTROLESS_SUFFIX
FROM golang:${GO_BUILDER_VERSION} AS builder

SHELL ["/bin/sh", "-eCuxo", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add gcc libc-dev mold fortify-headers

WORKDIR /usr/local/src/dendrite
ARG DENDRITE_VERSION

RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    wget -O - "https://github.com/matrix-org/dendrite/archive/refs/tags/v${DENDRITE_VERSION}.tar.gz" | \
      tar -xzof - --strip-components 1; \
    mkdir -p /var/lib/dendrite /var/log/dendrite; \
    exec go mod download

ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/go/pkg/mod,ro \
    --mount=type=cache,target=/root/.cache/go-build \
    --network=none \
    CGO_ENABLED=1 CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec go build -buildmode=pie -trimpath -ldflags="-s -w -linkmode=external -extldflags=-static-pie" -o bin/ \
      $(printf "./cmd/%s " create-account dendrite generate-config generate-keys)


FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot
COPY --from=builder \
     /usr/local/src/dendrite/bin/create-account \
     /usr/local/src/dendrite/bin/generate-config \
     /usr/local/src/dendrite/bin/generate-keys \
     /usr/local/src/dendrite/bin/dendrite \
     /usr/bin/

VOLUME /etc/dendrite
WORKDIR /etc/dendrite

ENTRYPOINT ["dendrite"]

EXPOSE 8008 8448
