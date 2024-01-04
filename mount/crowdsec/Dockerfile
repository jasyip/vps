ARG CROWDSEC_VERSION
FROM crowdsecurity/crowdsec:${CROWDSEC_VERSION}

RUN apk del --no-cache --no-network rsync

EXPOSE 6060
HEALTHCHECK CMD wget -q --spider localhost:8080/health || exit 1

COPY ./config.yaml.local /etc/crowdsec/
COPY ./acquis.d/ /etc/crowdsec/acquis.d/
