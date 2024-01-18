ARG CROWDSEC_VERSION
FROM crowdsecurity/crowdsec:${CROWDSEC_VERSION}

RUN apk add --no-network --no-cache ca-certificates-bundle && \
    apk del --no-cache --no-network --purge apk-tools rsync && \
    rm -rf /etc/apk /lib/apk /usr/share/apk /var/lib/apk /var/cache/apk

EXPOSE 6060
HEALTHCHECK CMD wget -q --spider localhost:8080/health || exit 1

COPY ./config.yaml.local /etc/crowdsec/
COPY ./acquis.d/ /etc/crowdsec/acquis.d/
