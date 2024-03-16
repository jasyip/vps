ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS yq-builder

ARG YQ_VERSION
WORKDIR /go/src/mikefarah/yq
RUN wget -qO - "https://github.com/mikefarah/yq/archive/refs/tags/v${YQ_VERSION}.tar.gz" | \
    tar -xzf - --strip-components 1 && CGO_ENABLED=0 go build -o /yq -ldflags=-extldflags=-static .

ARG DISTROLESS_SUFFIX
FROM gcr.io/distroless/static${DISTROLESS_SUFFIX}:debug-nonroot

ARG CROWDSEC_VERSION
SHELL ["/busybox/sh", "-c"]

USER root
COPY --from=crowdsecurity/crowdsec:${CROWDSEC_VERSION} /staging /staging
COPY --from=crowdsecurity/crowdsec:${CROWDSEC_VERSION} /usr/local/bin /usr/local/bin
COPY --from=yq-builder /yq /usr/local/bin/
COPY --chmod=444 ./docker_start.sh /
COPY ./config.yaml.local /etc/crowdsec/
COPY ./acquis.d /etc/crowdsec/acquis.d
RUN chown -R nonroot:nonroot /etc/crowdsec /staging
USER nonroot


EXPOSE 6060
HEALTHCHECK CMD wget -q --spider localhost:8080/health || exit 1
ENTRYPOINT ["sh", "/docker_start.sh"]
VOLUME /etc/crowdsec /var/lib/crowdsec/data /var/log
