import sys

sys.dont_write_bytecode = True

import logging
import os
import re
import shlex
import subprocess
from argparse import ArgumentParser
from collections.abc import Iterable
from itertools import chain
from pathlib import Path, PurePath
from typing import Final, Optional

COMPOSE: Final[str] = "podman-compose"
SET_METADATA_CMD: Final[tuple[str, ...]] = ("/opt/set-metadata", ".", "server")
main_args: Final[list[tuple[str, ...]]] = [("-f", "compose.yaml")]
subcommand_args: Final[list[tuple[str, ...]]] = []

own_parser: Final = ArgumentParser()
own_parser.add_argument("-d", "--debug", action="store_true")
own_parser.add_argument(
    "--less-opts",
    default="",
    type=shlex.split,
    help=f"options to pass to 'less', which may be invoked depending on provided {COMPOSE} subcommand",
)

_logger: Final = logging.getLogger(__name__)


def _first_ind(f, default: int = len(sys.argv)) -> int:
    return next((i for i, arg in enumerate(sys.argv[1:], 1) if f(arg)), default)


_subcommand_ind: int = _first_ind(lambda arg: not re.match(r"\s*-", arg))
if _subcommand_ind == len(sys.argv):
    if _first_ind(lambda arg: arg in {"-h", "--help"}) < _first_ind(
        lambda arg: arg == "--"
    ):
        own_parser.print_help(sys.stderr)
        sys.exit(2)
    raise ValueError("subcommand not provided")

# additional_X_args: from user input without translation
own_args, additional_main_args = own_parser.parse_known_args(
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


def command(args: Optional[Iterable[str]] = None) -> tuple[str, ...]:
    output: tuple[str, ...] = (COMPOSE, *chain.from_iterable(main_args))
    if args is None:
        output = output + (subcommand, *chain.from_iterable(subcommand_args))
    else:
        output = output + tuple(
            args
            if all(isinstance(arg, str) for arg in args)
            else chain.from_iterable(args)
        )

    _logger.debug(f"Will execute: {output}")
    return output


match subcommand:
    case "build":
        subcommand_args.append(("--pull",))

    case "up":
        subcommand_args.append(("-d",))

additional_subcommand_args: Final[list[str]] = sys.argv[_subcommand_ind + 1 :]

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
subcommand_args.append(tuple(additional_subcommand_args))
del additional_main_args, additional_subcommand_args

_logger.debug(f"main_args after parsing subcommand: {main_args}")
_logger.debug(f"subcommand_args after parsing subcommand: {subcommand_args}")


_logger.debug(f"Executing {SET_METADATA_CMD}")
subprocess.run(SET_METADATA_CMD, check=True)

final_command: Final[tuple[str, ...]] = command()
_logger.info(f"Executing: {final_command}")

if subcommand == "logs" and "--help" not in chain.from_iterable(chain(main_args, subcommand_args)):
    _logger.info("Will pipe command stdout and stderr to 'less'")
    sys.stdout.flush()
    sys.stderr.flush()
    os.execl(
        "/bin/sh",
        "/bin/sh",
        "-c",
        f"{shlex.join(final_command)} 2>&1 | /usr/bin/less {shlex.join(own_args.less_opts)}",
    )

else:
    sys.stdout.flush()
    sys.stderr.flush()
    os.execvp(final_command[0], final_command)
