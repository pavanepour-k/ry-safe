import subprocess
import sys

import pytest

from rysafe import Markup, escape, escape_silent


class TestEscape:
    def test_empty_string(self):
        assert escape("") == Markup("")
        assert escape_silent("") == Markup("")

    def test_plain_text(self):
        assert escape("hello world") == Markup("hello world")
        assert escape_silent("hello world") == Markup("hello world")

    def test_html_entities(self):
        assert escape("<>&\"'") == Markup("&lt;&gt;&amp;&quot;&#x27;")
        assert escape_silent("<>&\"'") == Markup("&lt;&gt;&amp;&quot;&#x27;")

    def test_mixed_content(self):
        text = 'Hello <world> & "friends"'
        expected = Markup("Hello &lt;world&gt; &amp; &quot;friends&quot;")
        assert escape(text) == expected

    def test_unicode(self):
        assert escape("café 🦀") == Markup("café 🦀")
        assert escape("北京") == Markup("北京")

    def test_already_escaped(self):
        markup = Markup("<b>safe</b>")
        assert escape(markup) == markup

    def test_object_with_html(self):
        class HTMLObject:
            def __html__(self):
                return "<b>custom</b>"

        obj = HTMLObject()
        assert escape(obj) == Markup("<b>custom</b>")

    def test_bytes_input(self):
        assert escape(b"hello") == Markup("hello")
        assert escape(b"<test>") == Markup("&lt;test&gt;")

    def test_none_input(self):
        assert escape_silent(None) == Markup("")

    def test_numeric_input(self):
        assert escape(123) == Markup("123")
        assert escape(45.67) == Markup("45.67")


@pytest.mark.parametrize(
    "py_version", ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]
)
def test_version_compatibility(py_version, monkeypatch):
    monkeypatch.setenv("PY_VERSION", py_version)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rysafe; print(rysafe.escape('<test>'))",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "&lt;test&gt;" in result.stdout
