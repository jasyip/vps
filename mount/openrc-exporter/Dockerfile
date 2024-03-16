ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder

ARG OPENRC_EXPORTER_VERSION
WORKDIR /usr/src/exporter
RUN apk add openrc-dev openrc-static gcc libc-dev && \
    wget -qO - "https://git.sr.ht/~tomleb/openrc-exporter/archive/${OPENRC_EXPORTER_VERSION}.tar.gz" | \
        tar -xzf - --strip-components 1 && \
    cd cmd/openrc-exporter && CGO_ENABLED=1 GOOS=linux go build -v -ldflags="-extldflags=-static" -o /openrc-exporter

FROM scratch

COPY --from=builder /openrc-exporter /

COPY <<EOF /etc/passwd
nobody:x:65534:65534:nobody:/:/sbin/nologin
EOF

USER nobody

VOLUME /run/openrc /etc/conf.d /etc/init.d
ENTRYPOINT ["/openrc-exporter"]
EXPOSE 9816
