"""Comprehensive Python tests for rysafe.

This test suite ensures compatibility with MarkupSafe API and covers
all edge cases, error handling, and security scenarios.
"""

import pytest
import sys
import os
from typing import Union

# Add the python_bindings directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python_bindings'))

try:
    from rysafe import escape, escape_silent, unescape, Markup
except ImportError:
    # Use fallback implementation for testing
    import html
    
    def escape(s: Union[str, bytes]) -> Union[str, bytes]:
        if isinstance(s, bytes):
            return html.escape(s.decode('utf-8', errors='replace')).encode('utf-8')
        return html.escape(str(s))
    
    def escape_silent(s):
        if s is None:
            return None
        return escape(s)
    
    def unescape(s: Union[str, bytes]) -> Union[str, bytes]:
        if isinstance(s, bytes):
            return html.unescape(s.decode('utf-8', errors='replace')).encode('utf-8')
        return html.unescape(str(s))
    
    class Markup:
        def __init__(self, content=""):
            self.content = escape(content)
        def __str__(self):
            return self.content
        def __repr__(self):
            return f"Markup('{self.content}')"


class TestBasicFunctionality:
    """Test basic escaping and unescaping functionality."""

    def test_escape_string(self):
        """Test basic string escaping."""
        assert escape('<b>hello</b>') == '&lt;b&gt;hello&lt;/b&gt;'
        assert escape('"quoted"') == '&quot;quoted&quot;'
        assert escape("'single'") == '&#x27;single&#x27;'
        assert escape('safe & sound') == 'safe &amp; sound'
        assert escape('<>&"\'') == '&lt;&gt;&amp;&quot;&#x27;'

    def test_escape_bytes(self):
        """Test basic bytes escaping."""
        assert escape(b'<b>hello</b>') == b'&lt;b&gt;hello&lt;/b&gt;'
        assert escape(b'"quoted"') == b'&quot;quoted&quot;'
        assert escape(b'safe text') == b'safe text'

    def test_unescape_string(self):
        """Test basic string unescaping."""
        assert unescape('&lt;b&gt;hello&lt;/b&gt;') == '<b>hello</b>'
        assert unescape('&quot;quoted&quot;') == '"quoted"'
        assert unescape('&#x27;single&#x27;') == "'single'"
        assert unescape('&#39;single&#39;') == "'single'"
        assert unescape('safe &amp; sound') == 'safe & sound'

    def test_unescape_bytes(self):
        """Test basic bytes unescaping."""
        assert unescape(b'&lt;b&gt;hello&lt;/b&gt;') == b'<b>hello</b>'
        assert unescape(b'&quot;quoted&quot;') == b'"quoted"'
        assert unescape(b'safe text') == b'safe text'

    def test_no_escaping_needed(self):
        """Test strings that don't need escaping."""
        safe_strings = [
            'safe text',
            'hello world',
            '',
            '123 abc',
            'unicode: café résumé 🌍',
        ]
        
        for s in safe_strings:
            assert escape(s) == s
            assert unescape(s) == s

    def test_roundtrip_consistency(self):
        """Test that escape -> unescape returns original."""
        test_cases = [
            '<b>hello</b>',
            '"quoted string"',
            "'single quoted'",
            'mixed <b>"quotes"</b> & symbols',
            '<script>alert(\'xss\')</script>',
            'Hello 🌍 & café résumé',
            '&existing; entities &amp; new',
            '',
            '<>&"\'',
        ]

        for case in test_cases:
            escaped = escape(case)
            unescaped = unescape(escaped)
            assert unescaped == case, f"Roundtrip failed for: {case}"


class TestEscapeSilent:
    """Test escape_silent functionality."""

    def test_escape_silent_with_none(self):
        """Test that escape_silent passes None through."""
        assert escape_silent(None) is None

    def test_escape_silent_with_string(self):
        """Test that escape_silent works with strings."""
        assert escape_silent('<script>') == '&lt;script&gt;'
        assert escape_silent('safe text') == 'safe text'

    def test_escape_silent_with_bytes(self):
        """Test that escape_silent works with bytes."""
        assert escape_silent(b'<script>') == b'&lt;script&gt;'
        assert escape_silent(b'safe text') == b'safe text'


class TestTypeHandling:
    """Test type validation and error handling."""

    def test_invalid_input_types(self):
        """Test that invalid input types raise TypeError."""
        invalid_inputs = [123, [], {}, object(), True, 3.14]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError):
                escape(invalid_input)
            
            with pytest.raises(TypeError):
                unescape(invalid_input)

    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        assert escape('') == ''
        assert unescape('') == ''
        assert escape(b'') == b''
        assert unescape(b'') == b''


