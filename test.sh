#!/bin/bash
# Script to ensure test_comprehensive.py is executable

# Make test_comprehensive.py executable
chmod +x tests/test_comprehensive.py

# Also make benchmark.py executable since it has a shebang
chmod +x benchmark.py

echo "✓ Made test_comprehensive.py and benchmark.py executable"