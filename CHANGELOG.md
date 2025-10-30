# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-30

### Added
- Streamlit web interface
- Support for 14 orchestral instruments
- Independent matrix generation (pitch, duration, velocity)
- Preset ensembles (Quartet, Quintet, Orchestra)
- LilyPond integration for score rendering
- Hacklily online visualization
- Statistical analysis dashboard
- Multi-language support (EN, PT-BR)
- Comprehensive documentation

### Changed
- Refactored Markov chain generator class
- Improved MIDI parsing with music21
- Enhanced pitch range adjustment algorithm
- Updated UI with modern design

### Fixed
- Duration quantization edge cases
- Time signature synchronization
- Tie notation for cross-bar notes

## [1.0.0] - 2024-06-15

### Added
- Initial release
- Basic Markov chain melody generator
- Tkinter GUI
- MIDI file support
- Simple export functionality

---

[2.0.0]: https://github.com/yourusername/markov-music-generator/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/yourusername/markov-music-generator/releases/tag/v1.0.0
