"""
Gerador de Música com Cadeias de Markov - Versão Web
Aplicação Streamlit com visualização e playback integrados
"""

import streamlit as st
import numpy as np
import random
from music21 import converter, note, chord, stream, instrument, metadata, meter, tempo, dynamics, pitch, tie, bar
import time
import os
import base64
from pathlib import Path
import tempfile
import subprocess
import shutil
from typing import List, Dict, Tuple, Optional
import pandas as pd

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Gerador Musical com Markov",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DEFINIÇÕES DE INSTRUMENTOS
# ============================================================================

INSTRUMENT_RANGES = {
    'Flute': ('C4', 'C7'),
    'Oboe': ('Bb3', 'A6'),
    'Clarinet': ('D3', 'Bb6'),
    'Bassoon': ('Bb1', 'Eb5'),
    'Horn': ('F2', 'B5'),
    'Trumpet': ('Gb3', 'Gb6'),
    'Trombone': ('E2', 'Bb5'),
    'Tuba': ('D1', 'F4'),
    'Violin I': ('G3', 'A7'),
    'Violin II': ('G3', 'A7'),
    'Viola': ('C3', 'E6'),
    'Violoncello': ('C2', 'C6'),
    'Double Bass': ('E1', 'G4'),
    'Piano': ('A0', 'C8')
}

QUANTIZATION_OPTIONS = {
    "Semicolcheia": 0.25,
    "Colcheia": 0.5,
    "Semínima": 1.0,
    "Mínima": 2.0
}

TIME_SIGNATURES = ['4/4', '3/4', '2/4', '3/8', '6/8', '12/8']

# ============================================================================
# CLASSE MARKOV CHAIN
# ============================================================================

class MarkovChainMelodyGenerator:
    """Gerador de melodias baseado em Cadeias de Markov"""
    
    def __init__(self, states, order=1):
        if not states:
            raise ValueError("A lista de estados não pode estar vazia.")
        self.states = states
        self.order = order
        self.initial_probabilities = {}
        self.transition_matrix = {}
        self.pitch_matrix = {}
        self.duration_matrix = {}
        self.velocity_matrix = {}
        self.generated_sequences = {}

    def train(self, notes):
        """Treina o modelo com os dados fornecidos"""
        if not notes:
            raise ValueError("A lista de notas para treinamento não pode estar vazia.")
        self._calculate_initial_probabilities(notes)
        self._calculate_transition_matrix(notes)
        self._calculate_separate_matrices(notes)

    def _calculate_initial_probabilities(self, notes):
        """Calcula probabilidades iniciais"""
        for i in range(len(notes) - self.order + 1):
            state = tuple(notes[i:i+self.order])
            self.initial_probabilities[state] = self.initial_probabilities.get(state, 0) + 1
        total = sum(self.initial_probabilities.values())
        for state in self.initial_probabilities:
            self.initial_probabilities[state] /= total

    def _calculate_transition_matrix(self, notes):
        """Calcula matriz de transição principal"""
        for i in range(len(notes) - self.order):
            current_state = tuple(notes[i:i+self.order])
            next_state = notes[i+self.order]
            if current_state not in self.transition_matrix:
                self.transition_matrix[current_state] = {}
            self.transition_matrix[current_state][next_state] = \
                self.transition_matrix[current_state].get(next_state, 0) + 1
        
        for current_state in self.transition_matrix:
            total = sum(self.transition_matrix[current_state].values())
            for next_state in self.transition_matrix[current_state]:
                self.transition_matrix[current_state][next_state] /= total

    def _calculate_separate_matrices(self, notes):
        """Calcula matrizes separadas para pitch, duration e velocity"""
        for i in range(len(notes) - 1):
            current_state = notes[i]
            next_state = notes[i + 1]
            
            # Pitch matrix
            if current_state[0] not in self.pitch_matrix:
                self.pitch_matrix[current_state[0]] = {}
            if next_state[0] not in self.pitch_matrix[current_state[0]]:
                self.pitch_matrix[current_state[0]][next_state[0]] = 0
            self.pitch_matrix[current_state[0]][next_state[0]] += 1

            # Duration matrix
            if current_state[1] not in self.duration_matrix:
                self.duration_matrix[current_state[1]] = {}
            if next_state[1] not in self.duration_matrix[current_state[1]]:
                self.duration_matrix[current_state[1]][next_state[1]] = 0
            self.duration_matrix[current_state[1]][next_state[1]] += 1

            # Velocity matrix
            if current_state[4] not in self.velocity_matrix:
                self.velocity_matrix[current_state[4]] = {}
            if next_state[4] not in self.velocity_matrix[current_state[4]]:
                self.velocity_matrix[current_state[4]][next_state[4]] = 0
            self.velocity_matrix[current_state[4]][next_state[4]] += 1

        self._normalize_matrix(self.pitch_matrix)
        self._normalize_matrix(self.duration_matrix)
        self._normalize_matrix(self.velocity_matrix)

    def _normalize_matrix(self, matrix):
        """Normaliza uma matriz"""
        for state in matrix:
            total = sum(matrix[state].values())
            for next_state in matrix[state]:
                matrix[state][next_state] /= total

    def generate_all_sequences(self, instruments, length):
        """Gera sequências independentes para cada instrumento"""
        melodies_dict = {}
        sequences_data = {}
        
        for instrument in instruments:
            pitch_sequence = self._generate_sequence(length, self.pitch_matrix)
            duration_sequence = self._generate_sequence(length, self.duration_matrix)
            velocity_sequence = self._generate_sequence(length, self.velocity_matrix)
            
            melody = []
            for i in range(length):
                dynamic = map_velocity_to_dynamic(velocity_sequence[i])
                melody.append((
                    pitch_sequence[i],
                    duration_sequence[i],
                    dynamic,
                    'normal',
                    velocity_sequence[i]
                ))
            
            melodies_dict[instrument] = melody
            sequences_data[instrument] = {
                'pitch': pitch_sequence,
                'duration': duration_sequence,
                'velocity': velocity_sequence
            }
        
        self.generated_sequences = sequences_data
        return melodies_dict

    def _generate_sequence(self, length, matrix):
        """Gera uma sequência usando uma matriz específica"""
        if not matrix:
            raise ValueError("Matriz de transição vazia")
            
        sequence = []
        current_state = random.choice(list(matrix.keys()))
        sequence.append(current_state)
        
        for _ in range(length - 1):
            if current_state in matrix:
                next_states = list(matrix[current_state].keys())
                probabilities = list(matrix[current_state].values())
                current_state = random.choices(next_states, weights=probabilities)[0]
            else:
                current_state = random.choice(list(matrix.keys()))
            sequence.append(current_state)
            
        return sequence

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def map_velocity_to_dynamic(velocity):
    """Mapeia velocity MIDI para dinâmica musical"""
    if velocity is None:
        return 'mf'
    velocity = int(velocity)
    
    if velocity < 16:
        return 'ppp'
    elif velocity < 32:
        return 'pp'
    elif velocity < 48:
        return 'p'
    elif velocity < 64:
        return 'mp'
    elif velocity < 80:
        return 'mf'
    elif velocity < 96:
        return 'f'
    elif velocity < 112:
        return 'ff'
    else:
        return 'fff'

