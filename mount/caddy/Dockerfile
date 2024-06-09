ARG CADDY_VERSION
FROM caddy:${CADDY_VERSION}-builder-alpine AS builder

ARG CADDY_VERSION
ARG CROWDSEC_BOUNCER_VERSION
ARG DNS_IP_RANGE_VERSION
RUN --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/go/pkg/mod \
    XCADDY_SKIP_CLEANUP=0 XCADDY_SUDO=0 xcaddy build \
    --with "github.com/hslatman/caddy-crowdsec-bouncer@${CROWDSEC_BOUNCER_VERSION}" \
    --with "github.com/fvbommel/caddy-dns-ip-range@${DNS_IP_RANGE_VERSION}"

COPY ./entrypoint.c /usr/local/src/
RUN apk add --no-cache gcc libc-dev && \
    gcc -Os -s /usr/local/src/entrypoint.c -o /usr/bin/entrypoint && \
    apk del --no-cache gcc libc-dev

FROM caddy:${CADDY_VERSION}-alpine
# Just copy the config files, no need for volume!
# VOLUME /config
VOLUME /data

RUN apk del --no-cache --no-network --purge apk-tools libcap && \
    rm -rf /etc/apk /lib/apk /usr/share/apk /var/lib/apk /var/cache/apk

COPY --from=builder /usr/bin/caddy /usr/bin/entrypoint /usr/bin/


COPY Caddyfile /etc/caddy/
COPY site/ /srv/
COPY mta-sts.txt /run/files/

ENTRYPOINT ["entrypoint", \
            "/run/files/mta-sts.txt", \
            "run", \
            "--config", \
            "/etc/caddy/Caddyfile", \
            "--adapter", \
            "caddyfile" \
           ]
