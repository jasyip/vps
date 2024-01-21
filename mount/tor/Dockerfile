FROM alpine:latest as source

ARG TOR_VERSION
RUN apk --no-cache add "tor=$TOR_VERSION" libcap && \
    setcap cap_net_bind_service=+ep /usr/bin/tor && \
    apk del --no-cache --no-network --purge apk-tools libcap && \
    rm -fr /etc/apk /lib/apk /usr/share/apk /var/lib/apk /var/cache/apk && \
    for i in hostname hs_ed25519_secret_key hs_ed25519_public_key; do \
      ln -s -t /var/lib/tor "/run/secrets/$i" || exit; \
    done
# tor user is already added

USER tor

COPY torrc /etc/tor/

EXPOSE 9050

VOLUME ["/var/lib/tor"]
ENTRYPOINT ["tor", "-f", "/etc/tor/torrc"]
