#!/bin/sh

set -eu

slept=0
for curl_args in \
  "http://localhost:50080" \
  "-k -L https://localhost:50443" \
; do
  if [ "$slept" -eq 0 ]; then
    slept=1
  else
    sleep 1.5
  fi
  COMMAND="curl -sS -D - -o /dev/null $curl_args"
  echo "+ $COMMAND" >&2
  eval "$COMMAND"
  echo
done