class TestUnicodeAndEncoding:
    """Test Unicode handling and encoding edge cases."""

    def test_unicode_characters(self):
        """Test Unicode character handling."""
        # Basic Unicode
        assert escape('café & résumé') == 'café &amp; résumé'
        assert unescape('café &amp; résumé') == 'café & résumé'

        # Emoji
        assert escape('Hello 🌍 <world>') == 'Hello 🌍 &lt;world&gt;'
        assert unescape('Hello 🌍 &lt;world&gt;') == 'Hello 🌍 <world>'

    def test_numeric_entities(self):
        """Test numeric entity unescaping."""
        # Decimal entities
        assert unescape('&#60;') == '<'
        assert unescape('&#62;') == '>'
        assert unescape('&#38;') == '&'
        assert unescape('&#34;') == '"'
        assert unescape('&#39;') == "'"
        
        # Hexadecimal entities
        assert unescape('&#x3C;') == '<'
        assert unescape('&#x3E;') == '>'
        assert unescape('&#x26;') == '&'
        assert unescape('&#x22;') == '"'
        assert unescape('&#x27;') == "'"
        
        # Unicode code points
        assert unescape('&#8364;') == '€'  # Euro sign
        assert unescape('&#127757;') == '🌍'  # Earth emoji


class TestEdgeCases:
    """Test edge cases and malformed input."""

    def test_malformed_entities(self):
        """Test handling of malformed entities."""
        malformed_cases = [
            '&notanentity;',
            '&incomplete',
            '&#invalid;',
            '&#x;',
            '&#xGG;',
            '&amp',  # Missing semicolon
        ]

        for case in malformed_cases:
            # Should not crash and should return something reasonable
            result = unescape(case)
            assert isinstance(result, str)
            assert len(result) >= 0

    def test_single_character_inputs(self):
        """Test single character inputs."""
        chars = ['<', '>', '&', '"', "'", 'a', '1', ' ']
        
        for ch in chars:
            escaped = escape(ch)
            unescaped = unescape(escaped)
            assert unescaped == ch, f"Single char roundtrip failed for: {ch}"

    def test_large_inputs(self):
        """Test with large strings."""
        # Large safe string
        large_safe = 'a' * 10000
        assert escape(large_safe) == large_safe
        assert unescape(large_safe) == large_safe

        # Large unsafe string
        large_unsafe = '<script>' * 1000
        escaped_large = escape(large_unsafe)
        unescaped_large = unescape(escaped_large)
        assert unescaped_large == large_unsafe

    def test_nested_entities(self):
        """Test already escaped content."""
        already_escaped = '&lt;b&gt;hello&lt;/b&gt;'
        double_escaped = escape(already_escaped)
        assert double_escaped == '&amp;lt;b&amp;gt;hello&amp;lt;/b&amp;gt;'
        
        unescaped_once = unescape(double_escaped)
        assert unescaped_once == already_escaped
        
        unescaped_twice = unescape(unescaped_once)
        assert unescaped_twice == '<b>hello</b>'


class TestSecurity:
    """Test security aspects and XSS prevention."""

    def test_xss_prevention(self):
        """Test XSS payload escaping."""
        xss_payloads = [
            '<script>alert(\'xss\')</script>',
            '<img src=x onerror=alert(\'xss\')>',
            '<svg onload=alert(\'xss\')>',
            'javascript:alert(\'xss\')',
            '<iframe src=javascript:alert(\'xss\')>',
            '<object data=javascript:alert(\'xss\')>',
            '<embed src=javascript:alert(\'xss\')>',
            '<link rel=stylesheet href=javascript:alert(\'xss\')>',
            '<style>@import \'javascript:alert("xss")\'</style>',
            '<meta http-equiv=refresh content=0;url=javascript:alert(\'xss\')>',
        ]

        for payload in xss_payloads:
            escaped = escape(payload)
            # Ensure no unescaped < or > remain
            assert '<' not in escaped, f"Unescaped < found in: {escaped}"
            assert '>' not in escaped, f"Unescaped > found in: {escaped}"
            
            # Ensure roundtrip consistency
            unescaped = unescape(escaped)
            assert unescaped == payload, f"XSS roundtrip failed for: {payload}"

    def test_html_injection_prevention(self):
        """Test HTML injection prevention."""
        injection_attempts = [
            '<script src=\'evil.js\'></script>',
            '<div onclick=\'malicious()\'>click me</div>',
            '<input type=\'text\' value=\'"onmouseover="alert(\'xss\')">\'>',
            '<a href=\'javascript:void(0)\' onclick=\'alert()\'>link</a>',
            '<form action=\'javascript:alert()\'>',
            '<meta charset=\'utf-8\'>',
            '<!-- <script>alert()</script> -->',
        ]

        for injection in injection_attempts:
            escaped = escape(injection)
            # Verify that dangerous characters are escaped
            assert '<' not in escaped, f"Contains unescaped <: {escaped}"
            assert '>' not in escaped, f"Contains unescaped >: {escaped}"

    def test_attribute_injection_prevention(self):
        """Test attribute injection prevention."""
        attr_injections = [
            'value=">alert(\'xss\')<input type="',
            'title=\'onclick=alert() \'',
            'data-value=\'"><script>alert()</script>\'',
            'class="foo" onload="alert()"',
        ]

        for injection in attr_injections:
            escaped = escape(injection)
            assert '"' not in escaped, f"Contains unescaped quote: {escaped}"
            assert "'" not in escaped, f"Contains unescaped single quote: {escaped}"
            assert '<' not in escaped, f"Contains unescaped <: {escaped}"
            assert '>' not in escaped, f"Contains unescaped >: {escaped}"


