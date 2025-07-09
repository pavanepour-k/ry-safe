"""
Comprehensive tests for Markup string methods.

Ensures all string transformation methods properly preserve the Markup type.
"""

from rysafe import Markup


class TestMarkupStringMethods:
    """Test that string methods preserve Markup type."""

    def test_case_transformation_methods(self):
        """Test case transformation methods preserve Markup type."""
        m = Markup("Hello <World>")

        # Test each method returns Markup
        assert isinstance(m.lower(), Markup)
        assert m.lower() == Markup("hello <world>")

        assert isinstance(m.upper(), Markup)
        assert m.upper() == Markup("HELLO <WORLD>")

        assert isinstance(m.title(), Markup)
        assert m.title() == Markup("Hello <World>")

        assert isinstance(m.capitalize(), Markup)
        assert m.capitalize() == Markup("Hello <world>")

        assert isinstance(m.swapcase(), Markup)
        assert m.swapcase() == Markup("hELLO <wORLD>")

        assert isinstance(m.casefold(), Markup)
        assert m.casefold() == Markup("hello <world>")

    def test_alignment_methods(self):
        """Test alignment methods preserve Markup type."""
        m = Markup("<tag>")

        assert isinstance(m.center(10), Markup)
        assert m.center(10) == Markup("  <tag>   ")

        assert isinstance(m.ljust(10), Markup)
        assert m.ljust(10) == Markup("<tag>     ")

        assert isinstance(m.rjust(10), Markup)
        assert m.rjust(10) == Markup("     <tag>")

        assert isinstance(m.zfill(10), Markup)
        assert m.zfill(10) == Markup("00000<tag>")

    def test_whitespace_methods(self):
        """Test whitespace methods preserve Markup type."""
        m = Markup("  <tag>  ")

        assert isinstance(m.strip(), Markup)
        assert m.strip() == Markup("<tag>")

        assert isinstance(m.lstrip(), Markup)
        assert m.lstrip() == Markup("<tag>  ")

        assert isinstance(m.rstrip(), Markup)
        assert m.rstrip() == Markup("  <tag>")

        # Test with custom chars
        m2 = Markup("xxx<tag>xxx")
        assert isinstance(m2.strip("x"), Markup)
        assert m2.strip("x") == Markup("<tag>")

    def test_split_methods(self):
        """Test split methods return list of Markup."""
        m = Markup("a<br>b<br>c")

        parts = m.split("<br>")
        assert all(isinstance(p, Markup) for p in parts)
        assert parts == [Markup("a"), Markup("b"), Markup("c")]

        parts = m.rsplit("<br>", 1)
        assert all(isinstance(p, Markup) for p in parts)
        assert parts == [Markup("a<br>b"), Markup("c")]

        m2 = Markup("line1\nline2\nline3")
        lines = m2.splitlines()
        assert all(isinstance(line, Markup) for line in lines)
        assert lines == [Markup("line1"), Markup("line2"), Markup("line3")]

    def test_partition_methods(self):
        """Test partition methods preserve Markup type."""
        m = Markup("hello<br>world")

        left, sep, right = m.partition("<br>")
        assert isinstance(left, Markup)
        assert isinstance(right, Markup)
        assert left == Markup("hello")
        assert sep == "<br>"
        assert right == Markup("world")

        left, sep, right = m.rpartition("<br>")
        assert isinstance(left, Markup)
        assert isinstance(right, Markup)

    def test_replace_method(self):
        """Test replace preserves Markup type."""
        m = Markup("Hello <world>")

        result = m.replace("Hello", "Hi")
        assert isinstance(result, Markup)
        assert result == Markup("Hi <world>")

        result = m.replace("<world>", "<universe>")
        assert isinstance(result, Markup)
        assert result == Markup("Hello <universe>")

    def test_expandtabs_method(self):
        """Test expandtabs preserves Markup type."""
        m = Markup("a\tb\tc")

        result = m.expandtabs()
        assert isinstance(result, Markup)
        assert result == Markup("a       b       c")

        result = m.expandtabs(4)
        assert isinstance(result, Markup)
        assert result == Markup("a   b   c")

    def test_translate_method(self):
        """Test translate preserves Markup type."""
        m = Markup("Hello <world>")

        # Create translation table
        trans = str.maketrans("aeiou", "12345")

        result = m.translate(trans)
        assert isinstance(result, Markup)
        assert result == Markup("H2ll4 <w4rld>")

    def test_format_methods(self):
        """Test format methods with auto-escaping."""
        m = Markup("Hello {}, welcome to {}")

        # Test positional format
        result = m.format("<user>", "<site>")
        assert isinstance(result, Markup)
        assert result == Markup("Hello &lt;user&gt;, welcome to &lt;site&gt;")

        # Test with safe Markup
        result = m.format(Markup("<b>user</b>"), "<site>")
        assert result == Markup("Hello <b>user</b>, welcome to &lt;site&gt;")

        # Test format_map
        m2 = Markup("Hello {name}")
        result = m2.format_map({"name": "<script>"})
        assert isinstance(result, Markup)
        assert result == Markup("Hello &lt;script&gt;")

    def test_join_method(self):
        """Test join with auto-escaping."""
        m = Markup(" & ")

        result = m.join(["<a>", "b", "<c>"])
        assert isinstance(result, Markup)
        assert result == Markup("&lt;a&gt; & b & &lt;c&gt;")

        # Test with Markup items
        result = m.join([Markup("<b>bold</b>"), "<i>italic</i>"])
        assert result == Markup("<b>bold</b> & &lt;i&gt;italic&lt;/i&gt;")

    def test_indexing_and_slicing(self):
        """Test indexing and slicing behavior."""
        m = Markup("Hello <world>")

        # Single character should be string
        assert isinstance(m[0], str)
        assert m[0] == "H"

        # Slice should be Markup
        assert isinstance(m[0:5], Markup)
        assert m[0:5] == Markup("Hello")

        assert isinstance(m[6:], Markup)
        assert m[6:] == Markup("<world>")

    def test_iteration(self):
        """Test iteration over Markup."""
        m = Markup("Hi")

        chars = list(m)
        assert chars == ["H", "i"]
        assert all(isinstance(c, str) for c in chars)

        # Test that iteration doesn't escape
        m2 = Markup("<>")
        chars = list(m2)
        assert chars == ["<", ">"]

    def test_comparison_operators(self):
        """Test comparison operators work correctly."""
        m1 = Markup("abc")
        m2 = Markup("abc")
        m3 = Markup("def")

        # Equality
        assert m1 == m2
        assert m1 == "abc"
        assert not (m1 != m2)

        # Ordering
        assert m1 < m3
        assert m1 <= m3
        assert m3 > m1
        assert m3 >= m1

        # With plain strings
        assert m1 == "abc"
        assert m1 < "def"

    def test_special_methods(self):
        """Test special methods and edge cases."""
        m = Markup("<b>test</b>")

        # __repr__
        assert repr(m) == "Markup('<b>test</b>')"

        # __html__
        assert m.__html__() == "<b>test</b>"

        # __str__ (inherited)
        assert str(m) == "<b>test</b>"

        # __len__
        assert len(m) == 11

        # __contains__
        assert "<b>" in m
        assert "test" in m

    def test_chaining_operations(self):
        """Test chaining multiple operations preserves Markup."""
        m = Markup("  hello WORLD  ")

        result = m.strip().lower().replace("world", "universe").center(20)

        assert isinstance(result, Markup)
        assert result == Markup("   hello universe   ")

    def test_empty_markup(self):
        """Test operations on empty Markup."""
        m = Markup("")

        assert m.strip() == Markup("")
        assert m.upper() == Markup("")
        assert m.replace("x", "y") == Markup("")
        assert m.split() == []
        assert m.join(["a", "b"]) == Markup("ab")