def load_midi_file(file_path):
    """Carrega um arquivo MIDI e extrai informações de notas"""
    midi = converter.parse(file_path)
    parts = instrument.partitionByInstrument(midi)

    voices = []
    for i, part in enumerate(parts.parts):
        voice_data = []
        instrument_name = part.getInstrument().instrumentName or f"Instrumento {i+1}"
        for element in part.recurse().notesAndRests:
            if isinstance(element, note.Note):
                pitch_name = element.pitch.nameWithOctave
                duration = element.duration.quarterLength
                velocity = element.volume.velocity if element.volume and element.volume.velocity else 64
                dynamic = map_velocity_to_dynamic(velocity)
                voice_data.append((pitch_name, duration, dynamic, 'normal', velocity))
            elif isinstance(element, chord.Chord):
                pitch_name = element.sortAscending().pitches[-1].nameWithOctave
                duration = element.duration.quarterLength
                velocity = element.volume.velocity if element.volume and element.volume.velocity else 64
                dynamic = map_velocity_to_dynamic(velocity)
                voice_data.append((pitch_name, duration, dynamic, 'normal', velocity))
            elif isinstance(element, note.Rest):
                duration = element.duration.quarterLength
                voice_data.append(('R', duration, 'mf', 'normal', 64))
        if voice_data:
            voices.append((instrument_name, voice_data))

    if not voices:
        raise ValueError("O arquivo MIDI não contém dados de notas válidos.")
    
    return voices

def quantize_duration(duration, quantization):
    """Quantiza a duração para o valor mais próximo"""
    quantized = round(duration / quantization) * quantization
    if quantized < 0.125:
        quantized = 0.25
    if quantized > 4.0:
        quantized = 4.0
    return quantized

def adjust_pitch_to_range(note_pitch, instrument):
    """Ajusta a altura da nota ao intervalo do instrumento"""
    if note_pitch == 'R':
        return note_pitch
    
    base_instrument = instrument.split(" #")[0]
    
    if base_instrument in INSTRUMENT_RANGES:
        min_pitch, max_pitch = INSTRUMENT_RANGES[base_instrument]
    else:
        min_pitch, max_pitch = INSTRUMENT_RANGES["Violin I"]
    
    p = pitch.Pitch(note_pitch)
    min_p = pitch.Pitch(min_pitch)
    max_p = pitch.Pitch(max_pitch)
    
    while p.midi < min_p.midi:
        p.octave += 1
    while p.midi > max_p.midi:
        p.octave -= 1
    
    return p.nameWithOctave

def get_instrument(instr_name):
    """Retorna o objeto de instrumento correspondente ao nome"""
    base_name = instr_name.split(" #")[0]
    
    instr_map = {
        'Violin I': instrument.Violin(),
        'Violin II': instrument.Violin(),
        'Viola': instrument.Viola(),
        'Violoncello': instrument.Violoncello(),
        'Double Bass': instrument.Contrabass(),
        'Horn': instrument.Horn(),
        'Trumpet': instrument.Trumpet(),
        'Trombone': instrument.Trombone(),
        'Tuba': instrument.Tuba(),
        'Flute': instrument.Flute(),
        'Oboe': instrument.Oboe(),
        'Clarinet': instrument.Clarinet(),
        'Bassoon': instrument.Bassoon(),
        'Piano': instrument.Piano()
    }
    
    instr_obj = instr_map.get(base_name, instrument.Instrument())
    
    if "#" in instr_name:
        dobra_num = instr_name.split("#")[1].strip()
        instr_obj.instrumentName = f"{base_name} {dobra_num}"
    
    return instr_obj

