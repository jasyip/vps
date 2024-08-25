#!/bin/sh

# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: GPL-2.0-only

set -euo pipefail

gpg --recv-key C9E9416F76E610DBD09D040F47B70C55ACC9965B

URL="https://busybox.net/downloads/busybox-${BUSYBOX_VERSION}.tar.bz2"
wget -qO - "$URL" | pee 'tar -xjof - --strip-components 1' \
                        "gpg --verify <(wget -qO - '${URL}.sig') -" cat |
                        sha256sum -c <(wget -qO - "${URL}.sha256" | awk '{print $1 " -"}')


sed -i 's/\(^\|[^[:alnum:]_-]\)-static\($\|[^[:alnum:]=_-]\)/\1-static-pie\2/' Makefile.flags
make allnoconfig

sleep 1

sed -i 's%^.*\(CONFIG_PREFIX\)[ =].*$%\1="/busybox"%' .config
sed -i "s%^.*\(CONFIG_EXTRA_CFLAGS\)[ =].*$%\1=\"$CFLAGS\"%" .config
sed -i "s%^.*\(CONFIG_EXTRA_LDFLAGS\)[ =].*$%\1=\"$LDFLAGS\"%" .config

. busybox-config.sh
