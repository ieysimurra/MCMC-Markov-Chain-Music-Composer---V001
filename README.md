# 🎵 Gerador de Música com Cadeias de Markov

[![Versão Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Licença: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![App Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)
[![GitHub Stars](https://img.shields.io/github/stars/yourusername/markov-music-generator?style=social)](https://github.com/yourusername/markov-music-generator)

> **Um sistema inteligente de composição musical que utiliza Cadeias de Markov para gerar peças musicais originais baseadas em dados de treinamento MIDI**

[🇺🇸 English Version](README_EN.md)

![Demo](assets/demo/demo_video.gif)

## 📖 Índice

- [Visão Geral](#visão-geral)
- [Recursos](#recursos)
- [Demo](#demo)
- [Instalação](#instalação)
  - [Instalação Local (Tkinter)](#instalação-local-tkinter)
  - [Versão Web (Streamlit)](#versão-web-streamlit)
- [Como Usar](#como-usar)
- [Como Funciona](#como-funciona)
- [Documentação](#documentação)
- [Exemplos](#exemplos)
- [Contribuindo](#contribuindo)
- [Licença](#licença)
- [Citação](#citação)

---

## 🎯 Visão Geral

O **Gerador de Música com Cadeias de Markov** é um sistema de composição algorítmica em Python que analisa arquivos MIDI existentes e gera novas composições musicais originais usando modelos probabilísticos de Cadeias de Markov. O sistema aprende padrões melódicos, estruturas rítmicas e variações dinâmicas dos dados de treinamento para criar peças musicais estilisticamente similares, porém únicas.

### Conceitos-Chave

- **Cadeias de Markov**: Processo estocástico onde o próximo estado depende apenas do(s) estado(s) atual(is)
- **Estados Multidimensionais**: Cada estado musical contém altura, duração, dinâmica, articulação e velocity
- **Geração de Matrizes Independentes**: Matrizes de probabilidade separadas para altura, ritmo e dinâmica
- **Geração Consciente de Instrumento**: Ajuste automático de altura para o range de cada instrumento

---

## ✨ Recursos

### 🎼 Capacidades Musicais
- ✅ Análise de arquivos MIDI multi-track
- ✅ Suporte para 14 instrumentos orquestrais
- ✅ Ordem configurável da cadeia de Markov (1-3)
- ✅ Opções de quantização rítmica
- ✅ Suporte dinâmico a fórmulas de compasso
- ✅ Ajuste automático de tessitura por instrumento
- ✅ Marcações dinâmicas e articulações

### 💻 Recursos Técnicos
- ✅ **Interface Dupla**: GUI Desktop (Tkinter) e Aplicação Web (Streamlit)
- ✅ **Formatos de Exportação**: MusicXML, MIDI, análise CSV
- ✅ **Visualização de Partitura**: Renderização PNG e integração LilyPond
- ✅ **Análise Estatística**: Métricas detalhadas da composição
- ✅ **Presets de Ensemble**: Quarteto de Cordas, Quinteto de Sopros, Orquestra, etc.
- ✅ **Playback em Tempo Real**: Preview de áudio MIDI

### 🎨 Interface do Usuário
- ✅ Upload intuitivo de MIDI por arrastar-e-soltar
- ✅ Controles de parâmetros interativos
- ✅ Preview ao vivo da partitura
- ✅ Dashboard de análise abrangente
- ✅ Deploy com um clique no Streamlit Cloud

---

## 🚀 Demo

### Versão Web (Streamlit)
**Experimente agora**: [https://markov-music-generator.streamlit.app](https://your-app-url.streamlit.app)

### Capturas de Tela

<table>
  <tr>
    <td><img src="assets/images/screenshot_streamlit.png" alt="Interface Streamlit" width="400"/></td>
    <td><img src="assets/images/screenshot_tkinter.png" alt="Interface Tkinter" width="400"/></td>
  </tr>
  <tr>
    <td align="center"><b>Interface Web (Streamlit)</b></td>
    <td align="center"><b>Interface Desktop (Tkinter)</b></td>
  </tr>
</table>

---

## 🔧 Instalação

### Pré-requisitos
```bash
Python 3.8 ou superior
pip (gerenciador de pacotes Python)
```

### Instalação Local (Tkinter)

#### 1. Clone o repositório
```bash
git clone https://github.com/yourusername/markov-music-generator.git
cd markov-music-generator
```

#### 2. Crie um ambiente virtual (recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

#### 4. Execute a aplicação desktop
```bash
python markov_music_gui.py
```

---

### Versão Web (Streamlit)

#### Opção A: Executar Localmente
```bash
# Após instalar as dependências
streamlit run markov_music_streamlit.py
```

O aplicativo abrirá automaticamente em `http://localhost:8501`

#### Opção B: Deploy no Streamlit Cloud

1. **Faça um fork deste repositório** para sua conta GitHub

2. **Cadastre-se** em [share.streamlit.io](https://share.streamlit.io)

3. **Faça o Deploy**:
   - Clique em "New app"
   - Selecione seu repositório forkado
   - Arquivo principal: `markov_music_streamlit.py`
   - Clique em "Deploy"

4. **Compartilhe** a URL do seu app com outros!

---

## 📚 Como Usar

### Início Rápido

#### Versão Desktop (Tkinter)

1. **Inicie a aplicação**:
```bash
   python markov_music_gui.py
```

2. **Faça upload de arquivos MIDI**:
   - Clique em "Upload MIDI Files"
   - Selecione um ou mais arquivos `.mid` para treinamento

3. **Configure a geração**:
   - Selecione instrumentos (ou use presets)
   - Ajuste a ordem da cadeia de Markov (1-3)
   - Defina comprimento da melodia, BPM, fórmula de compasso

4. **Gere música**:
   - Clique em "Generate Music"
   - Visualize a partitura
   - Exporte como MIDI ou MusicXML

#### Versão Web (Streamlit)

1. **Acesse o app** (URL local ou na nuvem)

2. **Faça upload dos dados de treinamento** na barra lateral

3. **Selecione instrumentos** usando presets ou seleção customizada

4. **Configure os parâmetros**:
   - Ordem da cadeia
   - Quantização
   - Comprimento da melodia
   - Tempo e fórmula de compasso

5. **Gere e baixe**:
   - Clique em "🎵 Gerar Música"
   - Visualize a partitura
   - Baixe arquivos MIDI/MusicXML

---

## 🧠 Como Funciona

### Visão Geral da Arquitetura
```
┌─────────────────┐
│  Entrada MIDI   │
│  (arquivos.mid) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parse & Extração│
│  - Altura       │
│  - Duração      │
│  - Velocity     │
│  - Dinâmica     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pré-processo   │
│  - Quantização  │
│  - Normalização │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Construir Matrizes Probabilísticas │
├─────────────────────────────────┤
│  1. Matriz de Transição (completa) │
│  2. Matriz de Altura (melódica) │
│  3. Matriz de Duração (rítmica) │
│  4. Matriz de Velocity (dinâmica) │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Geração        │
│  - Random Walk  │
│  - Ponderado por│
│    Probabilidades│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pós-Processo   │
│  - Ajuste Range │
│  - Criar Partitura│
│  - Add Dinâmicas│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Exportação     │
│  - MIDI         │
│  - MusicXML     │
│  - PNG/PDF      │
└─────────────────┘
```

### Fundamento Matemático

#### Representação de Estado
Cada estado musical é uma 5-tupla:
```python
estado = (altura, duração, dinâmica, articulação, velocity)
```

#### Probabilidade de Transição
```
P(estado_n+1 | estado_n, ..., estado_n-k+1)
```
onde `k` é a ordem da cadeia de Markov.

#### Matriz de Probabilidade
```python
matriz_transicao[estado_atual][próximo_estado] = probabilidade
```

Para formulação matemática detalhada, veja [docs/pt-BR/GUIA_COMPLETO.md](docs/pt-BR/GUIA_COMPLETO.md)

---

## 📖 Documentação

### Português (Brasil)
- [Guia Técnico Completo](docs/pt-BR/GUIA_COMPLETO.md)
- [Tutorial para Iniciantes](docs/pt-BR/TUTORIAL.md)
- [Referência da API](docs/pt-BR/API.md)

### English
- [Complete Technical Guide](docs/en/COMPLETE_GUIDE.md)
- [Tutorial for Beginners](docs/en/TUTORIAL.md)
- [API Reference](docs/en/API.md)

---

## 🎼 Exemplos

### Arquivos MIDI de Exemplo

Exemplos de dados de treinamento disponíveis em `examples/midi_samples/`:
- `bach_prelude.mid` - Estilo Barroco
- `mozart_theme.mid` - Estilo Clássico

### Saídas Geradas

Exemplos de outputs em `examples/generated_outputs/`:
- `example_1.mid` - Composição para quarteto de cordas
- `example_1.xml` - MusicXML para software de notação

### Notebooks Jupyter

Explore o diretório `examples/notebooks/` para:
- Análise de cadeias de Markov
- Visualização estatística
- Scripts de geração customizados

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Consulte nosso [Guia de Contribuição](CONTRIBUTING.md) para detalhes.

### Configuração de Desenvolvimento
```bash
# Faça fork e clone o repositório
git clone https://github.com/yourusername/markov-music-generator.git

# Instale dependências de desenvolvimento
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Execute testes
pytest tests/

# Formate o código
black src/
isort src/
```

### Áreas para Contribuição
- 🐛 Correção de bugs
- ✨ Novos recursos
- 📝 Melhorias na documentação
- 🎨 Aprimoramentos de UI/UX
- 🌍 Traduções
- 🎵 Arquivos MIDI de exemplo

---

## 📊 Requisitos do Sistema

| Componente | Mínimo | Recomendado |
|-----------|---------|-------------|
| **Python** | 3.8 | 3.10+ |
| **RAM** | 4 GB | 8 GB+ |
| **Armazenamento** | 100 MB | 500 MB+ |
| **SO** | Windows 10, macOS 10.14, Linux | Qualquer SO moderno |

### Dependências Opcionais
- **MuseScore** (para renderização PNG de partituras)
- **LilyPond** (para notação avançada)
- **FluidSynth** (para playback de áudio)

---

## 📜 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 📚 Citação

Se você usar este software em sua pesquisa, por favor cite:
```bibtex
@software{markov_music_generator,
  author = {Seu Nome},
  title = {Gerador de Música com Cadeias de Markov},
  year = {2025},
  url = {https://github.com/yourusername/markov-music-generator},
  version = {2.0}
}
```

---

## 🙏 Agradecimentos

- Biblioteca **music21** pelo MIT
- Framework **Streamlit**
- Inspiração dos pioneiros da composição algorítmica
- Contribuidores e a comunidade open-source

---

## 📧 Contato

- **Issues no GitHub**: [Reportar bugs ou solicitar recursos](https://github.com/yourusername/markov-music-generator/issues)
- **Email**: seu.email@example.com
- **Twitter**: [@seuusuario](https://twitter.com/seuusuario)

---

## 🗺️ Roadmap

- [ ] v2.1: Integração de análise harmônica
- [ ] v2.2: Entrada MIDI em tempo real
- [ ] v2.3: Suporte multi-idioma (ES, FR, DE)
- [ ] v3.0: Modelos híbridos com redes neurais
- [ ] v3.1: Suporte a plugins VST

---

<div align="center">

**⭐ Dê uma estrela neste repositório se achar útil!**

Feito com ❤️ e 🎵 por [Seu Nome](https://github.com/seuusuario)

</div>
