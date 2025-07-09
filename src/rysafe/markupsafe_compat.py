"""
MarkupSafe compatibility layer for rysafe.

Provides drop-in replacement for markupsafe.Markup and escape functions.
Follows SRP with compatibility as sole responsibility.
"""

import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    SupportsIndex,
    Tuple,
    Union,
)

from ._rysafe_core import escape as _escape
from ._rysafe_core import escape_silent as _escape_silent
from ._rysafe_core import unescape as _unescape

if sys.version_info < (3, 8):
    raise RuntimeError("rysafe requires Python 3.8+")

if TYPE_CHECKING:
    from typing import Protocol

    from typing_extensions import TypeAlias

    class SupportsHTML(Protocol):
        def __html__(self) -> str: ...

    # Type alias for format_map parameter
    FormatMapMapping: TypeAlias = Mapping[str, Any]

__all__ = ["Markup", "escape", "escape_silent", "soft_str", "soft_unicode"]


class Markup(str):
    """
    String subclass for HTML/XML markup safe strings.

    A Markup string is one that is already properly escaped and can be
    safely inserted into an HTML document without further escaping.
    """

    __slots__ = ()

    def __new__(
        cls,
        base: Any = "",
        encoding: Optional[str] = None,
        errors: str = "strict",
    ) -> "Markup":
        """
        Create new Markup instance.

        Args:
            base: String or object to convert
            encoding: Character encoding
            errors: Error handling mode

        Returns:
            Markup: Safe markup string
        """
        if hasattr(base, "__html__"):
            base = base.__html__()
        if encoding is None:
            return super().__new__(cls, base)
        return super().__new__(cls, base, encoding, errors)

    def __html__(self) -> str:
        """Return self for HTML context."""
        return self

    def __add__(self, other: Any) -> "Markup":
        """Add with auto-escaping."""
        if isinstance(other, str):
            if not isinstance(other, Markup):
                other = escape(other)
        else:
            other = escape(str(other))
        return self.__class__(super().__add__(other))

    def __radd__(self, other: Any) -> "Markup":
        """Reverse add with auto-escaping."""
        if isinstance(other, str):
            if not isinstance(other, Markup):
                other = escape(other)
        else:
            other = escape(str(other))
        return self.__class__(other.__add__(self))

    def __mul__(self, n: SupportsIndex) -> "Markup":  # type: ignore[override]
        """Multiply preserving Markup type."""
        return self.__class__(super().__mul__(n))

    __rmul__ = __mul__

    def __mod__(self, arg: Any) -> "Markup":
        """Format with auto-escaping."""
        if isinstance(arg, tuple):
            arg = tuple(_escape_arg(item) for item in arg)
        else:
            arg = _escape_arg(arg)
        return self.__class__(super().__mod__(arg))

    def __repr__(self) -> str:
        """Representation showing Markup type."""
        return f"Markup({super().__repr__()})"

    def join(self, seq: Iterable[Any]) -> "Markup":
        """Join with auto-escaping."""
        return self.__class__(super().join(escape(item) for item in seq))

    # These methods override str's return type, which is a known limitation
    # when subclassing str. We use type: ignore to suppress the errors.

    def split(self, *args: Any, **kwargs: Any) -> List["Markup"]:  # type: ignore[override]
        """Split preserving Markup type."""
        return [
            self.__class__(item) for item in super().split(*args, **kwargs)
        ]

    def rsplit(self, *args: Any, **kwargs: Any) -> List["Markup"]:  # type: ignore[override]
        """Reverse split preserving Markup type."""
        return [
            self.__class__(item) for item in super().rsplit(*args, **kwargs)
        ]

    def splitlines(self, keepends: bool = False) -> List["Markup"]:  # type: ignore[override]
        """Split lines preserving Markup type."""
        return [self.__class__(item) for item in super().splitlines(keepends)]

    def unescape(self) -> str:
        """Unescape HTML entities."""
        return _unescape(self)

    def strip(self, chars: Optional[str] = None) -> "Markup":
        """Strip preserving Markup type."""
        return self.__class__(super().strip(chars))

    def lstrip(self, chars: Optional[str] = None) -> "Markup":
        """Left strip preserving Markup type."""
        return self.__class__(super().lstrip(chars))

    def rstrip(self, chars: Optional[str] = None) -> "Markup":
        """Right strip preserving Markup type."""
        return self.__class__(super().rstrip(chars))

    def format(self, *args: Any, **kwargs: Any) -> "Markup":
        """Format with auto-escaping."""
        args = tuple(_escape_arg(arg) for arg in args)
        kwargs = {k: _escape_arg(v) for k, v in kwargs.items()}
        return self.__class__(super().format(*args, **kwargs))

    def format_map(self, map_: Any) -> "Markup":  # type: ignore[override]
        """Format with mapping and auto-escaping."""
        # Accept any mapping-like object to match str's behavior
        escaped_map = {k: _escape_arg(v) for k, v in map_.items()}
        return self.__class__(super().format_map(escaped_map))

    def partition(self, sep: str) -> Tuple["Markup", str, "Markup"]:
        """Partition preserving Markup type."""
        parts = super().partition(sep)
        return (self.__class__(parts[0]), parts[1], self.__class__(parts[2]))

    def rpartition(self, sep: str) -> Tuple["Markup", str, "Markup"]:
        """Reverse partition preserving Markup type."""
        parts = super().rpartition(sep)
        return (self.__class__(parts[0]), parts[1], self.__class__(parts[2]))

    def replace(self, old: str, new: str, count: int = -1) -> "Markup":  # type: ignore[override]
        """Replace preserving Markup type."""
        return self.__class__(super().replace(old, new, count))

    # String transformation methods that preserve Markup type
    def capitalize(self) -> "Markup":
        """Capitalize preserving Markup type."""
        return self.__class__(super().capitalize())

    def casefold(self) -> "Markup":
        """Casefold preserving Markup type."""
        return self.__class__(super().casefold())

    def lower(self) -> "Markup":
        """Convert to lowercase preserving Markup type."""
        return self.__class__(super().lower())

    def upper(self) -> "Markup":
        """Convert to uppercase preserving Markup type."""
        return self.__class__(super().upper())

    def title(self) -> "Markup":
        """Convert to title case preserving Markup type."""
        return self.__class__(super().title())

    def swapcase(self) -> "Markup":
        """Swap case preserving Markup type."""
        return self.__class__(super().swapcase())

    def center(self, width: int, fillchar: str = " ") -> "Markup":  # type: ignore[override]
        """Center preserving Markup type."""
        return self.__class__(super().center(width, fillchar))

    def ljust(self, width: int, fillchar: str = " ") -> "Markup":  # type: ignore[override]
        """Left justify preserving Markup type."""
        return self.__class__(super().ljust(width, fillchar))

    def rjust(self, width: int, fillchar: str = " ") -> "Markup":  # type: ignore[override]
        """Right justify preserving Markup type."""
        return self.__class__(super().rjust(width, fillchar))

    def zfill(self, width: int) -> "Markup":  # type: ignore[override]
        """Zero fill preserving Markup type."""
        return self.__class__(super().zfill(width))

    def expandtabs(self, tabsize: int = 8) -> "Markup":  # type: ignore[override]
        """Expand tabs preserving Markup type."""
        return self.__class__(super().expandtabs(tabsize))

    def translate(self, table: Any) -> "Markup":
        """Translate preserving Markup type."""
        return self.__class__(super().translate(table))

    # Methods for iteration
    def __iter__(self) -> Iterator[str]:
        """Iterate over characters."""
        return super().__iter__()

    def __getitem__(self, index: Any) -> Union[str, "Markup"]:
        """Get item preserving Markup type for slices."""
        result = super().__getitem__(index)
        if isinstance(index, slice):
            return self.__class__(result)
        return result

    # Rich comparison methods
    def __eq__(self, other: Any) -> bool:
        """Equal comparison."""
        return super().__eq__(other)

    def __ne__(self, other: Any) -> bool:
        """Not equal comparison."""
        return super().__ne__(other)

    def __lt__(self, other: Any) -> bool:
        """Less than comparison."""
        return super().__lt__(other)

    def __le__(self, other: Any) -> bool:
        """Less than or equal comparison."""
        return super().__le__(other)

    def __gt__(self, other: Any) -> bool:
        """Greater than comparison."""
        return super().__gt__(other)

    def __ge__(self, other: Any) -> bool:
        """Greater than or equal comparison."""
        return super().__ge__(other)


