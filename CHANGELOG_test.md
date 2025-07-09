# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Comprehensive test suite with coverage reporting
- Performance benchmarks
- Support for `&apos;` XML entity
- Extended HTML entity support (common symbols, arrows, math)
- Optimized entity parsing with lookup tables
- String transformation methods that preserve Markup type
- Better error messages for FastAPI integration

### Changed
- Improved snake_case validation in consistency checker
- Optimized unescape performance with lazy_static lookup table
- Simplified FastAPI integration module
- Enhanced documentation with examples and benchmarks

### Fixed
- Fixed snake_case validation for single-word functions
- Fixed string methods not preserving Markup type
- Removed unused imports

## [0.1.0] - 2025-07-05

### Added
- Initial release
- Core HTML/XML escaping functionality
- Rust-powered performance with PyO3 bindings
- Full MarkupSafe API compatibility
- Python 3.8-3.13 support
- FastAPI integration with auto-escaping middleware
- `Markup` class with auto-escaping string operations
- `escape()` and `escape_silent()` functions
- HTML entity unescaping support
- Unicode and international character support
- Type annotations throughout
- CI/CD with GitHub Actions
- Automated dependency updates with Dependabot

### Security
- Memory-safe implementation using Rust
- Protection against XSS attacks through proper escaping
- Control character validation

[Unreleased]: https://github.com/pavanepour-k/rysafe/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/pavanepour-k/rysafe/releases/tag/v0.1.0