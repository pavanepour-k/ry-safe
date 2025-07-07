#!/usr/bin/env python3
"""
Quick verification script to test rysafe imports and functionality.
Run this after fixing import issues to verify everything works.
"""

import sys
import traceback

def test_rust_import():
    """Test importing the Rust extension module."""
    print("🔍 Testing Rust extension import...")
    try:
        import rysafe._rysafe as rust_module
        print("✅ Rust extension import: SUCCESS")
        return True
    except ImportError as e:
        print(f"❌ Rust extension import: FAILED - {e}")
        print("   This means maturin develop hasn't been run or failed")
        return False
    except Exception as e:
        print(f"❌ Rust extension import: ERROR - {e}")
        return False

def test_python_package_import():
    """Test importing the main Python package."""
    print("\n🔍 Testing Python package import...")
    try:
        import rysafe
        print("✅ Python package import: SUCCESS")
        return True
    except ImportError as e:
        print(f"❌ Python package import: FAILED - {e}")
        print("   Check python_bindings/__init__.py")
        return False
    except Exception as e:
        print(f"❌ Python package import: ERROR - {e}")
        return False

def test_basic_functions():
    """Test basic escape/unescape functionality."""
    print("\n🔍 Testing basic functions...")
    try:
        import rysafe
        
        # Test escape
        result = rysafe.escape('<script>')
        expected = '&lt;script&gt;'
        assert result == expected, f"Expected {expected}, got {result}"
        print("✅ escape() function: SUCCESS")
        
        # Test unescape
        result = rysafe.unescape('&lt;script&gt;')
        expected = '<script>'
        assert result == expected, f"Expected {expected}, got {result}"
        print("✅ unescape() function: SUCCESS")
        
        # Test escape_silent
        result = rysafe.escape_silent(None)
        assert result is None, f"Expected None, got {result}"
        print("✅ escape_silent() function: SUCCESS")
        
        return True
    except Exception as e:
        print(f"❌ Basic functions: FAILED - {e}")
        traceback.print_exc()
        return False

def test_markup_class():
    """Test Markup class functionality."""
    print("\n🔍 Testing Markup class...")
    try:
        import rysafe
        
        markup = rysafe.Markup('<script>')
        result = str(markup)
        expected = '&lt;script&gt;'
        assert result == expected, f"Expected {expected}, got {result}"
        print("✅ Markup class: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ Markup class: FAILED - {e}")
        traceback.print_exc()
        return False

def test_fastapi_plugin():
    """Test FastAPI plugin import."""
    print("\n🔍 Testing FastAPI plugin...")
    try:
        from rysafe.fastapi_plugin import get_escaper, EscapeConfig
        print("✅ FastAPI plugin import: SUCCESS")
        
        # Test getting escaper function
        escaper = get_escaper()
        result = escaper('<test>')
        expected = '&lt;test&gt;'
        assert result == expected, f"Expected {expected}, got {result}"
        print("✅ FastAPI escaper function: SUCCESS")
        
        return True
    except ImportError as e:
        print(f"❌ FastAPI plugin: FAILED - {e}")
        print("   Check python_bindings/fastapi_plugin.py")
        return False
    except Exception as e:
        print(f"❌ FastAPI plugin: ERROR - {e}")
        traceback.print_exc()
        return False

def test_version_info():
    """Test version information."""
    print("\n🔍 Testing version info...")
    try:
        import rysafe
        version = rysafe.__version__
        print(f"✅ Version: {version}")
        return True
    except Exception as e:
        print(f"❌ Version info: FAILED - {e}")
        return False

def main():
    """Run all verification tests."""
    print("🚀 rysafe Import Verification Script")
    print("=" * 40)
    
    tests = [
        test_rust_import,
        test_python_package_import, 
        test_basic_functions,
        test_markup_class,
        test_fastapi_plugin,
        test_version_info,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! rysafe is working correctly.")
        return 0
    else:
        print("🚨 Some tests failed. Check error messages above.")
        print("\n💡 Common fixes:")
        print("   1. Run: maturin develop --release")
        print("   2. Check: python_bindings/__init__.py imports")
        print("   3. Verify: src/lib.rs module declarations")
        print("   4. Ensure: Cargo.toml and pyproject.toml are at root")
        return 1

if __name__ == "__main__":
    sys.exit(main())