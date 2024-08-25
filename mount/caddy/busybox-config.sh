#!/bin/sh

# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: GPL-2.0-only

sed -i 's/^.*\(CONFIG_\(STATIC\|INSTALL_NO_USR\|DESKTOP\|LONG_OPTS\|SH_IS_NONE\|INSTALL_APPLET_SYMLINKS_NONE\|TAIL\|TEE\|FEATURE_TEE_USE_BLOCK_IO\)\)[ =].*$/\1=y/' .config
sed -i 's/^.*\(CONFIG_\(SH_IS_ASH\|INSTALL_APPLET_SYMLINKS\)\)[ =].*$/\1=n/' .config
