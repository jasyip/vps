ARG GO_BUILDER_VERSION
FROM golang:${GO_BUILDER_VERSION} AS builder

WORKDIR /go/src/exporter
ARG CFLAGS="-O2 -march=native -D_FORTIFY_SOURCE=2 -ftrivial-auto-var-init=pattern -fstack-protector-strong -fstack-clash-protection -fcf-protection=full -flto -fPIE -pie"
ARG LDFLAGS="-Wl,-O1,--sort-common,-z,relro,-z,now"
ARG OPENRC_EXPORTER_VERSION

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/var/cache/apk,sharing=locked \
    PKGS="openrc-dev openrc-static gcc libc-dev" && \
    apk add $PKGS && \
    wget -qO - "https://git.sr.ht/~tomleb/openrc-exporter/archive/${OPENRC_EXPORTER_VERSION}.tar.gz" | \
        tar -xzf - --strip-components 1 && \
    cd cmd/openrc-exporter && \
    exec go mod download

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS" \
    exec go build -ldflags="-s -w -linkmode=external -extldflags=-static-pie" -trimpath -buildmode=pie -o /openrc-exporter ./cmd/openrc-exporter

FROM scratch

COPY --from=builder /openrc-exporter /

COPY <<EOF /etc/passwd
nobody:x:65534:65534:nobody:/:/sbin/nologin
EOF

USER nobody

VOLUME /run/openrc /etc/conf.d /etc/init.d
ENTRYPOINT ["/openrc-exporter"]
EXPOSE 9816
