import pytest
from pydantic import ValidationError

from src.validation.schemas import RenderRequest


def test_render_defaults_for_png():
    request = RenderRequest(code="flowchart TD\nA-->B")
    assert request.format == "png"
    assert request.background == "white"


def test_render_transparent_png_default_background():
    request = RenderRequest(code="flowchart TD\nA-->B", transparent=True, format="png")
    assert request.background == "transparent"


def test_render_jpeg_forces_opaque_background():
    request = RenderRequest(
        code="flowchart TD\nA-->B",
        format="jpeg",
        transparent=True,
        background="transparent",
    )
    assert request.background == "white"


def test_render_theme_validation():
    with pytest.raises(ValidationError):
        RenderRequest(code="flowchart TD\nA-->B", theme="moonlight")
