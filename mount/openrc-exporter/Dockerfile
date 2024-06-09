ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder

ARG OPENRC_EXPORTER_VERSION
WORKDIR /go/src/exporter
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/var/cache/apk \
    PKGS="openrc-dev openrc-static gcc libc-dev" && \
    apk add $PKGS && \
    wget -qO - "https://git.sr.ht/~tomleb/openrc-exporter/archive/${OPENRC_EXPORTER_VERSION}.tar.gz" | \
        tar -xzf - --strip-components 1 && \
    cd cmd/openrc-exporter && \
    CGO_CPPFLAGS="-D_FORTIFY_SOURCE=2 -ftrivial-auto-var-init=pattern -fstack-protector-strong -fstack-clash-protection -fcf-protection=full" \
    CGO_LDFLAGS="-Wl,-O1,--sort-common,-z,relro,-z,now" \
    go build -ldflags="-s -w -linkmode=external -extldflags=-static-pie" -trimpath -buildmode=pie -o /openrc-exporter . && \
    apk del $PKGS && rm -rf *

FROM scratch

COPY --from=builder /openrc-exporter /

COPY <<EOF /etc/passwd
nobody:x:65534:65534:nobody:/:/sbin/nologin
EOF

USER nobody

VOLUME /run/openrc /etc/conf.d /etc/init.d
ENTRYPOINT ["/openrc-exporter"]
EXPOSE 9816
