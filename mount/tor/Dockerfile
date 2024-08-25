ARG ALPINE_VERSION
ARG DISTROLESS_SUFFIX
FROM alpine:$ALPINE_VERSION AS builder-base

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add moreutils gpg gpg-agent \
            ccache gcc mold make \
            libc-dev fortify-headers linux-headers && \
    find /usr/lib/ccache/bin -type l -exec ln -s \{\} /usr/local/bin \;

COPY ccache.conf /etc/

RUN gpg --fetch-keys \
      "https://madler.net/madler/pgp.html" \
      "https://keys.openpgp.org/vks/v1/by-fingerprint/BA5473A2B0587B07FB27CF2D216094DFD0CB81EF" \
      "https://www.wangafu.net/~nickm/public_key.asc" \
      "https://azat.sh/azatpub.asc" \
      "https://keys.openpgp.org/vks/v1/by-fingerprint/1C1BC007A9F607AA8152C040BEA7B180B1491921" \
      "https://keys.openpgp.org/vks/v1/by-fingerprint/B74417EDDF22AC9F9E90F49142E86A2A11F48D36" \
      "https://keys.openpgp.org/vks/v1/by-fingerprint/2133BC600AB133E1D826D173FE43009C4607B1FB"

FROM builder-base AS builder-zlib

ARG CFLAGS
ARG LDFLAGS
ARG ZLIB_VERSION
WORKDIR /usr/local/src/zlib
RUN URL="https://github.com/madler/zlib/releases/download/v${ZLIB_VERSION}/zlib-${ZLIB_VERSION}.tar.xz" && \
    wget -qO - "$URL" | pee 'tar -xJof - --strip-components 1' cat | \
      gpg --assert-signer 5ED46A6721D365587791E2AA783FCD8E58BCAFBA \
          --lock-never --verify <(wget -qO - "${URL}.asc") -

RUN exec ./configure --prefix="$(pwd)/install" --static

RUN --mount=type=cache,target=/var/ccache \
    --network=none \
    exec mold -run make -j$(nproc) install


FROM builder-base AS builder-openssl

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add perl

ARG CFLAGS
ARG LDFLAGS
ARG OPENSSL_VERSION
WORKDIR /usr/local/src/openssl

RUN URL="https://github.com/openssl/openssl/releases/download/openssl-${OPENSSL_VERSION}/openssl-${OPENSSL_VERSION}.tar.gz" && \
    wget -qO - "$URL" | pee 'tar -xzof - --strip-components 1' \
      "gpg --assert-signer BA5473A2B0587B07FB27CF2D216094DFD0CB81EF \
           --lock-never --verify <(wget -qO - '${URL}.asc') -" cat | \
      sha256sum -c <(wget -qO - "${URL}.sha256" | awk '{print $1 " -"}') && \
    exec ./Configure \
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

RUN --mount=type=cache,target=/var/ccache \
    --network=none \
    exec mold -run make install_dev


FROM builder-base AS builder-libevent
RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add file

ARG CFLAGS
ARG LDFLAGS
ARG LIBEVENT_VERSION
WORKDIR /usr/local/src/libevent

RUN --mount=target=openssl,ro,source=/usr/local/src/openssl/install,from=builder-openssl \
    URL="https://github.com/libevent/libevent/releases/download/release-${LIBEVENT_VERSION}-stable/libevent-${LIBEVENT_VERSION}-stable.tar.gz" && \
    wget -qO - "$URL" | pee 'tar -xzof - --strip-components 1' cat | \
      gpg --assert-signer 2133BC600AB133E1D826D173FE43009C4607B1FB \
          --assert-signer 9E3AC83A27974B84D1B3401DB86086848EF8686D \
          --lock-never --verify <(wget -qO - "${URL}.asc") - && \
    PKG_CONFIG_PATH="$(pwd)/openssl/lib64/pkgconfig" \
    LDFLAGS="$LDFLAGS -L$(pwd)/openssl/lib64" \
    CPPFLAGS="-I$(pwd)/openssl/include" \
    exec ./configure \
        --prefix="$(pwd)/install" \
        --disable-shared \
        --enable-static \
        --with-pic

RUN --mount=type=cache,target=/var/ccache \
    --mount=target=openssl,ro,source=/usr/local/src/openssl/install,from=builder-openssl \
    --network=none \
    exec mold -run make -j$(nproc) install


FROM builder-base as builder

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add libcap-setcap zstd-dev zstd-static

ARG CFLAGS
ARG LDFLAGS
ARG TOR_VERSION
WORKDIR /usr/local/src/tor

RUN --mount=target=zlib,ro,source=/usr/local/src/zlib/install,from=builder-zlib \
    --mount=target=libevent,ro,source=/usr/local/src/libevent/install,from=builder-libevent \
    --mount=target=openssl,ro,source=/usr/local/src/openssl/install,from=builder-openssl \
    URL="https://dist.torproject.org/tor-$TOR_VERSION.tar.gz" && \
    wget -qO - "$URL" | pee "tar -xzof - --strip-components 1" cat | \
      sha256sum -c <(wget -qO - "${URL}.sha256sum" | pee \
                       "gpg --assert-signer 514102454D0A87DB0767A1EBBE6A0531C18A9179 \
                            --assert-signer B74417EDDF22AC9F9E90F49142E86A2A11F48D36 \
                            --assert-signer 2133BC600AB133E1D826D173FE43009C4607B1FB \
                            --lock-never --verify <(wget -qO - '${URL}.sha256sum.asc') -" \
                       cat | awk '{print $1 " -"}') && \
    CPPFLAGS="-I$(pwd)/zlib/include -I$(pwd)/openssl/include -I$(pwd)/libevent/include" \
    ./configure \
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
    find -type f -name '*Makefile*' -exec sed -i \
      's/\(^\|[^[:alnum:]_-]\)-static\($\|[^[:alnum:]=_-]\)/\1-static-pie\2/' '{}' \+

RUN --mount=target=zlib,ro,source=/usr/local/src/zlib/install,from=builder-zlib \
    --mount=target=libevent,ro,source=/usr/local/src/libevent/install,from=builder-libevent \
    --mount=target=openssl,ro,source=/usr/local/src/openssl/install,from=builder-openssl \
    --mount=type=cache,target=/var/ccache \
    --network=none \
    mold -run make -j$(nproc) install && \
    strip install/bin/tor

FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

USER root

COPY --from=builder /usr/local/src/tor/install/bin/tor /usr/bin/

RUN --mount=target=/lib/ld-musl-x86_64.so.1,source=/lib/ld-musl-x86_64.so.1,from=builder \
    --mount=target=/lib/libcap.so.2,source=/usr/lib/libcap.so.2,from=builder \
    --mount=target=/usr/local/sbin/busybox,source=/bin/busybox,from=builder \
    --mount=target=/usr/local/sbin/setcap,source=/usr/sbin/setcap,from=builder \
    ["busybox", "sh", "-c", "\
      setcap cap_net_bind_service=+ep /usr/bin/tor && \
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