def get_time_signature_value(time_sig_str):
    """Retorna o valor em quarterLength de uma fórmula de compasso"""
    numerator, denominator = map(int, time_sig_str.split('/'))
    beat_value = 4.0 / denominator
    measure_length = numerator * beat_value
    return measure_length

def generate_time_signature_sequence(base_time_sig, num_measures, random_changes=False):
    """
    Gera uma sequência de fórmulas de compasso para toda a composição
    
    Args:
        base_time_sig: Fórmula de compasso inicial
        num_measures: Número estimado de compassos
        random_changes: Se True, faz mudanças aleatórias
    
    Returns:
        Lista de tuplas (measure_number, time_signature)
    """
    if not random_changes:
        # Todos os compassos usam a mesma fórmula
        return [(1, base_time_sig)]
    
    # Gerar mudanças aleatórias
    available_time_sigs = ['4/4', '3/4', '2/4', '3/8', '6/8', '12/8']
    time_sig_sequence = []
    current_time_sig = base_time_sig
    
    for measure_num in range(1, num_measures + 1):
        # Chance de 15% de mudar a fórmula de compasso
        if measure_num > 1 and random.random() < 0.15:
            # Escolher nova fórmula diferente da atual
            other_sigs = [sig for sig in available_time_sigs if sig != current_time_sig]
            current_time_sig = random.choice(other_sigs)
            time_sig_sequence.append((measure_num, current_time_sig))
        elif measure_num == 1:
            # Sempre registrar o primeiro compasso
            time_sig_sequence.append((1, current_time_sig))
    
    return time_sig_sequence

def create_score(melodies, instruments, bpm, time_signature='4/4', time_sig_sequence=None):
    """Cria uma partitura a partir das melodias geradas"""
    score = stream.Score()
    score.metadata = metadata.Metadata(title="Composição Gerada por Cadeias de Markov")

    mm = tempo.MetronomeMark(number=int(bpm))
    score.insert(0, mm)
    
    ts = meter.TimeSignature(time_signature)
    score.insert(0, ts)
    
    # Criar dicionário de mudanças de compasso (measure_number -> time_signature)
    time_sig_changes = {}
    if time_sig_sequence:
        for measure_num, ts_str in time_sig_sequence:
            time_sig_changes[measure_num] = ts_str

    for melody, instr_name in zip(melodies, instruments):
        part = stream.Part()
        part.insert(0, get_instrument(instr_name))
        part.insert(0, mm)
        part.insert(0, ts)
        
        current_measure = stream.Measure(number=1)
        current_ts = time_signature
        measure_length = get_time_signature_value(current_ts)
        current_measure.insert(0, meter.TimeSignature(current_ts))
        current_measure.insert(0, mm)
        
        measure_duration = 0.0
        current_dynamic = None
        measure_count = 1
        
        for note_data in melody:
            pitch_name, duration, dyn, art, vel = note_data
            adjusted_pitch = adjust_pitch_to_range(pitch_name, instr_name)
            
            # Verificar se deve mudar a fórmula de compasso neste compasso (sincronizado)
            if measure_count in time_sig_changes and measure_duration == 0:
                new_ts = time_sig_changes[measure_count]
                if new_ts != current_ts:
                    current_ts = new_ts
                    measure_length = get_time_signature_value(current_ts)
                    current_measure.insert(0, meter.TimeSignature(current_ts))
            
            remaining_space = measure_length - measure_duration
            
            if duration > remaining_space and remaining_space > 0:
                adjusted_duration = remaining_space
            else:
                adjusted_duration = duration
            
            if adjusted_pitch == 'R':
                n = note.Rest(quarterLength=adjusted_duration)
            else:
                n = note.Note(adjusted_pitch, quarterLength=adjusted_duration)
                n.volume.velocity = vel
                
                if dyn != current_dynamic:
                    dyn_mark = dynamics.Dynamic(dyn)
                    current_measure.append(dyn_mark)
                    current_dynamic = dyn
            
            current_measure.append(n)
            measure_duration += adjusted_duration
            
            if measure_duration >= measure_length:
                part.append(current_measure)
                measure_count += 1
                current_measure = stream.Measure(number=len(part.getElementsByClass('Measure')) + 1)
                measure_duration = 0.0
                
                if duration > adjusted_duration:
                    remaining_duration = duration - adjusted_duration
                    if adjusted_pitch != 'R':
                        remaining_note = note.Note(adjusted_pitch, quarterLength=remaining_duration)
                        remaining_note.volume.velocity = vel
                        n.tie = tie.Tie('start')
                        remaining_note.tie = tie.Tie('stop')
                        current_measure.append(remaining_note)
                        measure_duration += remaining_duration
        
        if measure_duration > 0:
            if measure_duration < measure_length:
                rest_duration = measure_length - measure_duration
                current_measure.append(note.Rest(quarterLength=rest_duration))
            part.append(current_measure)
        
        part.makeNotation(inPlace=True)
        
        if part.getElementsByClass('Measure'):
            last_measure = part.getElementsByClass('Measure')[-1]
            last_measure.rightBarline = bar.Barline('final')
        
        score.append(part)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    score.metadata.date = timestamp
    
    return score

