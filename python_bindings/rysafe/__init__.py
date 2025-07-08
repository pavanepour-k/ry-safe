try:
    from ._rysafe import escape, escape_silent, soft_str, unescape, Markup
except ImportError:
    import html
    
    def escape(s):
        if hasattr(s, '__html__'):
            return Markup(s.__html__())
        if s is None:
            return Markup("None")
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
                return Markup(super().__add__(other))
            if hasattr(other, '__html__'):
                return Markup(super().__add__(other.__html__()))
            return Markup(super().__add__(escape(other)))
        
        def __mod__(self, args):
            if isinstance(args, tuple):
                escaped_args = tuple(
                    arg if isinstance(arg, Markup) or hasattr(arg, '__html__')
                    else escape(arg) 
                    for arg in args
                )
            else:
                escaped_args = (
                    args if isinstance(args, Markup) or hasattr(args, '__html__')
                    else escape(args)
                )
            return Markup(super().__mod__(escaped_args))
        
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

__all__ = ["escape", "escape_silent", "soft_str", "unescape", "Markup"]
__version__ = "0.1.0"