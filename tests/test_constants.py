"""Checks on the pinned download manifests in grjev.constants."""

import re

import pytest

from grjev.constants import DOWNLOADS


@pytest.mark.parametrize("name", sorted(DOWNLOADS))
def test_download_manifest_is_pinned_and_hashed(name: str) -> None:
    base_url, sha256_by_path, _ = DOWNLOADS[name]
    assert re.search(r"/[0-9a-f]{40}/", base_url)
    assert sha256_by_path
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in sha256_by_path.values())
