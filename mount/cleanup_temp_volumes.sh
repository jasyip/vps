#!/bin/sh

podman volume ls -n --format '{{.Name}}' | \
      { grep -xE '[0-9a-f]{64}' || true ; } | \
      xargs -r podman volume rm
