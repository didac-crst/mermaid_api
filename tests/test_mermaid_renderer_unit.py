import pytest

from src.render.mermaid_renderer import _raise_on_browser_error
from src.response.errors import MermaidParseError


def test_raise_on_browser_error_does_nothing_for_success():
    _raise_on_browser_error({"error": False, "svg": "<svg></svg>"})


def test_raise_on_browser_error_maps_message():
    with pytest.raises(MermaidParseError) as exc_info:
        _raise_on_browser_error({"error": True, "message": "Syntax error in text"})
    assert exc_info.value.message == "Syntax error in text"
    assert exc_info.value.status_code == 400


def test_raise_on_browser_error_uses_default_message():
    with pytest.raises(MermaidParseError) as exc_info:
        _raise_on_browser_error({"error": True})
    assert exc_info.value.message == "Invalid Mermaid syntax"