def _escape_arg(arg: Any) -> Union[Markup, str]:
    """Escape argument for Markup operations."""
    if hasattr(arg, "__html__"):
        return Markup(arg.__html__())
    return escape(arg)


def escape(s: Any) -> Markup:
    """
    Escape string for HTML/XML.

    Escapes &, <, >, ", and ' characters to their HTML entity equivalents.

    Args:
        s: Object to escape (will be converted to string)

    Returns:
        Markup: Escaped safe string

    Examples:
        >>> escape('<script>alert("xss")</script>')
        Markup('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')
        >>> escape(None)
        Markup('None')
    """
    if hasattr(s, "__html__"):
        return Markup(s.__html__())
    if isinstance(s, bytes):
        s = s.decode("utf-8", "replace")
    else:
        s = str(s)
    return Markup(_escape(s))


def escape_silent(s: Any) -> Markup:
    """
    Escape string silently ignoring errors.

    Like escape() but returns an empty string for None values.

    Args:
        s: Object to escape

    Returns:
        Markup: Escaped safe string

    Examples:
        >>> escape_silent('<b>Bold</b>')
        Markup('&lt;b&gt;Bold&lt;/b&gt;')
        >>> escape_silent(None)
        Markup('')
    """
    if s is None:
        return Markup()
    return Markup(_escape_silent(str(s)))


def soft_str(s: Any) -> str:
    """
    Convert to string preserving Markup.

    If the input is already a string (including Markup), return it unchanged.
    Otherwise convert to string.

    Args:
        s: Object to convert

    Returns:
        str: String representation
    """
    if isinstance(s, str):
        return s
    return str(s)


# Alias for backward compatibility
soft_unicode = soft_str
