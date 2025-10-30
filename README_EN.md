# 🎵 Markov Chain Music Generator

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)
[![GitHub Stars](https://img.shields.io/github/stars/yourusername/markov-music-generator?style=social)](https://github.com/yourusername/markov-music-generator)

> **An intelligent music composition system using Markov Chains to generate original musical pieces based on MIDI training data**

[🇧🇷 Versão em Português](README.md)

![Demo](assets/demo/demo_video.gif)

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
  - [Local Installation (Tkinter)](#local-installation-tkinter)
  - [Web Version (Streamlit)](#web-version-streamlit)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Documentation](#documentation)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)
- [Citation](#citation)

---

## 🎯 Overview

The **Markov Chain Music Generator** is a Python-based algorithmic composition system that analyzes existing MIDI files and generates new, original musical compositions using probabilistic Markov Chain models. The system learns melodic patterns, rhythmic structures, and dynamic variations from training data to create stylistically similar yet unique musical pieces.

### Key Concepts

- **Markov Chains**: Stochastic process where the next state depends only on the current state(s)
- **Multi-dimensional States**: Each musical state contains pitch, duration, dynamics, articulation, and velocity
- **Independent Matrix Generation**: Separate probability matrices for pitch, rhythm, and dynamics
- **Instrument-aware Generation**: Automatic pitch adjustment for each instrument's range

---

## ✨ Features

### 🎼 Musical Capabilities
- ✅ Multi-track MIDI file analysis
- ✅ Support for 14 orchestral instruments
- ✅ Configurable Markov chain order (1-3)
- ✅ Rhythm quantization options
- ✅ Dynamic time signature support
- ✅ Automatic pitch range adjustment per instrument
- ✅ Dynamic markings and articulations

### 💻 Technical Features
- ✅ **Dual Interface**: Desktop GUI (Tkinter) and Web App (Streamlit)
- ✅ **Export Formats**: MusicXML, MIDI, CSV analysis
- ✅ **Score Visualization**: PNG rendering and LilyPond integration
- ✅ **Statistical Analysis**: Detailed composition metrics
- ✅ **Preset Ensembles**: String Quartet, Wind Quintet, Orchestra, etc.
- ✅ **Real-time Playback**: MIDI audio preview

### 🎨 User Interface
- ✅ Intuitive drag-and-drop MIDI upload
- ✅ Interactive parameter controls
- ✅ Live score preview
- ✅ Comprehensive analysis dashboard
- ✅ One-click deployment to Streamlit Cloud

---

## 🚀 Demo

### Web Version (Streamlit)
**Try it live**: [https://markov-music-generator.streamlit.app](https://mcmc-markov-chain-music-composer.streamlit.app/)

### Screenshots

<table>
  <tr>
    <td><img src="assets/images/screenshot_streamlit.png" alt="Streamlit Interface" width="400"/></td>
    <td><img src="assets/images/screenshot_tkinter.png" alt="Tkinter Interface" width="400"/></td>
  </tr>
  <tr>
    <td align="center"><b>Web Interface (Streamlit)</b></td>
    <td align="center"><b>Desktop Interface (Tkinter)</b></td>
  </tr>
</table>

---

## 🔧 Installation

### Prerequisites
```bash
Python 3.8 or higher
pip (Python package manager)
```

### Local Installation (Tkinter)

#### 1. Clone the repository
```bash
git clone https://github.com/yourusername/markov-music-generator.git
cd markov-music-generator
```

#### 2. Create virtual environment (recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Run the desktop application
```bash
python markov_music_gui.py
```

---

### Web Version (Streamlit)

#### Option A: Run Locally
```bash
# After installing dependencies
streamlit run markov_music_streamlit.py
```

The app will open automatically at `http://localhost:8501`

#### Option B: Deploy to Streamlit Cloud

1. **Fork this repository** to your GitHub account

2. **Sign up** at [share.streamlit.io](https://share.streamlit.io)

3. **Deploy**:
   - Click "New app"
   - Select your forked repository
   - Main file: `markov_music_streamlit.py`
   - Click "Deploy"

4. **Share** your app URL with others!

---

## 📚 Usage

### Quick Start

#### Desktop Version (Tkinter)

1. **Launch the application**:
```bash
   python markov_music_gui.py
```

2. **Upload MIDI files**:
   - Click "Upload MIDI Files"
   - Select one or more `.mid` files for training

3. **Configure generation**:
   - Select instruments (or use presets)
   - Adjust Markov chain order (1-3)
   - Set melody length, BPM, time signature

4. **Generate music**:
   - Click "Generate Music"
   - Preview the score
   - Export as MIDI or MusicXML

#### Web Version (Streamlit)

1. **Access the app** (local or cloud URL)

2. **Upload training data** in the sidebar

3. **Select instruments** using presets or custom selection

4. **Configure parameters**:
   - Chain order
   - Quantization
   - Melody length
   - Tempo and time signature

5. **Generate and download**:
   - Click "🎵 Generate Music"
   - View the score visualization
   - Download MIDI/MusicXML files

---

## 🧠 How It Works

### Architecture Overview
```
┌─────────────────┐
│  MIDI Input     │
│  (.mid files)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parse & Extract│
│  - Pitch        │
│  - Duration     │
│  - Velocity     │
│  - Dynamics     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Preprocessing  │
│  - Quantization │
│  - Normalization│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Build Probability Matrices     │
├─────────────────────────────────┤
│  1. Transition Matrix (full)    │
│  2. Pitch Matrix (melodic)      │
│  3. Duration Matrix (rhythmic)  │
│  4. Velocity Matrix (dynamic)   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Generation     │
│  - Random Walk  │
│  - Weighted by  │
│    Probabilities│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Post-Process   │
│  - Range Adjust │
│  - Create Score │
│  - Add Dynamics │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Export         │
│  - MIDI         │
│  - MusicXML     │
│  - PNG/PDF      │
└─────────────────┘
```

### Mathematical Foundation

#### State Representation
Each musical state is a 5-tuple:
```python
state = (pitch, duration, dynamic, articulation, velocity)
```

#### Transition Probability
```
P(state_n+1 | state_n, ..., state_n-k+1)
```
where `k` is the Markov chain order.

#### Probability Matrix
```python
transition_matrix[current_state][next_state] = probability
```

For detailed mathematical formulation, see [docs/en/COMPLETE_GUIDE.md](docs/en/COMPLETE_GUIDE.md)

---

## 📖 Documentation

### English
- [Complete Technical Guide](docs/en/COMPLETE_GUIDE.md)
- [Tutorial for Beginners](docs/en/TUTORIAL.md)
- [API Reference](docs/en/API.md)

### Português (Brasil)
- [Guia Técnico Completo](docs/pt-BR/GUIA_COMPLETO.md)
- [Tutorial para Iniciantes](docs/pt-BR/TUTORIAL.md)
- [Referência da API](docs/pt-BR/API.md)

---

## 🎼 Examples

### Sample MIDI Files

Training data examples are available in `examples/midi_samples/`:
- `bach_prelude.mid` - Baroque style
- `mozart_theme.mid` - Classical style

### Generated Outputs

Example outputs in `examples/generated_outputs/`:
- `example_1.mid` - String quartet composition
- `example_1.xml` - MusicXML for notation software

### Jupyter Notebooks

Explore the `examples/notebooks/` directory for:
- Markov chain analysis
- Statistical visualization
- Custom generation scripts

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/markov-music-generator.git

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black src/
isort src/
```

### Areas for Contribution
- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🎨 UI/UX enhancements
- 🌍 Translations
- 🎵 Example MIDI files

---

## 📊 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.8 | 3.10+ |
| **RAM** | 4 GB | 8 GB+ |
| **Storage** | 100 MB | 500 MB+ |
| **OS** | Windows 10, macOS 10.14, Linux | Any modern OS |

### Optional Dependencies
- **MuseScore** (for PNG score rendering)
- **LilyPond** (for advanced notation)
- **FluidSynth** (for audio playback)

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 📚 Citation

If you use this software in your research, please cite:
```bibtex
@software{markov_music_generator,
  author = {Your Name},
  title = {Markov Chain Music Generator},
  year = {2025},
  url = {https://github.com/yourusername/markov-music-generator},
  version = {2.0}
}
```

---

## 🙏 Acknowledgments

- **music21** library by MIT
- **Streamlit** framework
- Inspiration from algorithmic composition pioneers
- Contributors and the open-source community

---

## 📧 Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/markov-music-generator/issues)
- **Email**: ieysimurra@gmail.com

---

## 🗺️ Roadmap

- [ ] v2.1: Harmonic analysis integration
- [ ] v2.2: Real-time MIDI input
- [ ] v2.3: Multi-language support (ES, FR, DE)
- [ ] v3.0: Neural network hybrid models
- [ ] v3.1: VST plugin support

---

<div align="center">

**⭐ Star this repository if you find it useful!**

Made with ❤️ and 🎵 by [Your Name](https://github.com/yourusername)

</div>
