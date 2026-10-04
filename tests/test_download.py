"""Tests for grjev.download. httpx.get is replaced, so nothing touches the network."""

import hashlib
from pathlib import Path

import httpx
import pytest

from grjev import download

CONTENT = b"metatool"
SHA256 = hashlib.sha256(CONTENT).hexdigest()
URL = "https://example.org/file.json"


def serve(monkeypatch: pytest.MonkeyPatch, content: bytes) -> list[str]:
    """Make httpx.get return content, and return the list that records the requested URLs."""
    requested: list[str] = []

    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        requested.append(url)
        return httpx.Response(200, content=content, request=httpx.Request("GET", url))

    monkeypatch.setattr(download.httpx, "get", fake_get)
    return requested


def test_file_sha256_hashes_the_file_content(tmp_path: Path) -> None:
    path = tmp_path / "file.json"
    path.write_bytes(CONTENT)
    assert download.file_sha256(path) == SHA256


def test_download_file_writes_verified_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    serve(monkeypatch, CONTENT)
    destination = tmp_path / "nested" / "file.json"
    assert download.download_file(URL, destination, SHA256) is True
    assert destination.read_bytes() == CONTENT


def test_download_file_rejects_content_with_wrong_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    serve(monkeypatch, b"something else")
    destination = tmp_path / "file.json"
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        download.download_file(URL, destination, SHA256)
    assert not destination.exists()


def test_download_file_skips_a_verified_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    requested = serve(monkeypatch, CONTENT)
    destination = tmp_path / "file.json"
    destination.write_bytes(CONTENT)
    assert download.download_file(URL, destination, SHA256) is False
    assert requested == []


def test_download_file_rejects_existing_copy_with_wrong_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    requested = serve(monkeypatch, CONTENT)
    destination = tmp_path / "file.json"
    destination.write_bytes(b"edited by hand")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        download.download_file(URL, destination, SHA256)
    assert requested == []


def test_download_files_quotes_paths_and_counts_fetches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    requested = serve(monkeypatch, CONTENT)
    manifest = {"scenario/Finance Staff.json": SHA256, "scenario/artists&designers.json": SHA256}
    assert download.download_files("https://example.org/", manifest, tmp_path) == 2
    assert requested == [
        "https://example.org/scenario/Finance%20Staff.json",
        "https://example.org/scenario/artists%26designers.json",
    ]
    assert (tmp_path / "scenario" / "Finance Staff.json").read_bytes() == CONTENT
