ARG CARGO_CHEF_VERSION
FROM lukemathwalker/cargo-chef:$CARGO_CHEF_VERSION AS chef
WORKDIR /app


FROM busybox:musl as source
ARG MAIL_SERVER_VERSION
RUN mkdir /source && \
    wget -qO - \
        "https://github.com/stalwartlabs/mail-server/archive/refs/tags/${MAIL_SERVER_VERSION}.tar.gz" | \
        tar -xzf - -C /source --strip-components 1


FROM chef AS planner
COPY --from=source /source .
RUN cargo chef prepare --recipe-path recipe.json


FROM chef AS builder 
COPY --from=planner /app/recipe.json recipe.json

# Build dependencies - this is the caching Docker layer!
ARG RUSTFLAGS="-C link-arg=-fuse-ld=mold"
RUN --mount=type=cache,target=/app/target \
    apt-get update -y && \
    apt-get install -y --no-install-recommends --no-upgrade \
        libcap2-bin busybox \
        protobuf-compiler mold make \
        libfindbin-libs-perl && \
    apt-get clean autoclean && apt-get autoremove --yes && \
    bash -c 'rm -rf /var/lib/{apt,dpkg,cache,log}' && \
    RUSTFLAGS="$RUSTFLAGS" cargo chef cook --release --locked \
        --no-default-features --features=postgres \
        --recipe-path recipe.json
# Build application
COPY --from=source /source .
RUN --mount=type=cache,target=/app/target \
    --network=none \
    RUSTFLAGS="$RUSTFLAGS" cargo build --release \
        --locked --no-default-features --features=postgres \
        -p mail-server -p stalwart-cli && \
    find /app/target/release/stalwart-* -executable -exec \
        install -Dm755 -t /app/binaries '{}' \+

ARG DISTROLESS_SUFFIX
FROM gcr.io/distroless/cc${DISTROLESS_SUFFIX}:nonroot

COPY --from=builder \
    /app/binaries/ \
    /bin/busybox \
    /bin/find \
    /sbin/setcap \
    /bin/

COPY --from=builder \
    /lib/x86_64-linux-gnu/libcap.so.* \
    /lib/x86_64-linux-gnu/libpsx.so.* \
    /lib/x86_64-linux-gnu/libselinux.so.* \
    /lib/x86_64-linux-gnu/libpcre2-8.so.* \
    /lib/

SHELL ["busybox", "sh", "-c"]
USER root
COPY ./etc/ /opt/stalwart-mail/etc/
RUN --network=none \
    echo /bin/stalwart-* | busybox xargs -n 1 setcap cap_net_bind_service=+ep && \
    busybox chown nonroot /opt/stalwart-mail && \
    find /opt/stalwart-mail/etc -type d -exec busybox chmod 755 '{}' \+ \
        -o -type f -exec busybox chmod 644 '{}' \+ && \
    busybox rm /bin/busybox /bin/find /bin/setcap \
        /lib/libcap.so.* /lib/libpsx.so.* \
        /lib/libselinux.so.* /lib/libpcre2-8.so.*
SHELL [""]

USER nonroot

VOLUME [ "/opt/stalwart-mail" ]
ENTRYPOINT [ "stalwart-mail", "--config", "/opt/stalwart-mail/etc/config.toml" ]
EXPOSE 8080 25 587 465 143 993 4190
