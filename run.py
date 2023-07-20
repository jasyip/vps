#!/usr/bin/python


import decimal
import logging
import os
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

        kwpairs: Final[list[str]] = args[-1].split(",")
        for i, pair in enumerate(kwpairs):
            key, separator, value = pair.partition("=")
            key = key.strip()
            value = value.strip()

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
    parser.add_argument("base_image", nargs='?', type=lambda x: x if x is None else Path(x))
    main_args, qemu_args = parser.parse_known_args()

    logging.basicConfig(
        stream=sys.stderr, level=logging.DEBUG if main_args.debug else logging.INFO
    )

    if main_args.base_image is None:
        raw_images: Final[set[Path]] = set()
        for child in ROOT_DIR.iterdir():
            if child.suffix.removeprefix(".") in {"raw", "img"}:
                raw_images.add(child)
        if len(raw_images) != 1:
            parser.error("cannot unambiguously assume base image, please provide")
        main_args.base_image = next(iter(raw_images))

    _logger.debug(f"{qemu_args=}")
    command_list: list[tuple[str, ...]] = list(config.command(main_args.base_image))
    command_list.append(tuple(qemu_args))
    _logger.info(f"{pformat(command_list)=!s}")

    final_command: Final[tuple[str, ...]] = tuple(chain.from_iterable(command_list))
    _logger.debug(f"{final_command=}")
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(final_command[0], final_command)
