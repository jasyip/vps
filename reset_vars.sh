#!/bin/sh

set -e

FILE="OVMF_VARS.fd"

if [ -f "$FILE" ]; then
  rm "$FILE"
fi
touch "$FILE"
chattr +C "$FILE"
cp "/usr/share/ovmf/x64/$FILE" .
