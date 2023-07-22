#!/bin/sh

for i in \
  "http://localhost:50080" \
  "-k -L https://localhost:50443" \
  ; do
  COMMAND="curl -i -f $i"
  echo "+ $COMMAND"
  eval "$COMMAND" || exit
  echo
done
