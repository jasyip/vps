FROM lukemathwalker/cargo-chef:latest-rust-1 AS chef
WORKDIR /app


FROM busybox:musl as source
ARG MAIL_SERVER_VERSION
RUN wget -O source.tar.gz \
        "https://github.com/stalwartlabs/mail-server/archive/refs/tags/${MAIL_SERVER_VERSION}.tar.gz" && \
    mkdir /source && \
    tar x -af source.tar.gz -C /source --strip-components 1


FROM chef AS planner
COPY --from=source /source .
RUN cargo chef prepare --recipe-path recipe.json


FROM chef AS builder 
COPY --from=planner /app/recipe.json recipe.json
# Build dependencies - this is the caching Docker layer!
RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/app/target \
    UPDATED=0; \
    while \
        apt-get install -y --no-install-recommends --no-upgrade \
            libcap2-bin busybox protobuf-compiler mold; \
        [ "$UPDATED" -eq 0 ] && [ "$?" -ne 0 ]; \
    do apt-get update -y || exit; \
       UPDATED=1; \
    done; \
    rm -rf /var/cache/apt/* && \
    busybox sh -c "echo -e '[build]\nrustflags = [\"-C\", \"link-arg=-fuse-ld=mold\"]'" | \
        install -D /dev/stdin .cargo/config.toml && \
    cargo chef cook --release \
        --no-default-features --features=postgres \
        --recipe-path recipe.json
# Build application
COPY --from=source /source .
RUN --mount=type=cache,target=/app/target \
    cargo build --release \
        --no-default-features --features=postgres \
        -p mail-server -p stalwart-cli -p stalwart-install && \
    find /app/target/release/stalwart-* -executable -exec \
        install -Dm755 -t /app/binaries '{}' \+


FROM gcr.io/distroless/cc-debian12:nonroot

COPY --from=builder \
    /app/binaries/ \
    /bin/busybox \
    /sbin/setcap \
    /bin/
COPY --from=builder \
    /lib/x86_64-linux-gnu/libcap.so.* \
    /lib/x86_64-linux-gnu/libpsx.so.* \
    /lib/

SHELL ["/bin/busybox", "sh", "-c"]
USER root
RUN echo /bin/stalwart-* | /bin/busybox xargs -n 1 setcap cap_net_bind_service=+ep && \
    /bin/busybox mkdir -p /opt && \
    /bin/busybox rm -f /bin/busybox /bin/setcap \
        /lib/libcap.so.* /lib/libpsx.so.*

SHELL [""]
USER nonroot

COPY ./etc/ /opt/stalwart-mail/etc/

VOLUME [ "/opt/stalwart-mail" ]
ENTRYPOINT [ "/bin/stalwart-mail" ]
EXPOSE 8080 25 587 465 143 993 4190
