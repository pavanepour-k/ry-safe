"""Type stubs for the _rysafe_core Rust extension module."""

def escape(text: str) -> str:
    """
    Escape HTML/XML special characters.

    Args:
        text: String to escape

    Returns:
        Escaped string

    Raises:
        ValueError: If text contains invalid control characters
    """
    ...

def escape_silent(text: str) -> str:
    """
    Escape HTML/XML special characters, ignoring errors.

    Args:
        text: String to escape

    Returns:
        Escaped string
    """
    ...

def unescape(text: str) -> str:
    """
    Unescape HTML/XML entities.

    Args:
        text: String containing HTML entities

    Returns:
        Unescaped string
    """
    ...

__version__: str
