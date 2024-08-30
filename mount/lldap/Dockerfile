# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: GPL-3.0-only

ARG MUSLRUST_VERSION
ARG DISTROLESS_SUFFIX
FROM clux/muslrust:${MUSLRUST_VERSION} AS builder

SHELL ["bash", "-eCuxo", "pipefail", "-c"]

WORKDIR /app
RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' >| \
      /etc/apt/apt.conf.d/keep-cache; \
    apt-get update; \
    exec apt-get install -y --no-install-recommends libssl-dev wget brotli zstd pigz

ARG SCCACHE_VERSION

RUN wget -O - "https://github.com/mozilla/sccache/releases/download/v$SCCACHE_VERSION/sccache-v${SCCACHE_VERSION}-x86_64-unknown-linux-musl.tar.gz" | \
      tar -C /usr/local/bin -xzof - --strip-components 1 "sccache-v${SCCACHE_VERSION}-x86_64-unknown-linux-musl/sccache"

COPY sccache.conf /root/.config/sccache/config

ARG LLDAP_VERSION
RUN --mount=target=/Cargo.lock.patch,source=Cargo.lock.patch \
    wget -O - \
        "https://github.com/lldap/lldap/archive/refs/tags/v${LLDAP_VERSION}.tar.gz" | \
        tar -xzof - --strip-components 1; \
    echo /*.patch | xargs -n 1 patch -p0 -i

ARG RUSTFLAGS
ARG CARGO_BUILD_TARGET=x86_64-unknown-linux-musl
# Cannot cache build target due to hard link requirements by rustup
# unfortunately, so must 
RUN --mount=type=cache,target=/var/sccache \
    --mount=type=cache,target=/root/.cargo/registry/cache,sharing=locked \
    --mount=type=cache,target=/tmp/cargo/wasm-pack \
    RUSTC_WRAPPER=sccache RUSTFLAGS="-C strip=symbols" \
    cargo install --color always --locked --no-track --target-dir /tmp/cargo/wasm-pack --bin wasm-pack wasm-pack; \
    cargo fetch --color always --locked; \
    cd app/static; \
    rustup target add wasm32-unknown-unknown; \
    xargs -a libraries.txt wget --no-hsts -nv --; rm libraries.txt; \
    xargs -a fonts/fonts.txt wget --no-hsts -nv -P fonts --; rm fonts/fonts.txt; \
    mkdir /data

RUN --mount=type=cache,target=/var/sccache \
    --mount=type=cache,target=/app/target \
    --mount=type=cache,target=/root/.cargo/registry/cache,ro \
    --network=none \
    RUSTC_WRAPPER=sccache cargo build --color always --release --frozen --bins \
        -p lldap -p lldap_migration_tool -p lldap_set_password; \
    find /app/target/**/release/lldap* ! -name '*.*' -executable -exec \
        install -Dm755 -s -t /app/bin '{}' \+

RUN --mount=type=cache,target=/var/sccache \
    --mount=type=cache,target=/app/target \
    --mount=type=cache,target=/root/.cache/.wasm-pack \
    --mount=type=cache,target=/root/.cargo/registry/cache,sharing=locked \
    RUSTC_WRAPPER=sccache RUSTFLAGS="-C strip=symbols" \
    wasm-pack build -t web --release --no-typescript app --color always --frozen --bins; \
    ( cd app/pkg; rm .gitignore package.json ); \
    mv -f app/index_local.html app/index.html; \
    for i in js wasm css html; do \
        find app -type f -name "*.$i" -exec sh -c \
            'brotli -Zf -- "$@" && zstdmt -19 -f -- "$@" && pigz -9kf -- "$@"' \
            sh \{\} \+ || exit; \
    done

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
