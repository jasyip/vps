#!/bin/sh

# SPDX-FileCopyrightText: 2024 Jason Yip <general@jasonyip.slmail.me>
# SPDX-License-Identifier: GPL-2.0-only

sed -i 's/^.*\(CONFIG_\(STATIC\|INSTALL_NO_USR\|DESKTOP\|LONG_OPTS\|SH_IS_ASH\|ASH\|ASH_ECHO\|ASH_PRINTF\|ASH_TEST\|ASH_CMDCMD\|CAT\|CHOWN\|CP\|DIRNAME\|FIND\|GREP\|INSTALL\|LN\|MKDIR\|READLINK\|SED\|TR\|TRUE\|WGET\)\)[ =].*$/\1=y/' .config
sed -i 's/^.*\(CONFIG_FEATURE_\(USE_SENDFILE\|PRESERVE_HARDLINKS\|FIND_TYPE\|FIND_EXEC\|READLINK_FOLLOW\|TR_CLASSES\|WGET_LONG_OPTIONS\|WGET_TIMEOUT\)\)[ =].*$/\1=y/' .config
sed -i 's/^.*\(CONFIG_INSTALL_APPLET_SYMLINKS\)[ =].*$/\1=n/' .config
