#!/usr/bin/python

import sys

sys.dont_write_bytecode = True

import logging
from typing import Final

_logger: Final = logging.getLogger(__name__)

from pathlib import Path

ROOT_DIR: Path = Path(__file__).parent
sys.path.append(str(ROOT_DIR))
if ROOT_DIR.is_relative_to(Path.cwd()):
    ROOT_DIR = ROOT_DIR.relative_to(Path.cwd())

import os
import platform
from numbers import Real
from typing import Iterable

from argparse import ArgumentParser
from snapshot import latest_snapshot
from utils import *

MEMORY_RATIO: Final[Real | float] = 0.25

def base_command(backing_img) -> Iterable[tuple[str, ...]]:
    MOUNTS: Final[Iterable[tuple[str, str]]] = (
        # fmt: off
        # mount_options("drive", media="cdrom", readonly="on", file="cd_image.iso"),
        mount_options("virtfs", "local", path="mount", mount_tag="docker", security_model="mapped-xattr"),
        # fmt: on
    )

    # fmt: off
    return [
        (f"qemu-system-{platform.machine()}",),
        ( "-accel",    "kvm",),
        ( "-machine",  "q35",),
        ( "-device",   "intel-iommu",),
        ( "-cpu",      "host,hv_relaxed,hv_spinlocks=0x1fff,hv_vapic,hv_time",),
        ( "-smp",       str(os.cpu_count()),),
        ( "-m",         str(memory_ratio(MEMORY_RATIO)) + "G",),
        ( "-boot",     "menu=on",),
        ( "-nic",      "user,model=virtio-net-pci",),
        ( "-drive",    "if=pflash,format=raw,readonly=on,file=/usr/share/edk2-ovmf/x64/OVMF_CODE.fd",),
        ( "-drive",    "if=pflash,format=raw,file=OVMF_VARS.fd",),
        ( "-drive",   f"file={latest_snapshot(backing_img)},format=qcow2,if=virtio,aio=native,cache.direct=on",),
        *MOUNTS,
    ]
    # fmt: on


import subprocess
from itertools import chain
from pprint import pformat
from signal import raise_signal

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("image", type=Path)
    main_args, qemu_args = parser.parse_known_args()

    logging.basicConfig(level=logging.DEBUG if main_args.debug else logging.INFO)

    _logger.debug(f"{qemu_args=}")
    command_list: list[tuple[str, ...]] = list(base_command(main_args.image))
    command_list.append(tuple(qemu_args))
    _logger.info(f"{pformat(command_list)=!s}")

    return_code: Final[int] = subprocess.run(chain.from_iterable(command_list)).returncode  # type: ignore[call-overload]
    _logger.debug(f"{return_code=}")
    if return_code < 0:
        raise_signal(-return_code)
    else:
        sys.exit(return_code)