class TestMarkupEscaping:
    """Test auto-escaping behavior in various contexts."""

    def test_concatenation_escaping(self):
        """Test concatenation auto-escapes unsafe strings."""
        m = Markup("<b>Safe</b>")

        # String concatenation
        result = m + " & " + "<script>"
        assert result == Markup("<b>Safe</b> &amp; &lt;script&gt;")

        # Reverse concatenation
        result = "<script>" + " & " + m
        assert result == Markup("&lt;script&gt; &amp; <b>Safe</b>")

        # With another Markup
        m2 = Markup("<i>Also safe</i>")
        result = m + " " + m2
        assert result == Markup("<b>Safe</b> <i>Also safe</i>")

    def test_multiplication(self):
        """Test multiplication preserves Markup."""
        m = Markup("<br>")

        result = m * 3
        assert isinstance(result, Markup)
        assert result == Markup("<br><br><br>")

        result = 2 * m
        assert isinstance(result, Markup)
        assert result == Markup("<br><br>")

    def test_mod_operator_escaping(self):
        """Test % operator with auto-escaping."""
        m = Markup("<p>%s</p>")

        # Single argument
        result = m % "<script>"
        assert result == Markup("<p>&lt;script&gt;</p>")

        # Tuple arguments
        m2 = Markup("<p>%s and %s</p>")
        result = m2 % ("<tag1>", "<tag2>")
        assert result == Markup("<p>&lt;tag1&gt; and &lt;tag2&gt;</p>")

        # Safe markup not escaped
        result = m % Markup("<b>Bold</b>")
        assert result == Markup("<p><b>Bold</b></p>")

    def test_unescape_method(self):
        """Test HTML entity unescaping."""
        # Basic entities
        m = Markup("&lt;div&gt;Hello &amp; goodbye&lt;/div&gt;")
        assert m.unescape() == "<div>Hello & goodbye</div>"

        # Numeric entities
        m2 = Markup("&#60;&#62;&#38;")
        assert m2.unescape() == "<>&"

        # Hex entities
        m3 = Markup("&#x3C;&#x3E;&#x26;")
        assert m3.unescape() == "<>&"

        # Mixed entities
        m4 = Markup("&copy; 2024 &bull; &lt;script&gt;")
        assert m4.unescape() == "© 2024 • <script>"

        # Invalid entities unchanged
        m5 = Markup("&invalid; &noentity")
        assert m5.unescape() == "&invalid; &noentity"
