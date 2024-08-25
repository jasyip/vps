ARG CADDY_VERSION
ARG DISTROLESS_SUFFIX
FROM caddy:${CADDY_VERSION}-builder-alpine AS builder-base

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add moreutils gpg gpg-agent \
            ccache gcc make mold \
            libc-dev fortify-headers libcap-setcap && \
    find /usr/lib/ccache/bin -type l -exec ln -s \{\} /usr/local/bin \;

COPY ccache.conf /etc/

FROM builder-base AS builder-other

ARG BUSYBOX_VERSION
ARG CFLAGS
ARG LDFLAGS

WORKDIR /usr/local/src/busybox
RUN --mount=target=busybox-setup.sh,ro,source=busybox-setup.sh \
    --mount=target=busybox-config.sh,ro,source=busybox-config.sh \
    . busybox-setup.sh

RUN --mount=type=cache,target=/var/ccache \
    --mount=target=entrypoint.c,source=entrypoint.c \
    --network=none \
    mold -run make busybox && make install && \
    exec cc $CFLAGS -s -static-pie -o /entrypoint entrypoint.c

FROM builder-base AS builder

ARG CROWDSEC_BOUNCER_VERSION
ARG DNS_IP_RANGE_VERSION
ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/var/ccache \
    --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    XCADDY_GO_BUILD_FLAGS="-ldflags='-w -s -linkmode=external -extldflags=-static-pie' -buildmode=pie -trimpath" \
    XCADDY_SKIP_CLEANUP=0 XCADDY_SUDO=0 \
    CGO_ENABLED=1 CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec mold -run xcaddy build \
    --with "github.com/hslatman/caddy-crowdsec-bouncer@${CROWDSEC_BOUNCER_VERSION}" \
    --with "github.com/fvbommel/caddy-dns-ip-range@${DNS_IP_RANGE_VERSION}"


FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:latest

COPY --from=builder /usr/bin/caddy /usr/bin/
COPY --from=builder-other /busybox/bin/busybox /usr/sbin/
COPY --from=builder-other /entrypoint /usr/bin/

RUN --mount=target=/lib/libcap.so.2,source=/usr/lib/libcap.so.2,from=builder \
    --mount=target=/lib/ld-musl-x86_64.so.1,source=/lib/ld-musl-x86_64.so.1,from=builder \
    --mount=target=/usr/sbin/busybox,source=/bin/busybox,from=builder \
    --mount=target=/usr/sbin/setcap,source=/usr/sbin/setcap,from=builder \
     ["busybox", "sh", "-c", \
      "cd /usr/sbin && \
       busybox ln -s busybox tail && \
       busybox ln -s busybox tee && \
       setcap cap_net_bind_service=+ep /usr/bin/caddy && \
       busybox mkdir -p /var/log/caddy \
      " \
     ]

COPY mta-sts.txt /run/files/
COPY Caddyfile /etc/caddy/
COPY site/ /srv/

ENTRYPOINT ["entrypoint", "/run/files/mta-sts.txt"]
CMD ["run", \
     "--config", \
     "/etc/caddy/Caddyfile", \
     "--adapter", \
     "caddyfile" \
    ]

VOLUME /data

ENV XDG_CONFIG_HOME /config
ENV XDG_DATA_HOME /data

EXPOSE 80 443 443/udp 2019

WORKDIR /srv