def score_to_lilypond(score):
    """
    Converte uma partitura music21 para formato LilyPond simplificado
    Versão que não requer LilyPond instalado localmente
    """
    try:
        # Mapeamento de notas para LilyPond
        def note_to_lily(note_obj):
            if isinstance(note_obj, note.Rest):
                return f"r{duration_to_lily(note_obj.duration.quarterLength)}"
            
            pitch_name = note_obj.pitch.name.lower()
            octave = note_obj.pitch.octave
            
            # Ajustar oitava para notação LilyPond (C4 = c')
            lily_octave = octave - 3
            if lily_octave > 0:
                octave_str = "'" * lily_octave
            elif lily_octave < 0:
                octave_str = "," * abs(lily_octave)
            else:
                octave_str = ""
            
            # Alterar sharp/flat
            if '#' in note_obj.pitch.name:
                pitch_name = pitch_name.replace('#', 'is')
            elif '-' in note_obj.pitch.name:
                pitch_name = pitch_name.replace('-', 'es')
            
            duration_str = duration_to_lily(note_obj.duration.quarterLength)
            
            return f"{pitch_name}{octave_str}{duration_str}"
        
        def duration_to_lily(quarter_length):
            """Converte quarterLength para notação LilyPond"""
            if quarter_length >= 4.0:
                return "1"
            elif quarter_length >= 2.0:
                return "2"
            elif quarter_length >= 1.0:
                return "4"
            elif quarter_length >= 0.5:
                return "8"
            elif quarter_length >= 0.25:
                return "16"
            else:
                return "32"
        
        # Construir código LilyPond
        lily_code = []
        lily_code.append("\\version \"2.20.0\"")
        lily_code.append("")
        lily_code.append("\\header {")
        lily_code.append(f"  title = \"{score.metadata.title or 'Composição'}\"")
        lily_code.append("}")
        lily_code.append("")
        lily_code.append("\\score {")
        lily_code.append("  <<")
        
        # Processar cada parte
        for part in score.parts[:4]:  # Limitar a 4 partes para simplicidade
            instr = part.getInstrument()
            instr_name = instr.instrumentName or "Instrumento"
            
            lily_code.append(f"    \\new Staff {{")
            lily_code.append(f"      \\set Staff.instrumentName = \"{instr_name}\"")
            
            # Pegar tempo
            tempo_marks = list(part.recurse().getElementsByClass('MetronomeMark'))
            if tempo_marks:
                bpm = int(tempo_marks[0].number)
                lily_code.append(f"      \\tempo 4 = {bpm}")
            
            # Pegar compasso
            time_sigs = list(part.recurse().getElementsByClass('TimeSignature'))
            if time_sigs:
                ts = time_sigs[0]
                lily_code.append(f"      \\time {ts.numerator}/{ts.denominator}")
            
            lily_code.append("      {")
            
            # Converter notas (primeiros 50 para não ficar muito grande)
            notes_list = list(part.recurse().notesAndRests)[:50]
            notes_str = " ".join([note_to_lily(n) for n in notes_list])
            
            # Quebrar em linhas de ~60 caracteres
            lines = []
            current_line = "        "
            for note_str in notes_str.split():
                if len(current_line) + len(note_str) > 70:
                    lines.append(current_line)
                    current_line = "        " + note_str
                else:
                    current_line += " " + note_str if current_line.strip() else note_str
            if current_line.strip():
                lines.append(current_line)
            
            lily_code.extend(lines)
            lily_code.append("      }")
            lily_code.append("    }")
        
        lily_code.append("  >>")
        lily_code.append("  \\layout { }")
        lily_code.append("  \\midi { }")
        lily_code.append("}")
        
        return "\n".join(lily_code)
        
    except Exception as e:
        # Fallback: código LilyPond mínimo
        return f"""\\version "2.20.0"

\\header {{
  title = "Composição Gerada"
}}

\\score {{
  \\new Staff {{
    \\tempo 4 = 120
    \\time 4/4
    {{ c'4 d'4 e'4 f'4 g'2 a'2 }}
  }}
  \\layout {{ }}
  \\midi {{ }}
}}

% Nota: Esta é uma versão simplificada
% A conversão completa encontrou um erro: {str(e)}
"""

def create_hacklily_url(lilypond_code):
    """Cria uma URL do Hacklily com o código LilyPond"""
    # Hacklily aceita código via URL encoding
    encoded = base64.b64encode(lilypond_code.encode()).decode()
    hacklily_url = f"https://www.hacklily.org/#code={encoded}"
    return hacklily_url

def get_audio_player_html(midi_path):
    """Cria um player de áudio HTML para o MIDI"""
    with open(midi_path, 'rb') as f:
        midi_bytes = f.read()
    midi_b64 = base64.b64encode(midi_bytes).decode()
    
    html = f"""
    <audio controls style="width: 100%;">
        <source src="data:audio/midi;base64,{midi_b64}" type="audio/midi">
        Seu navegador não suporta o elemento de áudio.
    </audio>
    """
    return html

def create_predefined_training_data():
    """Cria dados de treinamento predefinidos"""
    return [
        ("C5", 1, 64, 'normal', 64), ("C5", 1, 64, 'normal', 64), 
        ("G5", 1, 64, 'normal', 64), ("G5", 1, 64, 'normal', 64),
        ("A5", 1, 64, 'normal', 64), ("A5", 1, 64, 'normal', 64), 
        ("G5", 2, 64, 'normal', 64),
        ("F5", 1, 64, 'normal', 64), ("F5", 1, 64, 'normal', 64), 
        ("E5", 1, 64, 'normal', 64), ("E5", 1, 64, 'normal', 64),
        ("D5", 1, 64, 'normal', 64), ("D5", 1, 64, 'normal', 64), 
        ("C5", 2, 64, 'normal', 64)
    ]

# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================

def init_session_state():
    """Inicializa o estado da sessão"""
    if 'midi_voices' not in st.session_state:
        st.session_state.midi_voices = {}
    if 'selected_instruments' not in st.session_state:
        st.session_state.selected_instruments = []
    if 'voice_mappings' not in st.session_state:
        st.session_state.voice_mappings = {}
    if 'generated_score' not in st.session_state:
        st.session_state.generated_score = None
    if 'generation_log' not in st.session_state:
        st.session_state.generation_log = []

def add_log(message):
    """Adiciona mensagem ao log"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.generation_log.append(f"[{timestamp}] {message}")

def main():
    """Função principal da aplicação"""
    init_session_state()
    
    # Header
    st.markdown('<p class="main-header">🎵 Gerador Musical com Cadeias de Markov</p>', 
                unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Crie composições musicais originais usando aprendizado de máquina probabilístico</p>', 
                unsafe_allow_html=True)
    
    # Sidebar - Configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Fonte de dados
        st.subheader("📁 Fonte de Dados")
        use_midi = st.radio(
            "Escolha a fonte:",
            ["Arquivos MIDI", "Dados Predefinidos"],
            help="Arquivos MIDI: Use suas próprias músicas como base\nDados Predefinidos: Use melodia simples pré-programada"
        )
        
        uploaded_files = None
        if use_midi == "Arquivos MIDI":
            uploaded_files = st.file_uploader(
                "Envie arquivos MIDI",
                type=['mid', 'midi'],
                accept_multiple_files=True,
                help="Envie um ou mais arquivos MIDI para análise"
            )
            
            if uploaded_files:
                st.success(f"✓ {len(uploaded_files)} arquivo(s) carregado(s)")
        
        st.divider()
        
        # Seleção de instrumentos
        st.subheader("🎻 Instrumentação")
        
        # Presets rápidos
        preset = st.selectbox(
            "Preset de Instrumentos",
            ["Personalizado", "Quarteto de Cordas", "Piano Solo", "Trio de Sopros", "Orquestra Pequena"]
        )
        
        if preset == "Quarteto de Cordas":
            st.session_state.selected_instruments = ["Violin I", "Violin II", "Viola", "Violoncello"]
        elif preset == "Piano Solo":
            st.session_state.selected_instruments = ["Piano"]
        elif preset == "Trio de Sopros":
            st.session_state.selected_instruments = ["Flute", "Clarinet", "Bassoon"]
        elif preset == "Orquestra Pequena":
            st.session_state.selected_instruments = [
                "Flute", "Oboe", "Clarinet", "Bassoon",
                "Horn", "Trumpet",
                "Violin I", "Violin II", "Viola", "Violoncello"
            ]
        else:  # Personalizado
            selected = st.multiselect(
                "Selecione os instrumentos:",
                list(INSTRUMENT_RANGES.keys()),
                default=st.session_state.selected_instruments
            )
            st.session_state.selected_instruments = selected
        
        # Mostrar instrumentos selecionados
        if st.session_state.selected_instruments:
            st.info(f"📋 {len(st.session_state.selected_instruments)} instrumento(s) selecionado(s)")
        
        st.divider()
        
        # Parâmetros de geração
        st.subheader("🎛️ Parâmetros")
        
        order = st.slider(
            "Ordem da Cadeia de Markov",
            min_value=1,
            max_value=3,
            value=1,
            help="Ordem maior = mais fiel ao original, mas menos variação"
        )
        
        quantization_name = st.selectbox(
            "Quantização Rítmica",
            list(QUANTIZATION_OPTIONS.keys()),
            index=1  # Colcheia por padrão
        )
        quantization = QUANTIZATION_OPTIONS[quantization_name]
        
        melody_length = st.slider(
            "Comprimento da Melodia (notas)",
            min_value=20,
            max_value=500,
            value=100,
            step=10
        )
        
        bpm = st.slider(
            "BPM (Tempo)",
            min_value=40,
            max_value=240,
            value=120,
            step=5
        )
        
        time_signature = st.selectbox(
            "Fórmula de Compasso",
            TIME_SIGNATURES,
            index=0  # 4/4 por padrão
        )
        
        random_time_changes = st.checkbox(
            "Mudanças Aleatórias de Compasso",
            value=False,
            help="Altera aleatoriamente a fórmula de compasso durante a música (sincronizado em todos os instrumentos)"
        )
        
        if random_time_changes:
            st.info("💡 As mudanças de compasso ocorrerão simultaneamente em todos os instrumentos")
        
        st.divider()
        
        # Botão de geração
        generate_button = st.button(
            "🎼 Gerar Música",
            type="primary",
            use_container_width=True
        )
    
    # Área principal
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎹 Geração", 
        "📊 Visualização & Playback", 
        "📈 Análise", 
        "ℹ️ Sobre"
    ])
    
    # TAB 1: Geração
    with tab1:
        st.header("Processo de Geração")
        
        if generate_button:
            # Validações
            if use_midi == "Arquivos MIDI" and not uploaded_files:
                st.error("❌ Por favor, envie arquivos MIDI primeiro!")
                return
            
            if not st.session_state.selected_instruments:
                st.error("❌ Por favor, selecione pelo menos um instrumento!")
                return
            
            # Limpar log anterior
            st.session_state.generation_log = []
            add_log("Iniciando geração de música...")
            
            # Container de progresso
            progress_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # PASSO 1: Carregar dados de treinamento
                    status_text.text("📂 Carregando dados de treinamento...")
                    progress_bar.progress(10)
                    
                    training_data_dict = {}
                    
                    if use_midi == "Arquivos MIDI":
                        # Salvar arquivos temporariamente e processar
                        temp_dir = tempfile.mkdtemp()
                        all_voices = {}
                        
                        for uploaded_file in uploaded_files:
                            temp_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(temp_path, 'wb') as f:
                                f.write(uploaded_file.getbuffer())
                            
                            voices = load_midi_file(temp_path)
                            for voice_name, voice_data in voices:
                                if voice_name in all_voices:
                                    all_voices[voice_name].extend(voice_data)
                                else:
                                    all_voices[voice_name] = voice_data
                        
                        st.session_state.midi_voices = all_voices
                        add_log(f"Carregadas {len(all_voices)} vozes dos arquivos MIDI")
                        
                        # Mapear instrumentos para vozes
                        for instr in st.session_state.selected_instruments:
                            if all_voices:
                                # Usar a primeira voz disponível (simplificado)
                                first_voice = list(all_voices.keys())[0]
                                training_data_dict[instr] = all_voices[first_voice]
                        
                        # Limpar arquivos temporários
                        shutil.rmtree(temp_dir)
                    else:
                        # Usar dados predefinidos
                        for instr in st.session_state.selected_instruments:
                            training_data_dict[instr] = create_predefined_training_data()
                        add_log("Usando dados predefinidos para treinamento")
                    
                    progress_bar.progress(25)
                    
                    # PASSO 2: Treinar modelos
                    status_text.text("🧠 Treinando modelos de Markov...")
                    models = {}
                    
                    # Agrupar instrumentos base
                    grouped_instruments = {}
                    for instrument in training_data_dict.keys():
                        base_instr = instrument.split(" #")[0]
                        if base_instr not in grouped_instruments:
                            grouped_instruments[base_instr] = []
                        grouped_instruments[base_instr].append(instrument)
                    
                    for base_instr, instr_list in grouped_instruments.items():
                        add_log(f"Treinando modelo para {base_instr}...")
                        
                        training_data = training_data_dict[instr_list[0]]
                        
                        # Quantizar durações
                        quantized_data = [
                            (pitch, quantize_duration(duration, quantization), dynamic, articulation, velocity)
                            for pitch, duration, dynamic, articulation, velocity in training_data
                        ]
                        
                        # Criar estados únicos
                        states = list(set(quantized_data))
                        model = MarkovChainMelodyGenerator(states, order)
                        model.train(quantized_data)
                        
                        for instrument in instr_list:
                            models[instrument] = model
                    
                    progress_bar.progress(50)
                    
                    # PASSO 3: Gerar melodias
                    status_text.text("🎵 Gerando melodias...")
                    melodies = []
                    instruments = []
                    
                    for base_instr, instr_list in grouped_instruments.items():
                        model = models[instr_list[0]]
                        add_log(f"Gerando melodias para {base_instr}...")
                        
                        melodies_dict = model.generate_all_sequences(instr_list, melody_length)
                        
                        for instrument in instr_list:
                            melody = melodies_dict[instrument]
                            adjusted_melody = [
                                (adjust_pitch_to_range(note[0], instrument), note[1], note[2], note[3], note[4])
                                for note in melody
                            ]
                            melodies.append(adjusted_melody)
                            instruments.append(instrument)
                    
                    progress_bar.progress(75)
                    
                    # PASSO 4: Criar partitura
                    status_text.text("📝 Criando partitura...")
                    
                    # Gerar sequência de mudanças de compasso (sincronizada para todos os instrumentos)
                    time_sig_sequence = None
                    if random_time_changes:
                        # Estimar número de compassos
                        avg_note_duration = 0.75
                        avg_measure_length = 3.5
                        estimated_total_duration = melody_length * avg_note_duration
                        estimated_measures = int(estimated_total_duration / avg_measure_length) + 10
                        
                        add_log(f"Gerando mudanças aleatórias de compasso (~{estimated_measures} compassos)")
                        time_sig_sequence = generate_time_signature_sequence(
                            time_signature, 
                            estimated_measures, 
                            random_changes=True
                        )
                        
                        # Log das mudanças geradas
                        changes_text = ", ".join([f"c.{num}:{sig}" for num, sig in time_sig_sequence[:10]])
                        if len(time_sig_sequence) > 10:
                            changes_text += "..."
                        add_log(f"Mudanças de compasso: {changes_text}")
                    
                    score = create_score(melodies, instruments, bpm, time_signature, time_sig_sequence)
                    st.session_state.generated_score = score
                    add_log("Partitura criada com sucesso!")
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Geração concluída!")
                    
                    st.success("🎉 Música gerada com sucesso! Veja as abas 'Visualização & Playback' e 'Análise'")
                    
                except Exception as e:
                    st.error(f"❌ Erro durante a geração: {str(e)}")
                    add_log(f"ERRO: {str(e)}")
        
        # Mostrar log
        if st.session_state.generation_log:
            st.subheader("📋 Log de Geração")
            log_container = st.container()
            with log_container:
                for log_entry in st.session_state.generation_log:
                    st.text(log_entry)
    
    # TAB 2: Visualização & Playback
    with tab2:
        st.header("Visualização da Partitura e Playback")
        
        if st.session_state.generated_score is None:
            st.info("👈 Gere uma música primeiro na aba 'Geração'")
        else:
            score = st.session_state.generated_score
            
            # Criar arquivos temporários
            temp_dir = tempfile.mkdtemp()
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            
            # Salvar MusicXML
            xml_path = os.path.join(temp_dir, f"composition_{timestamp}.musicxml")
            score.write('musicxml', fp=xml_path)
            
            # Salvar MIDI
            midi_path = os.path.join(temp_dir, f"composition_{timestamp}.mid")
            score.write('midi', fp=midi_path)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📥 Downloads")
                
                st.markdown("**🎼 Para MuseScore (Recomendado)**")
                # Botão download MusicXML
                with open(xml_path, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download MusicXML para MuseScore",
                        data=f,
                        file_name=f"composition_{timestamp}.musicxml",
                        mime="application/xml",
                        help="Arquivo MusicXML - Abra no MuseScore, Finale, Sibelius ou qualquer editor de partituras"
                    )
                
                st.markdown("---")
                st.markdown("**🎹 Para DAWs e Players**")
                # Botão download MIDI
                with open(midi_path, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download MIDI",
                        data=f,
                        file_name=f"composition_{timestamp}.mid",
                        mime="audio/midi",
                        help="Arquivo MIDI - Use em Ableton, FL Studio, Logic Pro ou qualquer DAW"
                    )
                
                st.markdown("---")
                st.info("💡 **Como abrir no MuseScore:**\n1. Baixe o arquivo MusicXML\n2. Abra o MuseScore\n3. Arquivo → Abrir\n4. Selecione o arquivo baixado")
            
            with col2:
                st.subheader("🎼 Informações")
                st.write(f"**Instrumentos:** {len(score.parts)}")
                st.write(f"**Compassos:** ~{len(score.parts[0].getElementsByClass('Measure')) if score.parts else 0}")
                st.write(f"**Tempo:** {bpm} BPM")
                st.write(f"**Compasso:** {time_signature}")
                
                if random_time_changes:
                    st.write(f"**Mudanças de Compasso:** ✅ Ativadas")
                else:
                    st.write(f"**Mudanças de Compasso:** ❌ Desativadas")
                
                st.markdown("---")
                st.markdown("**📊 Formatos Disponíveis:**")
                st.markdown("""
                - **MusicXML**: Partitura editável
                - **MIDI**: Áudio sequenciado
                """)
            
            st.divider()
            
            # Player de MIDI
            st.subheader("🔊 Player de Áudio")
            st.info("💡 Dica: O playback de MIDI pode não funcionar em todos os navegadores. Use o download do arquivo MIDI para melhor qualidade.")
            
            try:
                audio_html = get_audio_player_html(midi_path)
                st.markdown(audio_html, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Player de áudio não disponível: {str(e)}")
            
            st.divider()
            
            # Visualização com Hacklily
            st.subheader("👁️ Visualização da Partitura")
            
            viz_option = st.radio(
                "Escolha o método de visualização:",
                ["PNG (Rápido)", "Hacklily (Interativo)"],
                horizontal=True
            )
            
            if viz_option == "PNG (Rápido)":
                try:
                    # Tentar gerar PNG usando music21
                    st.info("Gerando visualização da partitura...")
                    png_path = os.path.join(temp_dir, f"score_{timestamp}.png")
                    
                    # music21 pode gerar PNG se MuseScore ou Lilypond estiverem instalados
                    score.write('musicxml.png', fp=png_path)
                    
                    if os.path.exists(png_path):
                        st.image(png_path, caption="Partitura Gerada")
                    else:
                        st.warning("Não foi possível gerar a visualização PNG. Instale o MuseScore ou Lilypond.")
                except Exception as e:
                    st.warning("Visualização PNG não disponível. Tente o método Hacklily ou faça o download do MusicXML.")
            
            else:  # Hacklily
                st.info("🌐 **Visualização Online com Hacklily** - Não requer instalação!")
                
                try:
                    with st.spinner("Gerando código LilyPond..."):
                        # Converter para LilyPond (usa função simplificada que não precisa de instalação)
                        lilypond_code = score_to_lilypond(score)
                    
                    # Criar URL do Hacklily
                    hacklily_url = create_hacklily_url(lilypond_code)
                    
                    st.success("✅ Código LilyPond gerado com sucesso!")
                    
                    st.markdown(f"""
                    <div class="info-box">
                    <p><strong>🔗 Visualização Interativa</strong></p>
                    <p>Clique no botão abaixo para abrir a partitura no Hacklily (nova aba):</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.link_button("🎼 Abrir Partitura no Hacklily", hacklily_url, type="primary")
                    
                    st.markdown("---")
                    
                    # Também mostrar o código LilyPond
                    with st.expander("📄 Ver código LilyPond (para desenvolvedores)"):
                        st.code(lilypond_code, language="text")
                        st.caption("💡 Você pode copiar este código e usar em qualquer editor LilyPond")
                    
                except Exception as e:
                    st.error("❌ Erro ao gerar visualização LilyPond")
                    st.warning(f"""
                    **Detalhes do erro:** {str(e)}
                    
                    **💡 Soluções alternativas:**
                    1. Use a opção "PNG (Rápido)" se tiver o MuseScore instalado
                    2. Baixe o arquivo MusicXML e abra no MuseScore
                    3. Baixe o arquivo MIDI e use em qualquer player
                    
                    **Nota:** Este erro não afeta os downloads. Os arquivos MusicXML e MIDI 
                    estão prontos para uso!
                    """)
            
            # Limpar arquivos temporários ao final da sessão
            # (Streamlit gerenciará isso automaticamente ao recarregar)
    
    # TAB 3: Análise
    with tab3:
        st.header("Análise das Cadeias de Markov")
        
        if st.session_state.generated_score is None:
            st.info("👈 Gere uma música primeiro na aba 'Geração'")
        else:
            st.subheader("📊 Estatísticas da Composição")
            
            score = st.session_state.generated_score
            
            # Análise básica
            num_parts = len(score.parts)
            total_measures = sum(len(part.getElementsByClass('Measure')) for part in score.parts)
            avg_measures = total_measures / num_parts if num_parts > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Instrumentos", num_parts)
            with col2:
                st.metric("Compassos Totais", total_measures)
            with col3:
                st.metric("Média por Parte", f"{avg_measures:.1f}")
            with col4:
                st.metric("Notas Geradas", melody_length * num_parts)
            
            st.divider()
            
            # Análise por instrumento
            st.subheader("🎻 Análise por Instrumento")
            
            instrument_data = []
            for part in score.parts:
                instr_name = part.getInstrument().instrumentName or "Desconhecido"
                notes = list(part.recurse().notes)
                rests = list(part.recurse().getElementsByClass('Rest'))
                
                pitches = [n.pitch.nameWithOctave for n in notes if hasattr(n, 'pitch')]
                highest = max(pitches, key=lambda p: pitch.Pitch(p).midi) if pitches else "N/A"
                lowest = min(pitches, key=lambda p: pitch.Pitch(p).midi) if pitches else "N/A"
                
                instrument_data.append({
                    "Instrumento": instr_name,
                    "Notas": len(notes),
                    "Pausas": len(rests),
                    "Nota Mais Aguda": highest,
                    "Nota Mais Grave": lowest
                })
            
            df = pd.DataFrame(instrument_data)
            st.dataframe(df, use_container_width=True)
            
            st.divider()
            
            # Informações sobre o modelo
            st.subheader("🧠 Informações do Modelo")
            
            st.markdown(f"""
            <div class="info-box">
            <p><strong>Parâmetros Utilizados:</strong></p>
            <ul>
                <li><strong>Ordem da Cadeia:</strong> {order}</li>
                <li><strong>Quantização:</strong> {quantization_name} ({quantization} quarterLength)</li>
                <li><strong>Comprimento:</strong> {melody_length} notas por instrumento</li>
                <li><strong>Tempo:</strong> {bpm} BPM</li>
                <li><strong>Compasso:</strong> {time_signature}</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # TAB 4: Sobre
    with tab4:
        st.header("Sobre o Gerador Musical")
        
        st.markdown("""
        ### 🎵 O que é este projeto?
        
        Este é um gerador de música baseado em **Cadeias de Markov**, uma técnica de aprendizado de máquina 
        probabilístico que analisa padrões em músicas existentes e cria novas composições originais.
        
        ### 🧠 Como funciona?
        
        1. **Análise**: O sistema lê arquivos MIDI e extrai informações sobre:
           - Alturas das notas (pitch)
           - Durações rítmicas
           - Dinâmicas (intensidade)
           - Articulações
        
        2. **Treinamento**: Constrói matrizes de probabilidade que capturam:
           - Quais notas tendem a seguir outras notas
           - Padrões rítmicos comuns
           - Variações de intensidade
        
        3. **Geração**: Cria novas melodias usando:
           - Seleção probabilística baseada nos padrões aprendidos
           - Ajuste automático de tessitura para cada instrumento
           - Manutenção de características estilísticas
        
        ### 📚 Tecnologias Utilizadas
        
        - **Streamlit**: Framework web interativo
        - **music21**: Processamento e análise musical
        - **NumPy**: Computação numérica
        - **LilyPond**: Renderização de partituras
        - **Hacklily**: Visualização interativa online
        
        ### 🎼 Recursos
        
        - ✅ Upload de múltiplos arquivos MIDI
        - ✅ Suporte a 14 instrumentos diferentes
        - ✅ Presets de instrumentação (Quarteto, Orquestra, etc.)
        - ✅ Parâmetros ajustáveis de geração
        - ✅ Visualização de partituras
        - ✅ Playback de áudio (MIDI)
        - ✅ Download em MusicXML e MIDI
        - ✅ Análise estatística detalhada
        
        ### 🔬 Conceitos Musicais
        
        **Cadeia de Markov**: Modelo probabilístico onde o próximo estado depende apenas do(s) estado(s) atual(is).
        
        **Ordem da Cadeia**:
        - Ordem 1: Próxima nota depende apenas da nota atual
        - Ordem 2: Depende das 2 notas anteriores
        - Ordem 3: Depende das 3 notas anteriores
        
        **Quantização**: Arredondamento de durações para simplificar o modelo e reduzir a complexidade.
        
        ### 👨‍💻 Desenvolvido com
        
        - Python 3.x
        - Streamlit 1.x
        - music21 9.x
        
        ### 📖 Referências
        
        - [music21 Documentation](http://web.mit.edu/music21/)
        - [Markov Chains in Music Generation](https://en.wikipedia.org/wiki/Markov_chain)
        - [Hacklily - Online LilyPond Editor](https://www.hacklily.org/)
        
        ---
        
        **Versão**: 2.0 Web  
        **Data**: Outubro 2025  
        **Licença**: MIT
        """)

if __name__ == "__main__":
    main()