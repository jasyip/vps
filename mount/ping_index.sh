#!/bin/sh

sleep=0
for curl_args in \
  "http://localhost" \
  "-k -L https://localhost" \
  ; do
  if [ "$sleep" -eq 0 ]; then
    sleep=1
  else
    sleep 1.5
  fi
  COMMAND="curl -i -f $curl_args"
  echo "+ $COMMAND"
  eval "$COMMAND" || exit
  echo
done
