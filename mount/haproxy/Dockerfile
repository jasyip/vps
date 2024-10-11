ARG ALPINE_VERSION
ARG DISTROLESS_SUFFIX
FROM alpine:$ALPINE_VERSION AS builder-base

SHELL ["/bin/sh", "-eCuxo", "pipefail", "-c"]

# runtime dependencies
RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add \
        ccache \
        gcc \
        mold \
        libc-dev \
        fortify-headers \
        perl \
        make \
        linux-headers \
        readline-dev; \
    find /usr/lib/ccache/bin -type l -exec ln -s \{\} /usr/local/bin \;

COPY ccache.conf /etc/


FROM builder-base AS builder-entrypoint

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add libcap-setcap

ARG CFLAGS
ARG LDFLAGS
WORKDIR /usr/local/src/entrypoint

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --mount=target=entrypoint.c,source=entrypoint.c \
    exec cc $CFLAGS $LDFLAGS -s -static-pie -o /entrypoint entrypoint.c

FROM builder-base AS builder-quictls

ARG CFLAGS
ARG LDFLAGS
ARG QUICTLS_VERSION
WORKDIR /usr/local/src/quictls

RUN wget -O - "https://github.com/quictls/openssl/archive/refs/tags/openssl-${QUICTLS_VERSION}.tar.gz" | \
      tar -xzof - --strip-components 1 $(printf "--exclude openssl-openssl-${QUICTLS_VERSION}/%s " test doc/man3 doc/man7); \
    exec ./Configure \
        linux-x86_64 \
        --prefix="/opt/quictls" \
        --libdir=lib \
        enable-ktls \
        no-async \
        no-autoalginit \
        no-autoerrinit \
        no-cmp \
        no-cms \
        no-ct \
        no-comp \
        no-dso \
        no-ec2m \
        enable-ec_nistp_64_gcc_128 \
        no-engine \
        no-err \
        no-filenames \
        no-gost \
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
    mold -run make -j$(nproc) build_libs; \
    make install_dev


FROM builder-base AS builder-lua

WORKDIR /usr/local/src/lua
ARG LUA_VERSION
RUN checksum="$(wget -O - 'https://www.lua.org/download.html' | \
                  perl -0 -ne 'print "$&" if /(?s)sha256:.+?\K[[:xdigit:]]{64}\b/')"; \
    wget -O - "https://www.lua.org/ftp/lua-${LUA_VERSION}.tar.gz" | tee \
      >(tar -xzf - --strip-components 1 --exclude '*/doc/*.html') | \
      { [ -z "$checksum" ] || sha256sum -c <(echo "$checksum -") ;}

ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --network=none \
    mold -run make -j$(nproc) CFLAGS="$CFLAGS" LDFLAGS="$LDFLAGS" linux; \
    make INSTALL_TOP=/opt/lua install; \
    printf "/opt/lua/%s " bin man share | xargs rm -rf --

FROM builder-base AS builder-pcre2

WORKDIR /usr/local/src/pcre2
ARG PCRE2_VERSION
ARG CFLAGS
ARG LDFLAGS
RUN URL="https://github.com/PCRE2Project/pcre2/releases/download/pcre2-${PCRE2_VERSION}/pcre2-${PCRE2_VERSION}.tar.bz2"; \
    wget -O - "$URL" | tar -xjo --strip-components 1; \
    # wget -O - "$URL" | tee >(tar -xjo --strip-components 1) | \
    #   gpg --verify <(wget -O - "${URL}.sig") -; \
    exec ./configure \
      --prefix=/opt/pcre2 \
      --disable-dependency-tracking \
      --disable-shared \
      --enable-static \
      --enable-jit \
      --enable-year2038

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --network=none \
    mold -run make -j$(nproc) libpcre2-8.la libpcre2-posix.la; \
    make install-libLTLIBRARIES install-includeHEADERS install-nodist_includeHEADERS

FROM builder-base AS builder-zlib

WORKDIR /usr/local/src/zlib
ARG ZLIB_VERSION
RUN wget -O - "https://github.com/zlib-ng/zlib-ng/archive/refs/tags/${ZLIB_VERSION}.tar.gz" | \
      tar -xzo --strip-components 1 $(printf "--exclude zlib-ng-${ZLIB_VERSION}/%s " doc test); \
    exec ./configure --zlib-compat

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --network=none \
    install -Dm644 zlib*.h zconf.h -t /opt/zlib/include; \
    install -Dm644 zlib.pc -t /opt/zlib/lib/pkgconfig;

FROM builder-base AS builder

WORKDIR /usr/local/src/haproxy
ARG HAPROXY_VERSION
RUN URL="https://www.haproxy.org/download/$(echo "$HAPROXY_VERSION" | cut -d . -f -2 \
                                           )/src/haproxy-${HAPROXY_VERSION}.tar.gz"; \
    wget -O - "$URL" | tee >(tar -xzf - --strip-components 1 $(printf "--exclude haproxy-${HAPROXY_VERSION}/%s " '.*' doc reg-tests tests CHANGELOG)) | \
      sha256sum -c <(wget -O - "${URL}.sha256" | awk '{print $1 " -"}')

ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --mount=target=/mnt/quictls,source=/opt/quictls,from=builder-quictls \
    --mount=target=/mnt/lua,source=/opt/lua,from=builder-lua \
    --mount=target=/mnt/pcre2,source=/opt/pcre2,from=builder-pcre2 \
    --mount=target=/mnt/zlib,source=/opt/zlib,from=builder-zlib \
    --network=none \
    mold -run make -j$(nproc) \
                   TARGET=linux-musl VERSION="$HAPROXY_VERSION" \
                   OPT_CFLAGS= ARCH_FLAGS= WARN_CFLAGS= \
                   CFLAGS="$CFLAGS -I/mnt/quictls/include -I/mnt/zlib/include -I/mnt/pcre2/include" \
                   LDFLAGS="$LDFLAGS -L/mnt/quictls/lib -L/mnt/pcre2/lib -static-pie" \
                   USE_OPENSSL=1 USE_SLZ=1 \
                   USE_PCRE2=1 USE_PCRE2_JIT=1 USE_STATIC_PCRE2=1 PCRE2_LDFLAGS="-lpcre2-8 -lpcre2-posix" \
                   USE_LUA=1 LUA_LIB_NAME=lua LUA_INC=/mnt/lua/include LUA_LIB=/mnt/lua/lib \
                   USE_QUIC=1 \
                   USE_PROMEX=1; \
    strip haproxy

FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:latest

COPY --from=builder /usr/local/src/haproxy/haproxy /usr/bin/
COPY --from=builder-entrypoint /entrypoint /usr/bin/

RUN --mount=target=/lib/libcap.so.2,source=/usr/lib/libcap.so.2,from=builder-entrypoint \
    --mount=target=/lib/ld-musl-x86_64.so.1,source=/lib/ld-musl-x86_64.so.1,from=builder-entrypoint \
    --mount=target=/usr/sbin/setcap,source=/usr/sbin/setcap,from=builder-entrypoint \
    ["setcap", "cap_net_bind_service=+ep", "/usr/bin/haproxy"]

COPY mta-sts.txt /run/files/
COPY haproxy.cfg /usr/local/etc/haproxy/
COPY site /srv

STOPSIGNAL SIGUSR1
ENTRYPOINT ["entrypoint"]
CMD ["haproxy", "-f", "/usr/local/etc/haproxy/haproxy.cfg"]
