#!/usr/bin/python


import decimal
import logging
import os
import re
import sys
from argparse import ArgumentParser
from decimal import Decimal
from itertools import chain
from numbers import Real
from pathlib import Path
from pprint import pformat
from typing import Final

_logger: Final = logging.getLogger(__name__)

ROOT_DIR: Path = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

import config


def mount_options(flag: str, *args) -> tuple[str, ...]:
    args = list(args)  # type: ignore[assignment]
    if args and "," in args[-1]:
        kwpairs: Final[list[str]] = re.split(r"\s*,\s*", args[-1])
        for i, pair in enumerate(kwpairs):
            key, separator, value = pair.partition("=")
            if separator and key in {"path", "file"}:
                as_path = Path(value)
                if not as_path.is_absolute() and not as_path.is_relative_to(ROOT_DIR):
                    as_path = ROOT_DIR / as_path
                kwpairs[i] = f"{key}={as_path}"
        args[-1] = ",".join(kwpairs)  # type: ignore[index]

    return ("-" + flag, *args)


def memory_ratio(ratio: Real | float) -> Decimal:
    return (
        Decimal(ratio)  # type: ignore[arg-type]
        * os.sysconf("SC_PAGE_SIZE")
        * os.sysconf("SC_PHYS_PAGES")
        / 1024
        / 1024
        / 1024
    ).quantize(Decimal(".01"), rounding=decimal.ROUND_UP)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("image", type=Path)
    main_args, qemu_args = parser.parse_known_args()

    logging.basicConfig(level=logging.DEBUG if main_args.debug else logging.INFO)

    _logger.debug(f"{qemu_args=}")
    command_list: list[tuple[str, ...]] = list(config.command(main_args.image))
    command_list.append(tuple(qemu_args))
    _logger.info(f"{pformat(command_list)=!s}")

    return_code: Final[int] = subprocess.run(chain.from_iterable(command_list)).returncode  # type: ignore[call-overload]
    _logger.debug(f"{return_code=}")
    if return_code < 0:
        raise_signal(-return_code)
    else:
        sys.exit(return_code)
