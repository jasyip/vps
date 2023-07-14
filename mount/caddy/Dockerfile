ARG CADDY_VERSION
FROM caddy:${CADDY_VERSION}-builder-alpine AS builder

RUN xcaddy build \
    --with github.com/hslatman/caddy-crowdsec-bouncer@v0.2.0 \
    && go clean -x -cache -modcache

ARG CADDY_VERSION=2
FROM caddy:${CADDY_VERSION}-alpine
# Just copy the config files, no need for volume!
# VOLUME /config

COPY --from=builder /usr/bin/caddy /usr/bin/caddy

VOLUME /data

COPY Caddyfile /etc/caddy/
COPY site/ /srv/
