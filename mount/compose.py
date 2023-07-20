import sys

sys.dont_write_bytecode = True

import logging
import os
import re
import shlex
import signal
import subprocess
from argparse import ArgumentParser
from collections.abc import Iterable
from pathlib import Path, PurePath
from typing import Final, Optional

COMPOSE: Final[str] = "podman-compose"
SET_METADATA_CMD: Final[tuple[str, ...]] = ("/opt/set-metadata", ".", "server")
LOCAL_ENV: Final[str] = ".local.env"
main_args: Final[list[str]] = ["-f", "compose.yaml", "--env-file", ".env"]
subcommand_args: Final[list[str]] = []

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

if Path(LOCAL_ENV).is_file():
    _logger.debug(f"Found '{LOCAL_ENV}'")
    main_args.extend(("--env-file", LOCAL_ENV))
    _logger.debug(f"{main_args=}")

subcommand: Final[str] = sys.argv[_subcommand_ind]
_logger.debug(f"{subcommand=}")


def command(args: Optional[Iterable[str]] = None) -> tuple[str, ...]:
    output: Final = (
        COMPOSE,
        *main_args,
        *((subcommand, *subcommand_args) if args is None else args),
    )
    _logger.debug(f"Will execute: {output}")
    return output


match subcommand:
    case "build":
        subcommand_args.append("--pull")

    case "up":
        subcommand_args.append("-d")

_logger.debug(f"default main_args based on subcommand: {main_args}")
_logger.debug(f"default subcommand_args based on subcommand: {subcommand_args}")

main_args.extend(additional_main_args)
subcommand_args.extend(sys.argv[_subcommand_ind + 1 :])

_logger.debug(f"{main_args=}")
_logger.debug(f"{subcommand_args=}")

_logger.debug(f"Executing {SET_METADATA_CMD}")
subprocess.run(SET_METADATA_CMD, check=True)

final_command: Final[tuple[str, ...]] = command()
_logger.info(f"Executing: {final_command}")
match subcommand:
    case "logs":
        pager_command: Final[tuple[str, ...]] = (
            "/usr/bin/less",
            *own_args.less_opts,
        )
        _logger.debug(f"{pager_command=}")
        with subprocess.Popen(
            final_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        ) as compose_proc:
            pager_status = subprocess.run(pager_command, stdin=compose_proc.stdout)
            assert compose_proc.stdout is not None
            compose_proc.stdout.close()

        compose_returncode: int = compose_proc.poll()  # type: ignore[assignment]
        pager_returncode: int = pager_status.returncode
        if compose_returncode < 0:
            _logger.warning(
                "'%s' received signal %d [%s]",
                " ".join(final_command),
                -compose_returncode,
                signal.strsignal(-compose_returncode),
            )
            compose_returncode = 1
        if pager_returncode < 0:
            _logger.warning(
                "'%s' received signal %d [%s]",
                " ".join(pager_command),
                -pager_returncode,
                signal.strsignal(-pager_returncode),
            )
            pager_returncode = 1

        sys.exit(compose_returncode or pager_returncode)

    case _:
        sys.stdout.flush()
        sys.stderr.flush()
        os.execvp(final_command[0], final_command)
