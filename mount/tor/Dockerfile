ARG ALPINE_VERSION
FROM alpine:$ALPINE_VERSION AS builder

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add \
      gcc \
      libc-dev \
      mold \
      make \
      perl \
      linux-headers \
      libcap-setcap \
      openssl-dev \
      zstd-dev \
      zstd-static

ARG CFLAGS
ARG LDFLAGS
ARG LIBEVENT_VERSION
ARG OPENSSL_VERSION
ARG ZLIB_VERSION

RUN mkdir zlib && cd zlib && \
    wget -qO - "https://zlib.net/zlib-${ZLIB_VERSION}.tar.xz" | \
      tar -xJf - --strip-components 1 && \
    ./configure \
      --prefix="$(pwd)/install" \
      --static \
    && \
    mold -run make -j$(nproc) install && \
    cd .. && \
    mkdir libevent && cd libevent && \ 
    wget -qO - "https://github.com/libevent/libevent/releases/download/release-${LIBEVENT_VERSION}-stable/libevent-2.1.12-stable.tar.gz" | \
      tar -xzf - --strip-components 1 && \
    ./configure --prefix=$PWD/install \
           --disable-shared \
           --enable-static \
           --with-pic \
    && \
    mold -run make -j$(nproc) install && \
    cd .. && \
    mkdir openssl && cd openssl && \
    wget -qO - https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz | \
      tar -xzf - --strip-components 1 && \ 
    ./Configure --prefix="$(pwd)/install" \
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
      linux-x86_64 \
    && \
    mold -run make install_sw && \
    apk del --no-cache --no-network \
      perl \
      linux-headers \
      openssl-dev

ARG TOR_VERSION

RUN mkdir tor && cd tor && \
    wget -qO - "https://dist.torproject.org/tor-$TOR_VERSION.tar.gz" | \
      tar -xzf - --strip-components 1 && \
    ./configure \
      --prefix="$(pwd)/install" \
      --exec-prefix="$(pwd)/install" \
      --enable-dependency-tracking \
      --enable-gpl \
      --disable-manpage --disable-html-manual --disable-asciidoc \
      --prefix=/usr \
      --sysconfdir=/etc \
      --localstatedir=/var \
      --enable-static-tor \
      --with-zlib-dir=../zlib/install \
      --with-libevent-dir=../libevent/install \
      --with-openssl-dir=../openssl/install \
      --disable-unittests \
      --enable-pic \
      --disable-module-relay \
      --enable-zstd \
      && \
    mold -run make -j$(nproc) install && \
    apk del --no-cache --no-network \
      clang \
      libc-dev \
      mold \
      make \
      zstd-dev \
      zstd-static

ARG DISTROLESS_SUFFIX
FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

USER root

COPY --from=builder /tor/install/bin/tor /bin/

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
