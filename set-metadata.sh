#!/bin/sh

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root" >&2
  exit 1
fi

set -e

CDPATH='' cd -- "$(dirname -- "$0")"

find . ! -type l ! \( -path '*/.git/*' -prune \) \
  -exec chown root:storage '{}' \; -exec chmod u-w,go= '{}' \;
find . ! -type l ! \( -type d -name .git -prune \) -type f -name '*.sh' -exec chmod u+x '{}' \;
find . ! -type l ! \( -type d -name .git -prune \) ! -path "./set-metadata.sh" \
  -perm -u+r -exec chmod g+r '{}' \;
find . ! -type l ! \( -type d -name .git -prune \) ! -path "./set-metadata.sh" \
  -perm -u+x -exec chmod g+x '{}' \;
