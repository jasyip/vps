ARG ALPINE_VERSION
FROM alpine:$ALPINE_VERSION as builder

ARG ZLIB_VERSION
ARG LIBEVENT_VERSION
ARG OPENSSL_VERSION
ARG TOR_VERSION
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

ARG CFLAGS="-O2 -march=native -pipe -D_FORTIFY_SOURCE=2 -ftrivial-auto-var-init=pattern -pie -Wl,-z,relro,-z,now -fstack-protector-strong -fstack-clash-protection -fcf-protection=full -fuse-ld=mold"
ARG LDFLAGS="-s -w"

RUN mkdir zlib && cd zlib && \
    wget -qO - "https://zlib.net/zlib-${ZLIB_VERSION}.tar.xz" | \
      tar -xJf - --strip-components 1 && \
    ./configure \
      --prefix="$(pwd)/install" \
      --static \
    && \
    CFLAGS="$CFLAGS -fPIE -pie" make -j$(nproc) install && \
    cd .. && \
    mkdir libevent && cd libevent && \ 
    wget -qO - "https://github.com/libevent/libevent/releases/download/release-${LIBEVENT_VERSION}-stable/libevent-2.1.12-stable.tar.gz" | \
      tar -xzf - --strip-components 1 && \
    ./configure --prefix=$PWD/install \
           --disable-shared \
           --enable-static \
           --with-pic \
    && \
    make -j$(nproc) install && \
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
    make install_sw && \
    apk del --no-cache --no-network \
      perl \
      linux-headers \
      openssl-dev

WORKDIR tor

RUN wget -qO - "https://dist.torproject.org/tor-$TOR_VERSION.tar.gz" | \
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
    make -j$(nproc) install && \
    apk del --no-cache --no-network \
      gcc \
      libc-dev \
      mold \
      make \
      zstd-dev \
      zstd-static

FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

USER root

COPY --from=builder /tor/install/bin/tor /usr/sbin/setcap /bin/busybox /bin/
COPY --from=builder /lib/ld-musl-x86_64.so.1 /usr/lib/libcap.so.2 /lib/

SHELL ["/bin/busybox", "sh", "-c"]

RUN setcap cap_net_bind_service=+ep /bin/tor && \
    busybox install -Dd -o nonroot -g nonroot -m700 /etc/tor /var/lib/tor && \
    for i in hostname hs_ed25519_secret_key hs_ed25519_public_key; do \
      busybox ln -s "/run/secrets/$i" /var/lib/tor || exit; \
    done && \
    busybox rm -- /lib/* /bin/setcap /bin/busybox

SHELL [""]

USER nonroot

COPY torrc /etc/tor/

EXPOSE 9050

VOLUME ["/var/lib/tor"]
ENTRYPOINT ["tor", "-f", "/etc/tor/torrc"]
