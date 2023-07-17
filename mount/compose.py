import sys

sys.dont_write_bytecode = True

import json
import logging
import os
import re
import secrets
import shlex
import signal
import subprocess
import time
from argparse import ArgumentParser
from collections.abc import Iterable, Sequence
from pathlib import Path, PurePath
from string import Template
from typing import Any, Final, Optional

COMPOSE: Final[str] = "podman-compose"
SET_METADATA_CMD: Final[tuple[str, ...]] = ("/opt/set-metadata", ".", "server")
main_args: Final[list[str]] = ["-f", "compose.yaml"]
subcommand_args: Final[list[str]] = []

own_parser: Final = ArgumentParser()
own_parser.add_argument("-d", "--debug", action="store_true")
own_parser.add_argument("-p", "--production", action="store_true")
own_parser.add_argument("--less-opts", default="", type=shlex.split)

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

os.chdir(PurePath(__file__).parent)

stage_file: Final[Path] = Path(
    "production.yaml" if own_args.production else "development.yaml"
)
if not stage_file.is_file():
    raise OSError(f"{stage_file} is not a file")
main_args.extend(("-f", str(stage_file)))


subcommand: Final[str] = sys.argv[_subcommand_ind]


def command(args: Optional[Iterable[str]] = None) -> tuple[str, ...]:
    return (
        COMPOSE,
        *main_args,
        *((subcommand, *subcommand_args) if args is None else args),
    )


match subcommand:
    case "build":
        subcommand_args.append("--pull")

    case "up":
        tmp_dir: Path
        if "XDG_RUNTIME_DIR" in os.environ:
            tmp_dir = Path(os.environ["XDG_RUNTIME_DIR"])
        elif "XDG_STATE_HOME" in os.environ:
            tmp_dir = Path(os.environ["XDG_STATE_HOME"], "tmp")
            tmp_dir.mkdir(exist_ok=True)
        else:
            tmp_dir = Path("~", ".local", "state", "tmp")
            tmp_dir.mkdir(parents=True, exist_ok=True)
        env_file: Final[Path] = tmp_dir / "compose.env"

        ps_proc: Final = subprocess.run(
            command(("--podman-args", "--all --format json", "ps")),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            text=True,
        )
        ps_json_output: Final = json.loads(ps_proc.stdout)
        if all(
            container["State"] in {"dead", "exited"} for container in ps_json_output
        ):
            env_template: Final = Template(Path(".env").read_text())
            env_file.write_text(
                env_template.safe_substitute(
                    CROWDSEC_BOUNCER_API_KEY=secrets.token_hex(16 // 2)
                )
            )

        main_args.extend(("--env-file", str(env_file)))
        subcommand_args.append("-d")

main_args.extend(additional_main_args)
subcommand_args.extend(sys.argv[_subcommand_ind + 1 :])

subprocess.run(SET_METADATA_CMD, check=True)

final_command: Final[tuple[str, ...]] = command()
_logger.info(f"Executing: {final_command}")
match subcommand:
    case "logs":
        pager_command: Final[Sequence[str]] = (
            "/usr/bin/less",
            *own_args.less_opts,
        )
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
