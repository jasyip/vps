ARG ALPINE_VERSION
ARG DISTROLESS_SUFFIX
FROM alpine:$ALPINE_VERSION AS builder-base

SHELL ["/bin/sh", "-eCuxo", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add gpg gpg-agent \
        ccache g++ mold make cmake samurai pkgconf patch \
        file perl \
        libc-dev fortify-headers \
        flex bison \
        cppzmq \
        boost-dev boost1.84-static \
        rapidjson-dev; \
    find /usr/lib/ccache/bin -type l -exec ln -s \{\} /usr/local/bin \;

COPY ccache.conf /etc/

RUN exec gpg --fetch-keys \
             'https://keys.openpgp.org/vks/v1/by-fingerprint/BA5473A2B0587B07FB27CF2D216094DFD0CB81EF' \
             'https://download.pureftpd.org/public_keys/jedi.gpg.asc' \
             'https://keys.openpgp.org/vks/v1/by-fingerprint/3176EF7DB2367F1FCA4F306B1F9B0E909AF37285' \
             'https://keys.openpgp.org/vks/v1/by-fingerprint/EDFAA3F2CA4E6EB05681AF8E9F6F1C2D7E045F8D' \
             'https://raw.githubusercontent.com/monero-project/monero/master/utils/gpg_keys/binaryfate.asc'


FROM builder-base AS builder-openssl

WORKDIR /usr/local/src/openssl
ARG OPENSSL_VERSION
ARG CFLAGS
ARG LDFLAGS

RUN URL="https://github.com/openssl/openssl/releases/download/openssl-${OPENSSL_VERSION}/openssl-${OPENSSL_VERSION}.tar.gz"; \
    wget -O - "$URL" | tee >(tar -xzo --strip-components 1 $(printf "--exclude openssl-${OPENSSL_VERSION}/%s " test doc/man3 doc/man7)) \
      >(gpg --assert-signer BA5473A2B0587B07FB27CF2D216094DFD0CB81EF \
            --lock-never --verify <(wget -O - "${URL}.asc") -) | \
      sha256sum -c <(wget -O - "${URL}.sha256" | awk '{print $1 " -"}'); \
    exec ./Configure \
        linux-x86_64 \
        --prefix=/opt/openssl \
        --libdir=lib \
        enable-ktls \
        no-apps \
        no-async \
        no-autoalginit \
        no-autoerrinit \
        no-capieng \
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


FROM builder-base AS builder-libsodium-zeromq

WORKDIR /usr/local/src/libsodium
ARG LIBSODIUM_VERSION
ARG CFLAGS
ARG LDFLAGS
RUN URL="https://download.libsodium.org/libsodium/releases/libsodium-${LIBSODIUM_VERSION}.tar.gz"; \
    wget -O - "$URL" | tee \
      >(tar -xzo --strip-components 1 $(printf "--exclude libsodium-${LIBSODIUM_VERSION}/%s " builds/msvc 'test/default/*.c')) | \
      gpg --assert-signer 210627AABA709FE1 \
          --lock-never --verify <(wget -O - "${URL}.sig") - || true; \
    exec ./configure \
      --prefix=/opt/libsodium \
      --disable-dependency-tracking \
      --disable-ssp \
      --enable-opt \
      --disable-shared \
      --with-pthreads

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --network=none \
    make -j$(nproc); \
    make install

WORKDIR /usr/local/src/libzmq
ARG LIBZMQ_VERSION
RUN BASE_URL="https://github.com/zeromq/libzmq/releases/download/v${LIBZMQ_VERSION}"; \
    wget -O - "${BASE_URL}/zeromq-${LIBZMQ_VERSION}.tar.gz" |\
      tee >(tar -xzo --strip-components 1 $(printf "--exclude zeromq-${LIBZMQ_VERSION}/%s " doc perf tests tools unittests ChangeLog)) | \
      sha1sum -c <(wget -O - "${BASE_URL}/SHA1SUMS" | awk '$2 ~ /\.tar\.gz$/ {print $1 " -"}'); \
    CXXFLAGS="$CFLAGS" exec cmake -B build -G Ninja \
         -DCMAKE_INSTALL_PREFIX=/opt/libzmq \
         -DCMAKE_PREFIX_PATH=/opt/libsodium \
         -DBUILD_TESTS=OFF \
         -DBUILD_SHARED=OFF \
         -DWITH_LIBSODIUM=ON \
         -DWITH_LIBSODIUM_STATIC=ON \
         -DWITH_DOC=OFF

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --network=none \
    cmake --build build; \
    cmake --install build


FROM builder-base AS builder-libexpat

WORKDIR /usr/local/src/libexpat
ARG LIBEXPAT_VERSION
ARG CFLAGS
ARG LDFLAGS
RUN URL="https://github.com/libexpat/libexpat/releases/download/R_$(echo "$LIBEXPAT_VERSION" | tr . _\
           )/expat-$LIBEXPAT_VERSION.tar.xz"; \
    wget -O - "$URL" | tee >(tar -xJo --strip-components 1 $(printf "--exclude expat-${LIBEXPAT_VERSION}/%s " fuzz m4 win32)) | \
      gpg --assert-signer CB8DE70A90CFBF6C3BF5CC5696262ACFFBD3AEC6 \
          --lock-never --verify <(wget -O - "${URL}.asc") -; \
    exec ./configure \
        --prefix=/opt/libexpat \
        --disable-maintainer-mode \
        --disable-dependency-tracking \
        --disable-shared \
        --without-xmlwf \
        --without-examples \
        --without-tests \
        --without-docbook

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --network=none \
    make -j$(nproc); \
    make install


FROM builder-base AS builder-libunbound

WORKDIR /usr/local/src/libunbound
ARG CFLAGS
ARG LDFLAGS
ARG LIBUNBOUND_VERSION
RUN --mount=target=/opt/openssl,source=/opt/openssl,from=builder-openssl \
    --mount=target=/opt/libexpat,source=/opt/libexpat,from=builder-libexpat \
    URL="https://www.nlnetlabs.nl/downloads/unbound/unbound-${LIBUNBOUND_VERSION}.tar.gz"; \
    wget -O - "$URL" | tee >(tar -xzo --strip-components 1 $(printf "--exclude unbound-${LIBUNBOUND_VERSION}/%s " 'test*' winrc)) \
      >(gpg --assert-signer EDFAA3F2CA4E6EB05681AF8E9F6F1C2D7E045F8D \
           --lock-never --verify <(wget -O - "${URL}.asc") -) | \
      sha256sum -c <(wget -O - "${URL}.sha256" | awk '{print $1 " -"}'); \
    exec ./configure \
        --prefix=/opt/libunbound \
        --disable-shared \
        --disable-dsa \
        --disable-gost \
        --with-libexpat=/opt/libexpat \
        --with-pthreads \
        --enable-subnet \
        --with-ssl=/opt/openssl \
        --with-libunbound-only

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --mount=target=/opt/openssl,source=/opt/openssl,from=builder-openssl \
    --mount=target=/opt/libexpat,source=/opt/libexpat,from=builder-libexpat \
    --network=none \
    make -j$(nproc) lib; \
    make install-lib


FROM builder-base AS builder

WORKDIR /usr/local/src/monerod
ARG CFLAGS
ARG LDFLAGS
ARG MONEROD_VERSION

RUN --mount=target=/CMakeLists.txt.patch,source=CMakeLists.txt.patch \
    --mount=target=/version-string.patch,source=version-string.patch \
    --mount=target=/opt/libsodium,source=/opt/libsodium,from=builder-libsodium-zeromq \
    --mount=target=/opt/libzmq,source=/opt/libzmq,from=builder-libsodium-zeromq \
    --mount=target=/opt/libexpat,source=/opt/libexpat,from=builder-libexpat \
    --mount=target=/opt/libunbound,source=/opt/libunbound,from=builder-libunbound \
    --mount=target=/opt/openssl,source=/opt/openssl,from=builder-openssl \
    wget -O - "https://downloads.getmonero.org/cli/monero-source-v${MONEROD_VERSION}.tar.bz2" | \
      tee >(tar -xjo --strip-components 1 $(printf "monero-source-v${MONEROD_VERSION}/%s " CMakeLists.txt Makefile contrib cmake external src translations)) | \
          sha256sum -c <(wget -O - "https://www.getmonero.org/downloads/hashes.txt" | \
                          tee >(gpg --assert-signer 81AC591FE9C4B65C5806AFC3F0AF4D462A0BDF92 \
                                   --lock-never --verify) | \
                              awk '$2 ~ /^monero-source.*\.tar\.bz2$/ {print $1 " -"}'); \
    patch -p1 -i /version-string.patch; \
    patch -p0 -i /CMakeLists.txt.patch; \
    mkdir -p /.bitmonero; \
    # https://gitlab.alpinelinux.org/alpine/aports/-/merge_requests/18788
    export CFLAGS="$CFLAGS -fno-lto -fno-ipa-cp $(printf "-I%s " /opt/*/include)"; \
    CXXFLAGS="$CFLAGS" \
    exec cmake -B build -G Ninja \
          -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_INSTALL_PREFIX=/usr/local \
          -DCMAKE_PREFIX_PATH="$(echo /opt/* | tr ' ' \;)" \
          -DSTATIC=ON \
          -DSTRIP_TARGETS=ON \
          -DBUILD_DOCUMENTATION=OFF \
          -DSTACK_TRACE=OFF \
          -DMANUAL_SUBMODULES=1 \
          -DUSE_DEVICE_TREZOR=OFF \
          -DUPNPC_BUILD_SHARED=OFF \
          -DUSE_READLINE=OFF \
          -DUSE_LTO=ON

RUN --mount=type=cache,target=/var/ccache,sharing=locked \
    --mount=target=/opt/libsodium,source=/opt/libsodium,from=builder-libsodium-zeromq \
    --mount=target=/opt/libzmq,source=/opt/libzmq,from=builder-libsodium-zeromq \
    --mount=target=/opt/libexpat,source=/opt/libexpat,from=builder-libexpat \
    --mount=target=/opt/libunbound,source=/opt/libunbound,from=builder-libunbound \
    --mount=target=/opt/openssl,source=/opt/openssl,from=builder-openssl \
    --network=none \
    cmake --build build -t daemon; \
    strip build/bin/monerod


FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

COPY --from=builder --chown=nonroot:nonroot /.bitmonero /home/nonroot/.bitmonero
COPY --from=builder --chmod=755 /usr/local/src/monerod/build/bin/monerod /usr/bin/


# Contains the blockchain
VOLUME /home/nonroot/.bitmonero

EXPOSE 18080 18081

ENTRYPOINT ["monerod"]
CMD ["--p2p-bind-ip=0.0.0.0", "--p2p-bind-port=18080", "--rpc-bind-ip=0.0.0.0", "--rpc-bind-port=18081", "--non-interactive", "--confirm-external-bind"]
