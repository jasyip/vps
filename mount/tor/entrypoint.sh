#!/bin/sh

set -eu

echo "${TOR_DOMAIN:?\$TOR_DOMAIN is not set}" > /var/lib/tor/hostname

for i in public secret; do
  FILE_NAME="hs_ed25519_${i}_key"
  LINK_NAME="/var/lib/tor/${FILE_NAME}"
  [ -h "$LINK_NAME" ] || ln -s "/run/secrets/$FILE_NAME" "$LINK_NAME"
done

exec tor -f /etc/tor/torrc "$@"
