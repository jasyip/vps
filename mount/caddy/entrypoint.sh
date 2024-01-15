#!/bin/sh

set -eu

echo "$MX_SUBDOMAINS" | \
      awk '{for(i=1;i<=NF;++i) { print "mx: " $i "." ENVIRON["DOMAIN"] }}' \
      >> /run/files/mta-sts.txt

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile $@
