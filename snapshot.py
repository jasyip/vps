#!/usr/bin/env python

import logging
import os
import re
import shutil
import subprocess
import sys
from argparse import ArgumentParser
from collections import namedtuple
from collections.abc import Iterable
from functools import cache, total_ordering
from pathlib import Path
from typing import Final, Optional, TypeAlias

_logger: Final = logging.getLogger(__name__)

PathLike: Final[TypeAlias] = os.PathLike | str
QEMU_IMG: Final[str] = "/usr/bin/qemu-img"


def _disable_cow(dest: PathLike) -> None:
    dest = Path(dest)
    if dest.exists():
        raise OSError(f"{dest=!s} already exists")
    dest.touch()
    process: Final = subprocess.run(
        ("chattr", "+C", str(dest)), check=True
    )


def _qemu_img(args: Iterable[str]) -> subprocess.CompletedProcess:
    _logger.debug(f"{args=}")
    return subprocess.run((QEMU_IMG, *args), check=True)


def _merge_snapshot(
    source: PathLike, dest: PathLike, *, source_fmt: str = "qcow2", dest_fmt: str, overwrite: bool
) -> None:

    try:
        _disable_cow(dest)

        _qemu_img((
            "convert",
            "-f",
            source_fmt,
            "-O",
            dest_fmt,
            str(source),
            str(dest),
        ))
    except BaseException as e:
        if overwrite:
            os.remove(dest)
        raise e

def _create_snapshot(source: PathLike, dest: PathLike, source_fmt: str = "raw") -> None:
    try:
        _disable_cow(dest)

        _qemu_img((
            "create",
            "-o",
            f"backing_file={source},backing_fmt={source_fmt}",
            "-f",
            "qcow2",
            str(dest),
        ))
    except BaseException as e:
        os.remove(dest)
        raise e


@total_ordering
class _Snapshot(namedtuple("_Snapshot", "path version version_match")):
    def __new__(cls, path: Path, version_match: re.Match[str]) -> "_Snapshot":
        return super().__new__(cls, path, int(version_match["num"]), version_match)

    def __lt__(self, other: tuple) -> bool:
        if not isinstance(other, _Snapshot):
            raise TypeError
        return self.version < other.version


@cache
def _get_all(backing: PathLike) -> Iterable[_Snapshot]:
    backing = Path(backing)
    if not backing.is_file():
        raise ValueError(f"'{backing}' is not a file")

    output: Final[list[_Snapshot]] = []
    path: Path
    for path in backing.parent.iterdir():
        version_match: Optional[re.Match[str]] = re.fullmatch(
            re.escape(backing.name[: backing.name.find(".")])
            + r"_(?P<num>[1-9]\d*|0)\.qcow2",
            path.name,
        )
        if version_match is not None:
            _logger.debug(f"Found snapshot '{path}'")
            output.append(_Snapshot(path, version_match))
    return output


def _get_latest(backing: PathLike) -> Optional[_Snapshot]:
    latest_snapshot: Optional[_Snapshot] = None
    snapshot: _Snapshot
    for snapshot in _get_all(backing):
        if latest_snapshot is None or snapshot > latest_snapshot:
            latest_snapshot = snapshot
    if latest_snapshot is None:
        _logger.debug(f"No snapshots found for '{backing}'")
    else:
        _logger.debug(f"Latest snapshot: '{latest_snapshot.path}'")
    return latest_snapshot


def latest_snapshot(backing: PathLike) -> Path:
    backing = Path(backing)
    latest_snapshot: Final[Optional[_Snapshot]] = _get_latest(backing)
    if latest_snapshot is not None:
        return latest_snapshot.path
    new_path: Final[Path] = backing.with_name(f"{backing.stem}_1.qcow2")
    _create_snapshot(backing, new_path, source_fmt=backing.suffix.removeprefix("."))
    return new_path


def new_snapshot(backing: PathLike, **kwargs) -> Path:
    backing = Path(backing)
    latest_snapshot: Final[Optional[_Snapshot]] = _get_latest(backing)
    new_version: int
    backing_file: Path
    if latest_snapshot is None:
        new_version = 1
        backing_file = backing
    else:
        new_version = latest_snapshot.version + 1
        backing_file = latest_snapshot.path
    new_path: Final[Path] = backing.with_name(f"{backing.stem}_{new_version}.qcow2")
    _logger.debug(f"new path: '{new_path}'")
    _create_snapshot(
        backing_file, new_path, source_fmt=backing_file.suffix.removeprefix(".")
    )
    return new_path


def merge_snapshots(backing: PathLike, **kwargs) -> Optional[Path]:
    backing = Path(backing)
    latest_snapshot: Optional[_Snapshot] = _get_latest(backing)
    if latest_snapshot is None:
        raise ValueError("Nothing to merge")
    merge_output_path: Path = backing
    while True:
        merge_output_path = merge_output_path.with_suffix(
            merge_output_path.suffix + "~"
        )
        if not merge_output_path.exists():
            break

    overwrite: Final = bool(kwargs.pop("overwrite"))

    _merge_snapshot(
        latest_snapshot.path,
        merge_output_path,
        dest_fmt=backing.suffix.removeprefix("."),
        overwrite=overwrite,
    )

    if overwrite:
        shutil.move(merge_output_path, backing)
        snapshot: _Snapshot
        for snapshot in _get_all(backing):
            snapshot.path.unlink()
        return None
    return merge_output_path


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    subparsers = parser.add_subparsers(required=True)

    new_parser = subparsers.add_parser("new")
    new_parser.add_argument("backing", metavar="backing_file", type=Path)
    new_parser.set_defaults(func=new_snapshot)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("-o", "--overwrite", action="store_true")
    merge_parser.add_argument("backing", metavar="backing_file", type=Path)
    merge_parser.set_defaults(func=merge_snapshots)

    args: Final = parser.parse_args()

    logging.basicConfig(
        stream=sys.stderr, level=logging.DEBUG if args.debug else logging.INFO
    )

    output: Final[Optional[Path]] = args.func(**vars(args))
    if output is None:
        _logger.info("Done!")
    else:
        _logger.info(f"New image: '{output}'")
