import sys

if __name__ == "__main__":
    sys.dont_write_bytecode = True

import json
import logging
import os
import re
import shlex
import subprocess
from argparse import ArgumentParser
from collections.abc import Callable, Iterable, Sequence, Set
from itertools import chain
from pathlib import Path, PurePath
from pprint import pformat
from shutil import which
from subprocess import DEVNULL, PIPE
from typing import Any, Final, NoReturn, Optional

_COMPOSE_BINARIES: Final[tuple[str, ...]] = ("docker-compose", "podman-compose")
_SET_METADATA_CMD: Final[tuple[str, ...]] = ("/opt/set-metadata", ".", "server")
_RELOAD_COMMANDS: Final[dict[str, Sequence[str]]] = {
    "caddy": ("exec", "caddy", "reload", "--config", "/etc/caddy/Caddyfile"),
    "crowdsec": ("kill", "--signal=HUP"),
    "prometheus": ("kill", "--signal=HUP"),
}

_main_args: Final[tuple[str, ...]] = tuple()
_subcommand_args: Final[tuple[str, ...]] = tuple()

_own_parser: Final = ArgumentParser()
_own_parser.add_argument("-d", "--debug", action="store_true")
_own_parser.add_argument(
    "--less-opts",
    default="",
    type=shlex.split,
    help="options to pass to 'less', which may be invoked depending on provided subcommand",
)

_logger: Final = logging.getLogger(__name__)


def _first_ind(
    args: Optional[Sequence[str]] = None,
    /,
    f: Callable[[str], bool] = lambda arg: not re.match(r"\s*-", arg),
    *,
    start: int = 0,
) -> int:
    if args is None:
        args = sys.argv
        start = 1
    arg: str
    for arg in args[start:]:
        if f(arg):
            break
        start += 1
    return start


