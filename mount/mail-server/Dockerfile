# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: AGPL-3.0-only

ARG MUSLRUST_VERSION
ARG ALPINE_VERSION
ARG DISTROLESS_SUFFIX
FROM clux/muslrust:${MUSLRUST_VERSION} AS builder

WORKDIR /app
RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > \
      /etc/apt/apt.conf.d/keep-cache && \
    apt-get update && \
    exec apt-get install -y --no-install-recommends mold protobuf-compiler make wget

ARG MAIL_SERVER_VERSION
ARG CARGO_BUILD_TARGET=x86_64-unknown-linux-musl
RUN --mount=type=cache,target=/root/.cargo/registry/cache,sharing=locked \
    wget -qO - "https://github.com/stalwartlabs/mail-server/archive/refs/tags/${MAIL_SERVER_VERSION}.tar.gz" | \
      tar -xzof - --strip-components 1 && \
    exec cargo fetch --locked --color=always

ARG RUSTFLAGS
RUN --mount=type=cache,target=/app/target \
    --mount=type=cache,target=/root/.cargo/registry/cache,ro \
    --network=none \
    cargo build --color=always --release --bins \
        --frozen --no-default-features --features=postgres \
        -p mail-server -p stalwart-cli && \
    find /app/target/**/release/stalwart-* -executable -exec \
        install -Dm755 -s -t /app/binaries '{}' \+

FROM alpine:${ALPINE_VERSION} AS supplementary

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add libcap-setcap

FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

COPY --from=builder /app/binaries/ /usr/bin/

USER root

COPY ./etc/ /opt/stalwart-mail/etc/

SHELL ["busybox", "sh", "-c"]

RUN --mount=target=/lib/ld-musl-x86_64.so.1,source=/lib/ld-musl-x86_64.so.1,from=supplementary \
    --mount=target=/lib/libcap.so.2,source=/usr/lib/libcap.so.2,from=supplementary \
    --mount=target=/usr/local/sbin/busybox,source=/bin/busybox,from=supplementary \
    --mount=target=/usr/local/sbin/setcap,source=/usr/sbin/setcap,from=supplementary \
    setcap cap_net_bind_service=+ep /usr/bin/stalwart-mail && \
    busybox chown nonroot /opt/stalwart-mail && \
    busybox find /opt/stalwart-mail/etc -type d -exec busybox chmod 755 \{\} \+ \
        -o -type f -exec busybox chmod 644 \{\} \+

SHELL [""]

USER nonroot

VOLUME [ "/opt/stalwart-mail" ]
ENTRYPOINT [ "stalwart-mail", "--config", "/opt/stalwart-mail/etc/config.toml" ]
EXPOSE 8080 25 587 465 143 993 4190
