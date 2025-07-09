#!/usr/bin/env python3
"""
Comprehensive test suite for rysafe functionality.
Run this to verify everything is working correctly.
"""

import sys
import traceback

def test_basic_imports():
    """Test that basic imports work."""
    print("🧪 Testing basic imports...")
    try:
        import rysafe
        print(f"   ✓ rysafe imported successfully (version: {rysafe.__version__})")
        
        # Test that core functions are available
        assert hasattr(rysafe, 'escape')
        assert hasattr(rysafe, 'escape_silent')
        assert hasattr(rysafe, 'Markup')
        print("   ✓ Core functions available")
        
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_core_rust_functions():
    """Test the underlying Rust functions."""
    print("\n🦀 Testing core Rust functions...")
    try:
        from rysafe._rysafe_core import escape, escape_silent, unescape
        
        # Test escaping
        test_cases = [
            ("<script>", "&lt;script&gt;"),
            ("'hello'", "&#x27;hello&#x27;"),
            ('"world"', "&quot;world&quot;"),
            ("&amp;", "&amp;amp;"),
            ("safe text", "safe text"),
            ("", ""),
        ]
        
        for input_str, expected in test_cases:
            result = escape(input_str)
            assert result == expected, f"Expected {expected}, got {result}"
        
        print("   ✓ escape() function works correctly")
        
        # Test silent escaping
        result = escape_silent("<script>alert('test')</script>")
        expected = "&lt;script&gt;alert(&#x27;test&#x27;)&lt;/script&gt;"
        assert result == expected
        print("   ✓ escape_silent() function works correctly")
        
        # Test unescaping
        escaped = "&lt;script&gt;alert(&#x27;test&#x27;)&lt;/script&gt;"
        unescaped = unescape(escaped)
        expected = "<script>alert('test')</script>"
        assert unescaped == expected
        print("   ✓ unescape() function works correctly")
        
        return True
    except Exception as e:
        print(f"   ❌ Core function test failed: {e}")
        traceback.print_exc()
        return False

def test_markup_class():
    """Test the Markup class functionality."""
    print("\n📄 Testing Markup class...")
    try:
        import rysafe
        
        # Test basic Markup creation
        markup = rysafe.Markup("<b>Safe</b>")
        assert str(markup) == "<b>Safe</b>"
        print("   ✓ Markup creation works")
        
        # Test auto-escaping on concatenation
        unsafe = "<script>alert('xss')</script>"
        result = markup + unsafe
        expected = "<b>Safe</b>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        assert str(result) == expected
        print("   ✓ Auto-escaping on concatenation works")
        
        # Test join with auto-escaping
        items = ["<span>", "safe", "<script>"]
        result = rysafe.Markup(" ").join(items)
        expected = "&lt;span&gt; safe &lt;script&gt;"
        assert str(result) == expected
        print("   ✓ join() with auto-escaping works")
        
        # Test format with auto-escaping
        template = rysafe.Markup("Hello {}")
        result = template.format("<script>")
        expected = "Hello &lt;script&gt;"
        assert str(result) == expected
        print("   ✓ format() with auto-escaping works")
        
        # Test unescape method
        escaped_markup = rysafe.Markup("&lt;b&gt;Bold&lt;/b&gt;")
        unescaped = escaped_markup.unescape()
        assert unescaped == "<b>Bold</b>"
        print("   ✓ unescape() method works")
        
        return True
    except Exception as e:
        print(f"   ❌ Markup class test failed: {e}")
        traceback.print_exc()
        return False

