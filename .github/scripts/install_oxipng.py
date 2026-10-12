#!/usr/bin/env python3
"""Install the pinned oxipng CLI into the active Python environment."""

import argparse
import hashlib
import io
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import urlopen


VERSION = "9.1.5"
ASSETS = {
    ("Linux", "x86_64"): (
        "x86_64-unknown-linux-gnu",
        "31988ec9631755c89466cc11397bd49346598f99cc2c48916d8bd4326e778f1f",
    ),
    ("Darwin", "x86_64"): (
        "x86_64-apple-darwin",
        "c59ca46fe281e95ca2728ca9950096f1099f0776ff4c7eeafae84fdedb26f737",
    ),
    ("Darwin", "arm64"): (
        "aarch64-apple-darwin",
        "a3fbb890c934ca785302d8533d5f076c053cc61946d52b728bca5df7f47cb2e8",
    ),
}


def install(destination: Path) -> Path:
    host = (platform.system(), platform.machine())
    if host not in ASSETS:
        raise RuntimeError(f"Unsupported oxipng platform: {host[0]} {host[1]}")
    target, checksum = ASSETS[host]
    archive_name = f"oxipng-{VERSION}-{target}"
    url = f"https://github.com/oxipng/oxipng/releases/download/v{VERSION}/{archive_name}.tar.gz"
    with urlopen(url, timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != checksum:
        raise RuntimeError(f"SHA-256 mismatch for {archive_name}.tar.gz")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".oxipng-", dir=destination) as temporary:
        binary = Path(temporary) / "oxipng"
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            member = archive.getmember(f"{archive_name}/oxipng")
            if not member.isfile():
                raise RuntimeError("The oxipng archive executable is not a regular file")
            with archive.extractfile(member) as source, binary.open("wb") as output:
                shutil.copyfileobj(source, output)
        binary.chmod(0o755)
        version = subprocess.run([str(binary), "--version"], check=True, capture_output=True, text=True)
        if version.stdout.strip() != f"oxipng {VERSION}":
            raise RuntimeError(f"Unexpected oxipng version: {version.stdout.strip()}")
        installed = destination / "oxipng"
        os.replace(binary, installed)
    return installed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path(sys.executable).parent,
                        help="Directory on PATH (default: the active Python executable directory)")
    args = parser.parse_args()
    print(f"Installed oxipng {VERSION} at {install(args.destination.absolute())}")


if __name__ == "__main__":
    main()
