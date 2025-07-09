import pytest
from rysafe import Markup


class TestMarkupCompatibility:
    def test_markup_creation(self):
        assert Markup("test") == "test"
        assert isinstance(Markup("test"), Markup)
        assert Markup(b"bytes") == "bytes"
        
    def test_markup_add(self):
        m = Markup("<b>")
        assert m + "test" == Markup("<b>test")
        assert m + "<script>" == Markup("<b>&lt;script&gt;")
        assert "test" + m == Markup("test<b>")
        
    def test_markup_mul(self):
        m = Markup("<br>")
        assert m * 3 == Markup("<br><br><br>")
        assert 2 * m == Markup("<br><br>")
        
    def test_markup_mod(self):
        m = Markup("<p>%s</p>")
        assert m % "test" == Markup("<p>test</p>")
        assert m % "<script>" == Markup("<p>&lt;script&gt;</p>")
        
    def test_markup_format(self):
        m = Markup("<p>{}</p>")
        assert m.format("test") == Markup("<p>test</p>")
        assert m.format("<script>") == Markup("<p>&lt;script&gt;</p>")
        
    def test_markup_join(self):
        m = Markup("<br>")
        assert m.join(["a", "b", "c"]) == Markup("a<br>b<br>c")
        assert m.join(["<", ">"]) == Markup("&lt;<br>&gt;")
        
    def test_markup_split(self):
        m = Markup("a<br>b<br>c")
        parts = m.split("<br>")
        assert all(isinstance(p, Markup) for p in parts)
        assert parts == ["a", "b", "c"]
        
    def test_markup_strip(self):
        m = Markup("  test  ")
        assert isinstance(m.strip(), Markup)
        assert m.strip() == "test"
        
    def test_markup_methods(self):
        m = Markup("Test String")
        assert isinstance(m.lower(), str)
        assert isinstance(m.upper(), str)
        assert isinstance(m.title(), str)
        
    def test_html_method(self):
        m = Markup("<b>test</b>")
        assert m.__html__() == "<b>test</b>"