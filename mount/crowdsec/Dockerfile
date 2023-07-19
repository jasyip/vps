ARG CROWDSEC_VERSION
FROM crowdsecurity/crowdsec:${CROWDSEC_VERSION}

HEALTHCHECK CMD wget -q --spider localhost:8080/health

COPY ./config.yaml.local /etc/crowdsec/
COPY ./acquis.d/ /etc/crowdsec/acquis.d/
