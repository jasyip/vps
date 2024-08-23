#!/bin/sh

# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: GPL-2.0-only

set -eu

wget -qO - "https://busybox.net/downloads/busybox-${BUSYBOX_VERSION}.tar.bz2" |
  tar -xjof - --strip-components 1
sed -i 's/\(^\|[^[:alnum:]_-]\)-static\($\|[^[:alnum:]=_-]\)/\1-static-pie\2/' Makefile.flags
make allnoconfig
sleep 1
sed -i 's/^.*\(CONFIG_\(STATIC\|INSTALL_NO_USR\|DESKTOP\|LONG_OPTS\|SH_IS_NONE\|INSTALL_APPLET_SYMLINKS_NONE\|TAIL\|TEE\|FEATURE_TEE_USE_BLOCK_IO\)\)[ =].*$/\1=y/' .config
sed -i 's/^.*\(CONFIG_\(SH_IS_ASH\|INSTALL_APPLET_SYMLINKS\)\)[ =].*$/\1=n/' .config
sed -i 's%^.*\(CONFIG_PREFIX\)[ =].*$%\1="/busybox"%' .config
sed -i "s%^.*\(CONFIG_EXTRA_CFLAGS\)[ =].*$%\1=\"$CFLAGS\"%" .config
sed -i "s%^.*\(CONFIG_EXTRA_LDFLAGS\)[ =].*$%\1=\"$LDFLAGS\"%" .config
