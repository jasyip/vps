import os
import platform
import sys
from pathlib import Path
from typing import Final, Iterable

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from run import *
from snapshot import latest_snapshot

MEMORY_RATIO: Final[Real | float] = 0.25


def command(backing_img, /) -> Iterable[tuple[str, ...]]:

    # fmt: off
    return (
        (f"/usr/bin/qemu-system-{platform.machine()}",),
        #
        # Disable if KVM isn't supported
        ( "-accel", "kvm",),

        ( "-cpu",   "host,hv_relaxed,hv_spinlocks=0x1fff,hv_vapic,hv_time",),
        ( "-smp",    str(os.cpu_count()),),
        ( "-m",      str(memory_ratio(MEMORY_RATIO)) + "G",),

        # Mandatory for user-mode networking with virtio driver
        ( "-nic",   "user,model=virtio-net-pci,hostfwd=tcp::50080-:50080,hosftfwd=tcp::50443-:50443",),

        # See https://wiki.archlinux.org/title/QEMU#Booting_in_UEFI_mode
        mount_options("drive", "if=pflash,format=raw,readonly=on,file=/usr/share/edk2-ovmf/x64/OVMF_CODE.fd"),
        mount_options("drive", "if=pflash,format=raw,file=OVMF_VARS.fd"),

        # Highly recommended to keep below line as-is
        mount_options("drive",  f"if=virtio,file={latest_snapshot(backing_img)},format=qcow2, aio=native,cache.direct"),

        # See https://wiki.qemu.org/Documentation/9psetup
        # mount_options("virtfs", "local", "path=mount,mount_tag=docker,security_model=mapped-xattr"),
    )
    # fmt: on
