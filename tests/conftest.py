from pathlib import Path
from textwrap import dedent

import pytest


@pytest.fixture
def make_project(tmp_path):
    """Create files from {relative path: content} and return the project root."""

    def _make(files: dict[str, str]) -> Path:
        for rel, content in files.items():
            p = tmp_path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(dedent(content).lstrip("\n"), encoding="utf-8")
        return tmp_path

    return _make
