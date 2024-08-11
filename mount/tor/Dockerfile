ARG ALPINE_VERSION
FROM alpine:$ALPINE_VERSION AS builder-base

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add gcc mold make libc-dev fortify-headers linux-headers


FROM builder-base AS builder-zlib

ARG CFLAGS
ARG LDFLAGS
ARG ZLIB_VERSION
WORKDIR /usr/local/src/zlib
RUN wget -qO - "https://github.com/madler/zlib/archive/refs/tags/v${ZLIB_VERSION}.tar.gz" | \
        tar -xzf - --strip-components 1 && \
    ./configure --prefix="$(pwd)/install" --static

RUN --network=none mold -run make -j$(nproc) install


FROM builder-base AS builder-openssl

ARG CFLAGS
ARG LDFLAGS
ARG OPENSSL_VERSION
WORKDIR /usr/local/src/openssl

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add perl && \
    wget -qO - "https://github.com/openssl/openssl/archive/refs/tags/openssl-${OPENSSL_VERSION}.tar.gz" | \
        tar -xzf - --strip-components 1 && \
    ./Configure \
        --prefix="$(pwd)/install" \
        no-shared \
        no-dso \
        enable-pic \
        threads \
        no-filenames \
        no-tests \
        no-zlib \
        no-async \
        no-comp \
        no-idea \
        no-mdc2 \
        no-rc5 \
        no-ec2m \
        no-sm2 \
        no-sm4 \
        no-ssl2 \
        no-ssl3 \
        no-seed \
        no-weak-ssl-ciphers \
        linux-x86_64

RUN --network=none mold -run make install_sw


FROM builder-base AS builder-libevent

ARG CFLAGS
ARG LDFLAGS
ARG LIBEVENT_VERSION
WORKDIR /usr/local/src/libevent
RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    --mount=target=openssl,ro,source=/usr/local/src/openssl/install,from=builder-openssl \
    apk add file && \
    wget -qO - "https://github.com/libevent/libevent/releases/download/release-${LIBEVENT_VERSION}-stable/libevent-2.1.12-stable.tar.gz" | \
      tar -xzf - --strip-components 1 && \
    PKG_CONFIG_PATH="$(pwd)/openssl/lib64/pkgconfig" LDFLAGS="$LDFLAGS -L$(pwd)/openssl/lib64" CPPFLAGS="-I$(pwd)/openssl/include" ./configure \
        --prefix="$(pwd)/install" \
        --disable-shared \
        --enable-static \
        --with-pic

RUN --mount=target=openssl,ro,source=/usr/local/src/openssl/install,from=builder-openssl \
    --network=none mold -run make -j$(nproc) install


FROM builder-base as builder

ARG CFLAGS
ARG LDFLAGS
ARG TOR_VERSION
WORKDIR /usr/local/src/tor

RUN --mount=target=zlib,ro,source=/usr/local/src/zlib/install,from=builder-zlib \
    --mount=target=libevent,ro,source=/usr/local/src/libevent/install,from=builder-libevent \
    --mount=target=openssl,ro,source=/usr/local/src/openssl/install,from=builder-openssl \
    --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add libcap-setcap zstd-dev zstd-static && \
    wget -qO - "https://dist.torproject.org/tor-$TOR_VERSION.tar.gz" | \
        tar -xzf - --strip-components 1 && \
    ./configure --help && \
    CPPFLAGS="-I$(pwd)/zlib/include -I$(pwd)/openssl/include -I$(pwd)/libevent/include" ./configure \
        --prefix="$(pwd)/install" \
        --disable-gcc-warnings-advisory \
        --disable-gcc-hardening \
        --enable-dependency-tracking \
        --enable-gpl \
        --disable-manpage --disable-html-manual --disable-asciidoc \
        --sysconfdir=/etc \
        --localstatedir=/var \
        --enable-static-tor \
        --with-zlib-dir=zlib/lib \
        --with-libevent-dir=libevent/lib \
        --with-openssl-dir=openssl/lib64 \
        --disable-unittests \
        --enable-pic \
        --disable-module-relay \
        --enable-zstd && \
    find -type f -name '*Makefile*' -exec sed -i 's/\(^\|[^[:alnum:]_-]\)-static\($\|[^[:alnum:]=_-]\)/\1-static-pie\2/' '{}' \+

RUN --mount=target=zlib,ro,source=/usr/local/src/zlib/install,from=builder-zlib \
    --mount=target=libevent,ro,source=/usr/local/src/libevent/install,from=builder-libevent \
    --mount=target=openssl,ro,source=/usr/local/src/openssl/install,from=builder-openssl \
    --network=none \
    mold -run make -j$(nproc) install && strip install/bin/tor

ARG DISTROLESS_SUFFIX
FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

USER root

COPY --from=builder /usr/local/src/tor/install/bin/tor /bin/

RUN --mount=target=/lib/ld-musl-x86_64.so.1,source=/lib/ld-musl-x86_64.so.1,from=builder \
    --mount=target=/lib/libcap.so.2,source=/usr/lib/libcap.so.2,from=builder \
    --mount=target=/bin/busybox,source=/bin/busybox,from=builder \
    --mount=target=/bin/setcap,source=/usr/sbin/setcap,from=builder \
    ["busybox", "sh", "-c", "\
      setcap cap_net_bind_service=+ep /bin/tor && \
      busybox install -Dd -o nonroot -g nonroot -m750 /var/lib/tor && \
      busybox install -Dd -g nonroot -m750 /etc/tor && \
      for i in hostname hs_ed25519_secret_key hs_ed25519_public_key; do \
          busybox ln -s \"/run/secrets/$i\" /var/lib/tor || exit; \
      done \
      " \
    ]

USER nonroot

COPY torrc /etc/tor/

EXPOSE 9050

VOLUME ["/var/lib/tor"]
ENTRYPOINT ["tor", "-f", "/etc/tor/torrc"]
