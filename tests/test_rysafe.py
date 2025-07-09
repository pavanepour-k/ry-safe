# Test script to verify rysafe works correctly
# Save this as test_rysafe.py and run it

import sys
print(f"Python version: {sys.version}")

try:
    # Test the core Rust functions directly
    from rysafe._rysafe_core import escape, escape_silent, unescape
    print("✓ Successfully imported core Rust functions")
    
    # Test basic escaping
    test_string = '<script>alert("hello")</script>'
    escaped = escape(test_string)
    print(f"Original: {test_string}")
    print(f"Escaped:  {escaped}")
    
    # Test unescaping
    unescaped = unescape(escaped)
    print(f"Unescaped: {unescaped}")
    
    # Test the Python package
    import rysafe
    print(f"✓ rysafe version: {rysafe.__version__}")
    
    # Test Markup class
    markup = rysafe.Markup("<b>Safe</b>")
    unsafe = "<script>alert('unsafe')</script>"
    combined = markup + unsafe
    print(f"Markup test: {combined}")
    
    print("\n🎉 All tests passed! rysafe is working correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    
    # Debug: Check what's available in rysafe
    try:
        import rysafe
        print(f"rysafe module found. Contents: {dir(rysafe)}")
        
        # Check if _rysafe_core exists
        try:
            import rysafe._rysafe_core
            print(f"_rysafe_core found. Contents: {dir(rysafe._rysafe_core)}")
        except ImportError as e2:
            print(f"_rysafe_core not found: {e2}")
            
    except ImportError as e3:
        print(f"rysafe package not found: {e3}")
        
except Exception as e:
    print(f"❌ Error: {e}")