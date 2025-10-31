"""Shared utilities for UI error recovery agents."""

from typing import Any


def get_type_name(expected_type: type) -> str:
    """Return a readable type name for error messages."""
    if hasattr(expected_type, "__name__"):
        return expected_type.__name__
    return str(expected_type)


def ensure_required_type(value: Any, name: str, expected_type: type) -> None:
    """Validate that ``value`` is provided and matches ``expected_type``."""
    if value is None:
        raise TypeError(f"{name} is required")
    if not isinstance(value, expected_type):
        raise TypeError(f"{name} must be a {get_type_name(expected_type)}")


def extract_agent_response_text(response: Any) -> str:
    """Normalize the agent response to a text payload."""
    content_text = str(response)
    try:
        message = getattr(response, "message", None)
        if not message:
            return content_text

        pieces: list[str] = []
        for chunk in message.get("content", []):
            text = chunk.get("text") if isinstance(chunk, dict) else None
            if text:
                pieces.append(text)
        if pieces:
            content_text = "\n".join(pieces)
    except Exception:
        pass
    return content_text
