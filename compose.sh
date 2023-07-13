#!/bin/sh

set -e

if [ $# -lt 2 ]; then
  echo "Not enough arguments" >&2
  exit 1
fi

COMPOSE="$(which podman-compose)"

STAGE="$1"
COMMAND="$2"

shift 2

case "$STAGE" in
  d | dev)
    STAGE=development
    ;;
  p | prod)
    STAGE=production
    ;;
esac

CDPATH='' cd -- "$(dirname -- "$0")"
test -f "${STAGE}.yaml"

compose_execute () {
  "$COMPOSE" -f "compose.yaml" -f "${STAGE}.yaml" "$@"
}


COMMAND_ARGS="$*"
ENV_FILE="$XDG_RUNTIME_DIR/compose.env"
case "$COMMAND" in
build)
  COMMAND_ARGS="--pull"
  ;;
up)
  if [ "$(compose_execute --podman-args "--all --format json" ps 2>/dev/null |
    jq '. | all(.State | in(["dead", "exited"]))')" = "true" ]; then
    # shellcheck disable=SC2016
    CROWDSEC_BOUNCER_API_KEY="$(openssl rand -hex 8)" envsubst \
      '$CROWDSEC_BOUNCER_API_KEY' < .env | tee "$ENV_FILE"
  fi
  MAIN_ARGS="--env-file $ENV_FILE"
  COMMAND_ARGS="--build -d --quiet-pull $COMMAND_ARGS"
  ;;
esac

# Start the process

set -x

/opt/set-metadata . storage

case "$COMMAND" in
logs)
  # shellcheck disable=SC2086
  compose_execute $MAIN_ARGS "$COMMAND" $COMMAND_ARGS 2>&1 | less
  ;;
*)
  # shellcheck disable=SC2086
  compose_execute $MAIN_ARGS "$COMMAND" $COMMAND_ARGS
  ;;
esac
