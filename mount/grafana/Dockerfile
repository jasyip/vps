# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: AGPL-3.0-only

ARG GRAFANA_VERSION
FROM grafana/grafana-oss:${GRAFANA_VERSION}

ARG GF_UID="472"
USER root
RUN apk del --no-cache --no-network --purge \
      apk-tools libcap curl libc-utils musl-utils && \
    rm -rf /etc/apk /lib/apk /usr/share/apk /var/lib/apk /var/cache/apk
USER "$GF_UID"

HEALTHCHECK CMD wget -q --spider localhost:3000/api/health || exit 1

COPY grafana.ini /etc/grafana/
