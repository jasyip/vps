ARG ALPINE_VERSION
ARG DISTROLESS_SUFFIX
FROM alpine:$ALPINE_VERSION AS builder-base

SHELL ["/bin/sh", "-eCuxo", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add gpg gpg-agent \
            ccache gcc mold make cmake samurai \
            libc-dev fortify-headers linux-headers pkgconf; \
    find /usr/lib/ccache/bin -type l -exec ln -s \{\} /usr/local/bin \;

COPY ccache.conf /etc/

RUN exec gpg --fetch-keys \
             'https://keys.openpgp.org/vks/v1/by-fingerprint/BA5473A2B0587B07FB27CF2D216094DFD0CB81EF' \
             'https://www.wangafu.net/~nickm/public_key.asc' \
             'https://azat.sh/azatpub.asc' \
             'https://keys.openpgp.org/vks/v1/by-fingerprint/1C1BC007A9F607AA8152C040BEA7B180B1491921' \
             'https://keys.openpgp.org/vks/v1/by-fingerprint/B74417EDDF22AC9F9E90F49142E86A2A11F48D36' \
             'https://keys.openpgp.org/vks/v1/by-fingerprint/2133BC600AB133E1D826D173FE43009C4607B1FB'


FROM alpine:$ALPINE_VERSION AS supplementary

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add libcap-setcap


FROM builder-base AS builder-zlib

WORKDIR /usr/local/src/zlib
ARG CFLAGS
ARG LDFLAGS
ARG ZLIB_VERSION
RUN wget -O - "https://github.com/zlib-ng/zlib-ng/archive/refs/tags/${ZLIB_VERSION}.tar.gz" | \
      tar -xzo --strip-components 1 $(printf "--exclude zlib-ng-${ZLIB_VERSION}/%s " doc test); \
    exec cmake -B build -G Ninja \
      -DWITH_GTEST=OFF \
      -DWITH_SANITIZER=OFF \
      -DZLIB_ENABLE_TESTS=OFF \
      -DZLIB_COMPAT=ON \
      -DWITH_RUNTIME_CPU_DETECTION=OFF \
      -DWITH_NATIVE_INSTRUCTIONS=ON

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --network=none \
    cd build; \
    cmake --build . -t zlibstatic; \
    install -Dm644 libz.a -t /opt/zlib/lib; \
    install -Dm644 *.h -t /opt/zlib/include; \
    install -Dm644 zlib.pc -t /opt/zlib/lib/pkgconfig; \
    find . -iname 'zlib*.cmake' -exec install -Dm644 -t /opt/zlib/lib/cmake/ZLIB '{}' \+


FROM builder-base AS builder

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add file perl

WORKDIR /usr/local/src/openssl
ARG CFLAGS
ARG LDFLAGS
ARG OPENSSL_VERSION

RUN URL="https://github.com/openssl/openssl/releases/download/openssl-${OPENSSL_VERSION}/openssl-${OPENSSL_VERSION}.tar.gz"; \
    wget -O - "$URL" | tee >(tar -xzo --strip-components 1 $(printf "--exclude openssl-${OPENSSL_VERSION}/%s " test doc/man3 doc/man7)) \
      >(gpg --assert-signer BA5473A2B0587B07FB27CF2D216094DFD0CB81EF \
            --lock-never --verify <(wget -O - "${URL}.asc") -) | \
      sha256sum -c <(wget -O - "${URL}.sha256" | awk '{print $1 " -"}'); \
    exec ./Configure \
        linux-x86_64 \
        --libdir=lib \
        enable-ktls \
        no-async \
        no-autoalginit \
        no-autoerrinit \
        no-cmp \
        no-cms \
        no-ct \
        no-comp \
        no-dgram \
        no-docs \
        no-dso \
        no-ec2m \
        enable-ec_nistp_64_gcc_128 \
        no-engine \
        no-err \
        no-filenames \
        no-gost \
        no-http \
        no-legacy \
        no-makedepend \
        no-multiblock \
        no-nextprotoneg \
        no-padlockeng \
        no-rfc3779 \
        no-stdio \
        no-srp \
        no-srtp \
        no-ssl-trace \
        no-static-engine \
        threads \
        no-ts \
        no-ui-console \
        no-idea \
        no-mdc2 \
        no-sm2 \
        no-sm4 \
        no-seed

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --network=none \
    make -j$(nproc) build_libs; \
    make install_dev

WORKDIR /usr/local/src/libevent
ARG LIBEVENT_VERSION

RUN URL="https://github.com/libevent/libevent/releases/download/release-${LIBEVENT_VERSION}-stable/libevent-${LIBEVENT_VERSION}-stable.tar.gz"; \
    wget -O - "$URL" | tee >(tar -xzo --strip-components 1 $(printf "--exclude libevent-${LIBEVENT_VERSION}-stable/%s " test configure build-aux m4)) | \
      gpg --assert-signer 2133BC600AB133E1D826D173FE43009C4607B1FB \
          --assert-signer 9E3AC83A27974B84D1B3401DB86086848EF8686D \
          --lock-never --verify <(wget -O - "${URL}.asc") -; \
    cmake -B build -G Ninja \
        -DEVENT__DISABLE_BENCHMARK=ON \
        -DEVENT__DISABLE_DEBUG_MODE=ON \
        -DEVENT__DISABLE_GCC_WARNINGS=ON \
        -DEVENT__DISABLE_REGRESS=ON \
        -DEVENT__DISABLE_SAMPLES=ON \
        -DEVENT__DISABLE_TESTS=ON \
        -DEVENT__LIBRARY_TYPE=STATIC

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --network=none \
    cmake --build build; \
    cmake --install build 

WORKDIR /usr/local/src/tor
ARG TOR_VERSION

RUN --mount=target=/opt/zlib,source=/opt/zlib,from=builder-zlib \
    URL="https://dist.torproject.org/tor-$TOR_VERSION.tar.gz"; \
    wget -O - "$URL" | tee >(tar -xzo --strip-components 1 $(printf "--exclude tor-${TOR_VERSION}/%s " ChangeLog ReleaseNotes)) | \
      sha256sum -c <(wget -O - "${URL}.sha256sum" | \
        tee >(gpg --assert-signer 514102454D0A87DB0767A1EBBE6A0531C18A9179 \
                  --assert-signer B74417EDDF22AC9F9E90F49142E86A2A11F48D36 \
                  --assert-signer 2133BC600AB133E1D826D173FE43009C4607B1FB \
                  --lock-never --verify <(wget -O - "${URL}.sha256sum.asc") -) | \
                awk '{print $1 " -"}'); \
    ./configure \
        --sysconfdir=/etc \
        --localstatedir=/var \
        --disable-dependency-tracking \
        --enable-gpl \
        --enable-static-tor \
        --disable-unittests \
        --enable-pic \
        --disable-manpage \
        --disable-html-manual \
        --disable-asciidoc \
        --disable-gcc-warnings-advisory \
        --disable-gcc-hardening \
        --disable-linker-hardening \
        --disable-module-relay \
        --disable-module-dirauth \
        --with-zlib-dir=/opt/zlib/lib \
        --with-libevent-dir=/usr/local/lib \
        --with-openssl-dir=/usr/local/lib; \
    find -type f -name '*Makefile*' -exec sed -i \
      's/\(^\|[^[:alnum:]_-]\)-static\($\|[^[:alnum:]=_-]\)/\1-static-pie\2/' '{}' \+

RUN --mount=target=/opt/zlib,source=/opt/zlib,from=builder-zlib \
    --mount=type=cache,target=/var/ccache,sharing=locked \
    --network=none \
    make -j$(nproc) src/app/tor; \
    install -Dm755 -s src/app/tor -t /

FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

USER root

COPY --from=builder /tor /usr/bin/

RUN --mount=target=/lib/ld-musl-x86_64.so.1,source=/lib/ld-musl-x86_64.so.1,from=builder \
    --mount=target=/lib/libcap.so.2,source=/usr/lib/libcap.so.2,from=supplementary \
    --mount=target=/usr/local/sbin/busybox,source=/bin/busybox,from=supplementary \
    --mount=target=/usr/local/sbin/setcap,source=/usr/sbin/setcap,from=supplementary \
    ["busybox", "sh", "-eCuxo", "pipefail", "-c", "\
      setcap cap_net_bind_service=+ep /usr/bin/tor; \
      busybox install -Dd -o nonroot -g nonroot -m750 /var/lib/tor; \
      busybox install -Dd -g nonroot -m750 /etc/tor; \
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