def main() -> NoReturn:
    main_args: Final[list[tuple[str, ...]]] = [_main_args]
    subcommand_args: Final[list[tuple[str, ...]]] = [_subcommand_args]

    _subcommand_ind: int = _first_ind()
    if _subcommand_ind == len(sys.argv):
        if _first_ind(f=lambda arg: arg in {"-h", "--help"}) < _first_ind(
            f=lambda arg: arg == "--"
        ):
            _own_parser.print_help(sys.stderr)
            sys.exit(2)
        _own_parser.error("subcommand not provided")

    # additional_X_args: from user input without translation
    own_args, additional_main_args = _own_parser.parse_known_args(
        sys.argv[1:_subcommand_ind]
    )
    logging.basicConfig(
        stream=sys.stderr, level=logging.DEBUG if own_args.debug else logging.INFO
    )

    _logger.debug(f"Parsed arguments for ownself: {own_args}")

    _logger.debug(f"Initial {main_args=}")
    _logger.debug(f"Initial {subcommand_args=}")

    os.chdir(PurePath(__file__).parent)

    subcommand: Final[str] = sys.argv[_subcommand_ind]
    _logger.debug(f"{subcommand=}")

    _compose: str
    match tuple(map(bool, map(which, _COMPOSE_BINARIES))):
        case (True, _):
            _compose = "docker-compose"
            os.environ.setdefault(
                "DOCKER_HOST",
                "unix://{}/podman/podman.sock".format(
                    os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
                ),
            )
        case (False, True):
            _compose = "podman-compose"
        case _:
            raise RuntimeError(" and ".join(_COMPOSE_BINARIES) + " are not present")

    def command(*args) -> tuple[str, ...]:
        output: Final[list[str]] = [_compose]
        output.extend(chain.from_iterable(main_args))
        if args:
            laid_args: Final[list[str]] = []
            arg: str | Iterable[str]
            for arg in args if len(args) > 1 or isinstance(args[0], str) else args[0]:
                if isinstance(arg, str):
                    laid_args.append(arg)
                else:
                    laid_args.extend(arg)

            output.extend(laid_args)
        else:
            output.append(subcommand)
            output.extend(chain.from_iterable(subcommand_args))

        _logger.debug(f"Will execute: {output}")
        return tuple(output)

    # Default subcommand arguments
    match subcommand:
        case "build":
            subcommand_args.append(("--pull",))

        case "up":
            subcommand_args.append(("-d",))

    additional_subcommand_args: Final[list[str]] = sys.argv[_subcommand_ind + 1 :]

    i: int
    arg: str
    # Strip trailing slashes in container command arguments
    match subcommand:
        case (
            "pull"
            | "push"
            | "build"
            | "up"
            | "down"
            | "run"
            | "start"
            | "stop"
            | "restart"
            | "logs"
            | "port"
            | "pause"
            | "unpause"
            | "kill"
            | "reload"
        ):
            for i, arg in enumerate(additional_subcommand_args):
                if not arg.startswith("-"):
                    additional_subcommand_args[i] = arg.rstrip("/")
        case "exec":
            for i, arg in enumerate(additional_subcommand_args):
                if not arg.startswith("-"):
                    additional_subcommand_args[i] = arg.rstrip("/")
                    break

    main_args.append(tuple(additional_main_args))
    del additional_main_args

    _logger.debug(f"main_args after parsing subcommand: {main_args}")

    _logger.debug(f"Executing {_SET_METADATA_CMD}")
    subprocess.run(_SET_METADATA_CMD, check=True)

    if subcommand == "reload":
        specific_containers: Final[Set[str]] = frozenset(
            arg for arg in additional_subcommand_args if not arg.startswith("-")
        )
        ps_proc: Final = subprocess.run(
            command("--podman-args", "--all --format json", "ps"),
            stdout=PIPE,
            stderr=DEVNULL,
            check=True,
            text=True,
        )
        ps_json_output: Final[list] = json.loads(ps_proc.stdout)
        reload_statuses: Final[dict[str, int]] = {}

        container: dict[str, Any]
        for container in ps_json_output:
            service = container["Labels"]["com.docker.compose.service"]
            if (
                container["State"] in {"dead", "exited"}
                or service not in _RELOAD_COMMANDS
                or (specific_containers and service not in specific_containers)
            ):
                _logger.debug(f"NOT reloading service '{service}'")
                continue

            reload_command: tuple[str, ...] = tuple(_RELOAD_COMMANDS[service])
            main_reload_command_ind: int = _first_ind(reload_command)

            final_reload_command: list[str] = []

            final_reload_command.extend(reload_command[: main_reload_command_ind + 1])
            reload_subcommand_args: tuple[str, ...] = reload_command[
                main_reload_command_ind + 1 :
            ]

            match reload_command[main_reload_command_ind]:
                case "exec":
                    final_reload_command.append("-d")

                    exec_command_ind: int = min(
                        _first_ind(reload_subcommand_args),
                        _first_ind(reload_subcommand_args, lambda arg: arg == "--") + 1,
                    )
                    final_reload_command.extend(
                        reload_subcommand_args[:exec_command_ind]
                    )
                    final_reload_command.append(service)
                    final_reload_command.extend(
                        reload_subcommand_args[exec_command_ind:]
                    )

                case "kill" | _:
                    final_reload_command.extend(reload_command)
                    final_reload_command.append(service)

            reload_statuses[service] = subprocess.run(
                command(final_reload_command),
                stderr=DEVNULL,
            ).returncode

        if not reload_statuses:
            _logger.warning("No services were reloaded")
        elif any(reload_statuses.values()):
            _logger.error(
                " ".join(
                    (
                        "Some of the return codes of each service's reload command",
                        "reported failures:",
                        pformat(reload_statuses),
                    )
                )
            )
            error_codes: Final[Set[int]] = frozenset(
                filter(None, reload_statuses.values())
            )
            sys.exit(next(iter(error_codes)) if len(error_codes) == 1 else 1)
        else:
            _logger.info(
                f"Services {tuple(reload_statuses.keys())} successfully reloaded"
            )

        sys.exit()

    subcommand_args.append(tuple(additional_subcommand_args))
    del additional_subcommand_args

    _logger.debug(f"subcommand_args after parsing subcommand: {subcommand_args}")

    final_command: Final[tuple[str, ...]] = command()
    _logger.info(f"Executing: {final_command}")

    if "--help" not in chain.from_iterable(chain(main_args, subcommand_args)):
        match subcommand:
            case "logs" | "config":
                _logger.info("Will pipe command stdout and stderr to 'less'")
                sys.stdout.flush()
                sys.stderr.flush()
                os.execl(
                    "/bin/sh",
                    "/bin/sh",
                    "-c",
                    f"{shlex.join(final_command)} 2>&1 | /usr/bin/less {shlex.join(own_args.less_opts)}",
                )

    sys.stdout.flush()
    sys.stderr.flush()
    os.execvp(final_command[0], final_command)


if __name__ == "__main__":
    main()
