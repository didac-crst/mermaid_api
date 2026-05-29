from pathlib import Path

import pytest

from src.main import _ensure_mermaid_runtime


def test_ensure_mermaid_runtime_raises_when_missing(tmp_path: Path) -> None:
    missing = tmp_path / "mermaid.min.js"
    with pytest.raises(RuntimeError, match="Mermaid runtime not found"):
        _ensure_mermaid_runtime(missing)


def test_ensure_mermaid_runtime_passes_when_present(tmp_path: Path) -> None:
    present = tmp_path / "mermaid.min.js"
    present.write_text("// mermaid", encoding="utf-8")
    _ensure_mermaid_runtime(present)
