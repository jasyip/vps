ARG MUSLRUST_VERSION
ARG DISTROLESS_SUFFIX
FROM clux/muslrust:${MUSLRUST_VERSION}-stable AS builder

WORKDIR /app
ARG LLDAP_VERSION
RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=target=/Cargo.lock.patch,source=Cargo.lock.patch \
    # --mount=target=/any_encoding.patch,source=any_encoding.patch \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > \
      /etc/apt/apt.conf.d/keep-cache && \
    apt-get update && \
    apt-get install -y --no-install-recommends libssl-dev make brotli zstd gzip wget && \
    wget -qO - \
        "https://github.com/lldap/lldap/archive/refs/tags/v${LLDAP_VERSION}.tar.gz" | \
        tar -xzf - --strip-components 1 && \
    patch -p0 -i /*.patch

ARG RUSTFLAGS
ARG CARGO_BUILD_TARGET=x86_64-unknown-linux-musl
# Cannot cache build target due to hard link requirements by rustup
# unfortunately, so must 
RUN --mount=type=cache,target=/root/.cargo/registry/cache \
    --mount=type=cache,target=/tmp/cargo/wasm-pack \
    RUSTFLAGS="-C strip=symbols" cargo install --color always --locked --no-track --target-dir /tmp/cargo/wasm-pack --bin wasm-pack wasm-pack && \
    cargo fetch --color always --locked && \
    cd app/static && \
    rustup target add wasm32-unknown-unknown && \
    xargs -a libraries.txt wget --no-hsts -nv -- && rm libraries.txt && \
    xargs -a fonts/fonts.txt wget --no-hsts -nv -P fonts -- && rm fonts/fonts.txt

RUN --mount=type=cache,target=/app/target \
    --mount=type=cache,target=/root/.cargo/registry/cache \
    --network=none \
    cargo build --color always --release --frozen --bins \
        -p lldap -p lldap_migration_tool -p lldap_set_password && \
    find /app/target/**/release/lldap* ! -name '*.*' -executable -exec \
        install -Dm755 -s -t /app/bin '{}' \+

RUN --mount=type=cache,target=/app/target \
    --mount=type=cache,target=/root/.cache/.wasm-pack \
    --mount=type=cache,target=/root/.cargo/registry/cache \
    RUSTFLAGS="-C strip=symbols" wasm-pack build -t web --release --no-typescript app --color always --frozen --bins && \
    ( cd app/pkg && rm .gitignore package.json ) && \
    mv -f app/index_local.html app/index.html && \
    for i in js wasm css html; do \
        find app -type f -name "*.$i" -exec sh -c \
            'brotli -Zf -- "$@" && zstd -9f -- "$@" && gzip -9kf -- "$@"' \
            sh \{\} \+ || exit; \
    done && \ 
    mkdir /data

FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:nonroot

WORKDIR /app

COPY --from=builder /app/app/index.html* app/
COPY --from=builder /app/app/static app/static
COPY --from=builder /app/app/pkg app/pkg
COPY --from=builder /app/bin/lldap /app/bin/lldap_migration_tool /app/bin/lldap_set_password ./
COPY --from=builder --chown=nonroot:nonroot /data /data

COPY ./lldap_config.toml /data/

EXPOSE 3890 17170

ENTRYPOINT ["/app/lldap"]
CMD ["run", "--config-file", "/data/lldap_config.toml"]
HEALTHCHECK CMD ["/app/lldap", "healthcheck", "--config-file", "/data/lldap_config.toml"]
