ARG CADDY_VERSION
FROM caddy:${CADDY_VERSION}-builder-alpine AS builder

ARG CADDY_VERSION
RUN --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/go/pkg/mod \
    XCADDY_SKIP_CLEANUP=0 XCADDY_SUDO=0 xcaddy build \
    --with github.com/hslatman/caddy-crowdsec-bouncer@v0.3.1 \
    --with github.com/yroc92/postgres-storage@276797a

FROM caddy:${CADDY_VERSION}-alpine
# Just copy the config files, no need for volume!
# VOLUME /config
VOLUME /data

COPY --from=builder /usr/bin/caddy /usr/bin/


COPY Caddyfile /etc/caddy/
COPY site/ /srv/
