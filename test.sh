#!/bin/bash
cargo check
if [ $? -eq 0 ]; then
    echo "Cargo check passed!"
    maturin develop --release
    if [ $? -eq 0 ]; then
        echo "Maturin build successful!"
        pytest tests/test_escape.py::TestTypeHandling::test_invalid_input_types -v
        pytest tests/test_escape.py::TestMarkupClass -v
    fi
fi