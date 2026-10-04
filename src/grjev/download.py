"""Download pinned files and check them against SHA-256 hashes."""

import hashlib
import logging
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import quote

import httpx

from grjev.constants import HTTP_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


def file_sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def check_sha256(actual: str, expected: str, source: str) -> None:
    """Raise ValueError if a SHA-256 digest differs from the expected one."""
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {source}: expected {expected}, got {actual}")


def download_file(url: str, destination: Path, sha256: str) -> bool:
    """Download url to destination after checking its SHA-256. Return False if a verified copy is already there."""
    if destination.exists():
        check_sha256(file_sha256(destination), sha256, str(destination))
        return False
    response = httpx.get(url, follow_redirects=True, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    check_sha256(hashlib.sha256(response.content).hexdigest(), sha256, url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    logger.info("Downloaded %s", destination)
    return True


def download_files(base_url: str, sha256_by_path: Mapping[str, str], destination_dir: Path) -> int:
    """Download each path under base_url into destination_dir. Return the number of files fetched."""
    fetched = 0
    for path, sha256 in sha256_by_path.items():
        fetched += download_file(base_url + quote(path), destination_dir / path, sha256)
    return fetched
