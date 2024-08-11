# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: GPL-2.0-only

ARG CADDY_VERSION
FROM caddy:${CADDY_VERSION}-builder-alpine AS builder-base

RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add gcc make mold libc-dev fortify-headers libcap-setcap

FROM builder-base AS builder-other

ARG BUSYBOX_VERSION
ARG CFLAGS
ARG LDFLAGS

WORKDIR /usr/local/src/busybox

RUN wget -qO - "https://busybox.net/downloads/busybox-${BUSYBOX_VERSION}.tar.bz2" | \
        tar -xkjf - --strip-components 1 && \
    sed -i 's/\(^\|[^[:alnum:]_-]\)-static\($\|[^[:alnum:]=_-]\)/\1-static-pie\2/' Makefile.flags && \
    make allnoconfig && \
    sleep 1 && \
    sed -i 's/^.*\(CONFIG_\(STATIC\|INSTALL_NO_USR\|DESKTOP\|LONG_OPTS\|SH_IS_NONE\|INSTALL_APPLET_SYMLINKS_NONE\|TAIL\|TEE\|FEATURE_TEE_USE_BLOCK_IO\)\)[ =].*$/\1=y/' .config && \
    sed -i 's/^.*\(CONFIG_\(SH_IS_ASH\|INSTALL_APPLET_SYMLINKS\)\)[ =].*$/\1=n/' .config && \
    sed -i 's%^.*\(CONFIG_PREFIX\)[ =].*$%\1="/busybox"%' .config && \
    sed -i "s%^.*\(CONFIG_EXTRA_CFLAGS\)[ =].*$%\1=\"$CFLAGS\"%" .config && \
    sed -i "s%^.*\(CONFIG_EXTRA_LDFLAGS\)[ =].*$%\1=\"$LDFLAGS\"%" .config

RUN --mount=target=entrypoint.c,source=entrypoint.c \
    --network=none \
    mold -run make busybox && \
    mold -run make install && \
    exec cc $CFLAGS -s -static-pie -o /entrypoint entrypoint.c

FROM builder-base AS builder

ARG CROWDSEC_BOUNCER_VERSION
ARG DNS_IP_RANGE_VERSION
ARG CFLAGS
ARG LDFLAGS

RUN --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/go/pkg/mod \
    XCADDY_GO_BUILD_FLAGS="-ldflags='-w -s -linkmode=external -extldflags=-static-pie' -buildmode=pie -trimpath" \
    XCADDY_SKIP_CLEANUP=0 XCADDY_SUDO=0 \
    CGO_ENABLED=1 CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec mold -run xcaddy build \
    --with "github.com/hslatman/caddy-crowdsec-bouncer@${CROWDSEC_BOUNCER_VERSION}" \
    --with "github.com/fvbommel/caddy-dns-ip-range@${DNS_IP_RANGE_VERSION}"


ARG DISTROLESS_SUFFIX
FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:latest

COPY --from=builder /usr/bin/caddy /bin/
COPY --from=builder-other /entrypoint /busybox/bin/busybox /bin/

RUN --mount=target=/lib/libcap.so.2,source=/usr/lib/libcap.so.2,from=builder \
    --mount=target=/lib/ld-musl-x86_64.so.1,source=/lib/ld-musl-x86_64.so.1,from=builder \
    --mount=target=/busybox,source=/bin/busybox,from=builder \
    --mount=target=/bin/setcap,source=/usr/sbin/setcap,from=builder \
     ["/busybox", "sh", "-c", \
      "cd /bin && \
       /busybox ln -s busybox tail && \
       /busybox ln -s busybox tee && \
       setcap cap_net_bind_service=+ep /bin/caddy && \
       /busybox mkdir -p /var/log/caddy \
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