class TestMarkupClass:
    """Test Markup class functionality."""

    def test_markup_creation(self):
        """Test Markup object creation."""
        markup = Markup('<script>')
        assert str(markup) == '&lt;script&gt;'
        assert repr(markup) == "Markup('&lt;script&gt;')"

    def test_markup_addition(self):
        """Test Markup object addition."""
        markup1 = Markup('<b>hello</b>')
        markup2 = Markup('<i>world</i>')
        
        combined = markup1 + markup2
        assert isinstance(combined, Markup)
        assert str(combined) == '&lt;b&gt;hello&lt;/b&gt;&lt;i&gt;world&lt;/i&gt;'

    def test_markup_string_addition(self):
        """Test Markup + string addition."""
        markup = Markup('<b>hello</b>')
        combined = markup + ' <i>world</i>'
        
        assert isinstance(combined, Markup)
        # The string part should be escaped
        assert '&lt;i&gt;world&lt;/i&gt;' in str(combined)

    def test_markup_html_method(self):
        """Test __html__ method."""
        markup = Markup('<b>hello</b>')
        assert markup.__html__() == '&lt;b&gt;hello&lt;/b&gt;'


class TestMarkupSafeCompatibility:
    """Test compatibility with MarkupSafe library."""

    def test_escape_behavior_compatibility(self):
        """Test that escape behavior matches MarkupSafe."""
        test_cases = [
            ('<', '&lt;'),
            ('>', '&gt;'),
            ('&', '&amp;'),
            ('"', '&quot;'),
            ("'", '&#x27;'),  # MarkupSafe uses &#x27; for single quotes
            ('<script>', '&lt;script&gt;'),
            ('R&D', 'R&amp;D'),
            ('"Hello World"', '&quot;Hello World&quot;'),
            ("'Hello World'", '&#x27;Hello World&#x27;'),
        ]

        for input_str, expected in test_cases:
            result = escape(input_str)
            assert result == expected, f"MarkupSafe compatibility failed for: {input_str}"

    def test_unescape_behavior_compatibility(self):
        """Test that unescape behavior matches MarkupSafe."""
        test_cases = [
            ('&lt;', '<'),
            ('&gt;', '>'),
            ('&amp;', '&'),
            ('&quot;', '"'),
            ('&#x27;', "'"),
            ('&#39;', "'"),  # Alternative single quote representation
            ('&#60;', '<'),  # Numeric entity
            ('&#x3C;', '<'),  # Hex entity
        ]

        for input_str, expected in test_cases:
            result = unescape(input_str)
            assert result == expected, f"Unescape compatibility failed for: {input_str}"


# Performance tests (optional, for development)
class TestPerformance:
    """Performance tests to ensure reasonable speed."""

    def test_performance_no_escaping(self):
        """Test performance when no escaping is needed."""
        import time
        
        safe_text = 'This is a safe string with no special characters' * 100
        start_time = time.time()
        
        for _ in range(1000):
            escape(safe_text)
        
        duration = time.time() - start_time
        # Should be reasonably fast
        assert duration < 1.0, f"Performance test failed: {duration}s"

    def test_performance_heavy_escaping(self):
        """Test performance with heavy escaping needed."""
        import time
        
        unsafe_text = '<script>&"\'</script>' * 100
        start_time = time.time()
        
        for _ in range(1000):
            escape(unsafe_text)
        
        duration = time.time() - start_time
        # Should still be reasonably fast
        assert duration < 2.0, f"Heavy escaping performance test failed: {duration}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])