#!/bin/sh

# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: GPL-2.0-only

sed -i 's/^.*\(CONFIG_\(STATIC\|INSTALL_NO_USR\|DESKTOP\|LONG_OPTS\|SH_IS_NONE\|WGET\|FEATURE_WGET_LONG_OPTIONS\|FEATURE_WGET_TIMEOUT\)\)[ =].*$/\1=y/' .config
sed -i 's/^.*\(CONFIG_SH_IS_ASH\)[ =].*$/\1=n/' .config
