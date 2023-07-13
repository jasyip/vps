import sys

sys.dont_write_bytecode = True
import decimal
import os
from decimal import Decimal
from numbers import Real
from pathlib import Path

ROOT_DIR = Path(__file__).parent
if ROOT_DIR.is_relative_to(Path.cwd()):
    ROOT_DIR = ROOT_DIR.relative_to(Path.cwd())


def mount_options(flag: str, *args, **kwargs) -> tuple[str, str]:
    for path_transform_key in ("path", "file"):
        if path_transform_key in kwargs:
            as_path = Path(kwargs[path_transform_key])
            if not as_path.is_absolute() and not as_path.is_relative_to(ROOT_DIR):
                as_path = ROOT_DIR / as_path
            kwargs[path_transform_key] = as_path

    return (
        f"-{flag}",
        ",".join(args + tuple(f"{k}={v}" for k, v in kwargs.items())),
    )


def memory_ratio(ratio: Real | float) -> Decimal:
    return (
        Decimal(ratio)  # type: ignore[arg-type]
        * os.sysconf("SC_PAGE_SIZE")
        * os.sysconf("SC_PHYS_PAGES")
        / 1024
        / 1024
        / 1024
    ).quantize(Decimal(".01"), rounding=decimal.ROUND_UP)