def test_escape_functions():
    """Test the high-level escape functions."""
    print("\n🛡️ Testing high-level escape functions...")
    try:
        import rysafe
        
        # Test escape function
        dangerous = '<script>alert("xss")</script>'
        result = rysafe.escape(dangerous)
        expected = "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;"
        assert str(result) == expected
        assert isinstance(result, rysafe.Markup)
        print("   ✓ escape() function works")
        
        # Test escape_silent function
        result = rysafe.escape_silent(dangerous)
        assert str(result) == expected
        assert isinstance(result, rysafe.Markup)
        print("   ✓ escape_silent() function works")
        
        # Test escaping None
        result = rysafe.escape_silent(None)
        assert str(result) == ""
        print("   ✓ escape_silent(None) works")
        
        # Test escaping bytes
        byte_input = b'<script>'
        result = rysafe.escape(byte_input)
        expected = "&lt;script&gt;"
        assert str(result) == expected
        print("   ✓ escape() works with bytes")
        
        return True
    except Exception as e:
        print(f"   ❌ Escape function test failed: {e}")
        traceback.print_exc()
        return False

def test_performance():
    """Test performance with a reasonably sized string."""
    print("\n⚡ Testing performance...")
    try:
        import rysafe
        import time
        
        # Create a test string with mixed content
        test_string = "Hello <world> & 'friends' " * 1000  # ~25KB string
        
        # Time the escape operation
        start_time = time.time()
        result = rysafe.escape(test_string)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"   ✓ Escaped {len(test_string)} characters in {duration:.4f} seconds")
        
        # Verify result is correct
        assert "&lt;world&gt;" in str(result)
        assert "&amp;" in str(result)
        assert "&#x27;friends&#x27;" in str(result)
        print("   ✓ Performance test result is correct")
        
        return True
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases and error conditions."""
    print("\n🎯 Testing edge cases...")
    try:
        import rysafe
        
        # Test empty string
        result = rysafe.escape("")
        assert str(result) == ""
        print("   ✓ Empty string handling works")
        
        # Test unicode
        unicode_text = "café 🦀 中文"
        result = rysafe.escape(unicode_text)
        assert str(result) == unicode_text  # Should not be escaped
        print("   ✓ Unicode handling works")
        
        # Test already safe markup
        safe = rysafe.Markup("<b>Bold</b>")
        result = rysafe.escape(safe)
        assert str(result) == "<b>Bold</b>"  # Should not double-escape
        print("   ✓ Safe markup not double-escaped")
        
        # Test object with __html__ method
        class HTMLObject:
            def __html__(self):
                return "<em>Emphasis</em>"
        
        obj = HTMLObject()
        result = rysafe.escape(obj)
        assert str(result) == "<em>Emphasis</em>"
        print("   ✓ Objects with __html__ method work")
        
        return True
    except Exception as e:
        print(f"   ❌ Edge case test failed: {e}")
        traceback.print_exc()
        return False

def test_fastapi_integration():
    """Test FastAPI integration if available."""
    print("\n🚀 Testing FastAPI integration...")
    try:
        import rysafe
        
        # Check if FastAPI components are available
        if hasattr(rysafe, 'SafeHTMLResponse'):
            print("   ✓ FastAPI integration is available")
            
            # Try to import FastAPI to see if it's installed
            try:
                import fastapi
                print("   ✓ FastAPI is installed")
                
                # Test SafeHTMLResponse creation
                response = rysafe.SafeHTMLResponse("<script>alert('test')</script>")
                content = response.render("<script>alert('test')</script>")
                assert b"&lt;script&gt;" in content
                print("   ✓ SafeHTMLResponse works correctly")
                
            except ImportError:
                print("   ⚠️ FastAPI not installed, skipping detailed tests")
                
        else:
            print("   ⚠️ FastAPI integration not available (FastAPI not installed)")
        
        return True
    except Exception as e:
        print(f"   ❌ FastAPI integration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests and report results."""
    print("🧬 rysafe Comprehensive Test Suite")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print()
    
    tests = [
        test_basic_imports,
        test_core_rust_functions,
        test_markup_class,
        test_escape_functions,
        test_performance,
        test_edge_cases,
        test_fastapi_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! rysafe is working perfectly!")
        return 0
    else:
        print("💥 Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main())