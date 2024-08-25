ARG ALPINE_VERSION
ARG DISTROLESS_SUFFIX
FROM alpine:$ALPINE_VERSION AS builder

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    exec apk add ccache g++ mold make cmake pkgconfig libc-dev fortify-headers patch \
        flex bison \
        openssl-dev openssl-libs-static \
        boost-dev boost1.84-static \
        cppzmq libzmq-static \
        libsodium-dev libsodium-static \
        zeromq-dev \
        rapidjson-dev

COPY ccache.conf /etc/

RUN find /usr/lib/ccache/bin -type l -exec ln -s \{\} /usr/local/bin \;

ARG CFLAGS
ARG LDFLAGS

ARG LIBEXPAT_VERSION
WORKDIR /usr/local/src/libexpat
RUN wget -qO - "https://github.com/libexpat/libexpat/releases/download/R_$(echo "$LIBEXPAT_VERSION" | tr . _)/expat-$LIBEXPAT_VERSION.tar.xz" | \
      tar -xJof - --strip-components 1 && \
    CFLAGS="$CFLAGS -fno-lto" exec ./configure \
        --prefix=/usr/local \
        --disable-maintainer-mode \
        --disable-shared \
        --enable-static \
        --without-examples \
        --with-pic \
        --without-tests \
        --without-docbook

RUN --mount=type=cache,target=/var/ccache \
    --network=none \
    exec mold -run make -j$(nproc) install

ARG LIBUNBOUND_VERSION
RUN wget -qO - "https://github.com/NLnetLabs/unbound/archive/refs/tags/release-${LIBUNBOUND_VERSION}.tar.gz" | \
      tar -xzof - --strip-components 1 && \
    CFLAGS="$CFLAGS -fno-lto" exec ./configure \
        --prefix=/usr/local \
        --enable-pie \
        --enable-relro-now \
        --disable-shared \
        --enable-static \
        --disable-dsa \
        --disable-gost \
        --with-libexpat=/usr/local \
        --with-pthreads \
        --enable-subnet \
        --with-ssl \
        --with-pic \
        --with-libunbound-only \
        --disable-flto

RUN --mount=type=cache,target=/var/ccache \
    --network=none \
    exec mold -run make -j$(nproc) install


WORKDIR /usr/local/src/monerod

ARG MONEROD_VERSION

RUN --mount=target=/CMakeLists.txt.patch,ro,source=CMakeLists.txt.patch \
    --mount=target=/version-string.patch,ro,source=version-string.patch \
    wget -qO - "https://downloads.getmonero.org/cli/monero-source-v${MONEROD_VERSION}.tar.bz2" | \
      tar -xjof - --strip-components 1 && \
    patch -p1 -i /version-string.patch && \
    patch -p0 -i /CMakeLists.txt.patch && \
    mkdir -p /.bitmonero && \
    export CFLAGS="$CFLAGS -fno-lto" && \
    CXXFLAGS="$CFLAGS" \
    exec cmake -B build/release \
          -DCMAKE_BUILD_TYPE=None \
          -DCMAKE_INSTALL_PREFIX=/usr/local \
          -DSTATIC=ON \
          -DSTRIP_TARGETS=ON \
          -DBUILD_DOCUMENTATION=OFF \
          -DSTACK_TRACE=OFF \
          -DMANUAL_SUBMODULES=1 \
          -DUSE_DEVICE_TREZOR=OFF \
          -DUPNPC_BUILD_SHARED=OFF \
          -DUSE_READLINE=OFF


RUN --mount=type=cache,target=/var/ccache \
    --network=none \
    mold -run make -C build/release -j$(nproc) daemon && \
    install -m755 -s build/release/bin/monerod -t /usr/local/bin/

FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

COPY --from=builder --chown=nonroot:nonroot /.bitmonero /home/nonroot/.bitmonero
COPY --from=builder /usr/local/bin/monerod /usr/bin/


# Contains the blockchain
VOLUME /home/nonroot/.bitmonero

EXPOSE 18080 18081

ENTRYPOINT ["monerod"]
CMD ["--p2p-bind-ip=0.0.0.0", "--p2p-bind-port=18080", "--rpc-bind-ip=0.0.0.0", "--rpc-bind-port=18081", "--non-interactive", "--confirm-external-bind"]
