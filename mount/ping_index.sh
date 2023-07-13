#!/bin/sh

for i in \
  "http://localhost:50080" \
  "-k https://localhost:50443" \
  ; do
  COMMAND="curl $i"
  echo "+ $COMMAND"
  eval "$COMMAND" || exit
  echo
done
