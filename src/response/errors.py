from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class MermaidApiError(Exception):
    code: str
    message: str
    status_code: int

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=self.status_code,
            detail={"error": {"code": self.code, "message": self.message}},
        )


class MermaidParseError(MermaidApiError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="MERMAID_PARSE_ERROR",
            message=message,
            status_code=400,
        )


class MermaidRenderTimeoutError(MermaidApiError):
    def __init__(self, message: str = "Render timed out") -> None:
        super().__init__(
            code="MERMAID_RENDER_TIMEOUT",
            message=message,
            status_code=504,
        )


class MermaidRenderError(MermaidApiError):
    def __init__(self, message: str = "Render failed") -> None:
        super().__init__(
            code="MERMAID_RENDER_ERROR",
            message=message,
            status_code=500,
        )
