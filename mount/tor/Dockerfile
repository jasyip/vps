FROM alpine:latest as source

ARG TOR_VERSION
RUN apk --no-cache add "tor=$TOR_VERSION" libcap && \
    setcap cap_net_bind_service=+ep /usr/bin/tor && \
    apk del --no-cache --no-network --purge apk-tools libcap && \
    rm -fr /etc/apk /lib/apk /usr/share/apk /var/lib/apk /var/cache/apk
# tor user is already added

USER tor

COPY torrc /etc/tor/
COPY --chmod=500 entrypoint.sh /

EXPOSE 9050

VOLUME ["/var/lib/tor"]
ENTRYPOINT ["/entrypoint.sh"]
