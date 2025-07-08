__version__ = "0.1.0"
__author__ = "rysafe contributors"
__license__ = "MIT"

try:
    from rysafe._rysafe import (
        escape,
        escape_silent,
        unescape,
        Markup,
        soft_str,
    )
except ImportError as e:
    import html
    import warnings
    
    warnings.warn(
        f"rysafe Rust extension not available: {e}",
        RuntimeWarning,
        stacklevel=2
    )
    
    def escape(s):
        if s is None:
            return Markup("None")
        if hasattr(s, '__html__'):
            return Markup(s.__html__())
        text = str(s)
        text = html.escape(text)
        text = text.replace("'", "&#x27;")
        return Markup(text)
    
    def escape_silent(s):
        if s is None:
            return Markup("")
        return escape(s)
    
    def unescape(s):
        text = str(s)
        text = html.unescape(text)
        text = text.replace("&#x27;", "'")
        return text
    
    soft_str = escape_silent
    
    class Markup(str):
        def __new__(cls, content=""):
            return str.__new__(cls, content)
        
        def __html__(self):
            return self
        
        def __add__(self, other):
            if isinstance(other, Markup):
                return Markup(str.__add__(self, other))
            if hasattr(other, '__html__'):
                return Markup(str.__add__(self, other.__html__()))
            return Markup(str.__add__(self, str(escape(other))))
        
        def __mod__(self, args):
            if isinstance(args, tuple):
                escaped_args = []
                for arg in args:
                    if isinstance(arg, Markup):
                        escaped_args.append(str(arg))
                    elif hasattr(arg, '__html__'):
                        escaped_args.append(arg.__html__())
                    else:
                        escaped_args.append(str(escape(arg)))
                return Markup(str.__mod__(self, tuple(escaped_args)))
            else:
                if isinstance(args, Markup):
                    escaped_arg = str(args)
                elif hasattr(args, '__html__'):
                    escaped_arg = args.__html__()
                else:
                    escaped_arg = str(escape(args))
                return Markup(str.__mod__(self, escaped_arg))
        
        def unescape(self):
            return unescape(self)
        
        def striptags(self):
            text = str(self)
            result = []
            in_tag = False
            for ch in text:
                if ch == '<':
                    in_tag = True
                elif ch == '>':
                    in_tag = False
                elif not in_tag:
                    result.append(ch)
            return ''.join(result)
        
        @classmethod
        def escape(cls, s):
            return escape(s)

try:
    from . import fastapi_plugin
except Exception:
    fastapi_plugin = None

__all__ = [
    "escape",
    "escape_silent", 
    "unescape",
    "Markup",
    "soft_str",
    "fastapi_plugin",
    "__version__",
]

soft_unicode = escape_silent

def is_markupsafe_available():
    try:
        import markupsafe
        return True
    except ImportError:
        return False

def get_version_info():
    return tuple(map(int, __version__.split('.')))

_default_escape_quotes = True

def set_escape_quotes(value: bool):
    global _default_escape_quotes
    _default_escape_quotes = value

def get_escape_quotes():
    return _default_escape_quotes