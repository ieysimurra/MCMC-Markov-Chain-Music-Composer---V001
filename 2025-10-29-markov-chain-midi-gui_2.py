import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import numpy as np
import random
from music21 import converter, note, chord, stream, instrument, layout, metadata, meter, clef, bar, tempo, dynamics, articulations, pitch, tie
import time
import csv
import subprocess
import sys
import platform
import shutil

# Definições de instrumentos e seus intervalos (ranges)
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

class MarkovChainMelodyGenerator:
    """Classe que implementa o gerador de melodia com cadeia de Markov"""
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

    def generate_all_sequences(self, instruments, length):
        """Gera sequências independentes para cada instrumento usando a mesma matriz"""
        melodies_dict = {}
        sequences_data = {}
        
        for instrument in instruments:
            pitch_sequence = self._generate_sequence(length, self.pitch_matrix)
            duration_sequence = self._generate_sequence(length, self.duration_matrix)
            velocity_sequence = self._generate_sequence(length, self.velocity_matrix)
            
            # Combinar as sequências em notas
            melody = []
            for i in range(length):
                # Gerar dinâmica a partir da velocity
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
    
    def export_analysis_data(self, filename_prefix):
        """Exporta as matrizes de transição e as sequências geradas"""
        # Exportar apenas as matrizes necessárias
        self._export_matrix(self.pitch_matrix, f"{filename_prefix}_pitch_matrix.csv")
        self._export_matrix(self.duration_matrix, f"{filename_prefix}_duration_matrix.csv")
        self._export_matrix(self.velocity_matrix, f"{filename_prefix}_velocity_matrix.csv")
        
        # Exportar sequências geradas para cada instrumento
        for instrument, sequences in self.generated_sequences.items():
            self._export_sequences(sequences, f"{filename_prefix}_{instrument}_sequences.csv")
    
    def _export_sequences(self, sequences, filename):
        """Exporta as sequências geradas para um arquivo CSV"""
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            # Escrever cabeçalho
            writer.writerow(['Index', 'Pitch', 'Duration', 'Velocity'])
            
            # Escrever dados
            for i in range(len(sequences['pitch'])):
                writer.writerow([
                    i,
                    sequences['pitch'][i],
                    sequences['duration'][i],
                    sequences['velocity'][i]
                ])
    
    def train(self, notes):
        if not notes:
            raise ValueError("A lista de notas para treinamento não pode estar vazia.")
        self._calculate_initial_probabilities(notes)
        self._calculate_transition_matrix(notes)
        self._calculate_separate_matrices(notes)

    def generate(self, length):
        if not self.states:
            raise ValueError("Não há estados para gerar a melodia.")
        melody = list(self._generate_starting_state())
        
        # Garantir que o estado inicial tenha 5 elementos
        if len(melody[0]) == 4:  # Se o estado inicial tiver apenas 4 elementos
            melody = [(note[0], note[1], note[2], note[3], 64) for note in melody]  # Adicionar velocity padrão
            
        for _ in range(self.order, length):
            prev_states = tuple(melody[-self.order:])
            next_state = self._generate_next_state(prev_states)
            # Garantir que o próximo estado tenha 5 elementos
            if len(next_state) == 4:
                next_state = (next_state[0], next_state[1], next_state[2], next_state[3], 64)
            melody.append(next_state)
        return melody

    def _calculate_initial_probabilities(self, notes):
        for i in range(len(notes) - self.order + 1):
            state = tuple(notes[i:i+self.order])
            self.initial_probabilities[state] = self.initial_probabilities.get(state, 0) + 1
        total = sum(self.initial_probabilities.values())
        for state in self.initial_probabilities:
            self.initial_probabilities[state] /= total

    def _calculate_transition_matrix(self, notes):
        for i in range(len(notes) - self.order):
            current_state = tuple(notes[i:i+self.order])
            next_state = notes[i+self.order]
            if current_state not in self.transition_matrix:
                self.transition_matrix[current_state] = {}
            self.transition_matrix[current_state][next_state] = self.transition_matrix[current_state].get(next_state, 0) + 1
        
        for current_state in self.transition_matrix:
            total = sum(self.transition_matrix[current_state].values())
            for next_state in self.transition_matrix[current_state]:
                self.transition_matrix[current_state][next_state] /= total

    def _generate_starting_state(self):
        return random.choices(list(self.initial_probabilities.keys()), 
                              weights=list(self.initial_probabilities.values()))[0]

    def _generate_next_state(self, current_state):
        if current_state in self.transition_matrix:
            next_states = list(self.transition_matrix[current_state].keys())
            probabilities = list(self.transition_matrix[current_state].values())
            next_state = random.choices(next_states, weights=probabilities)[0]
            # Garantir que o estado tenha 5 elementos
            if len(next_state) == 4:
                return (next_state[0], next_state[1], next_state[2], next_state[3], 64)
            return next_state
        random_state = random.choice(self.states)
        # Garantir que o estado aleatório tenha 5 elementos
        if len(random_state) == 4:
            return (random_state[0], random_state[1], random_state[2], random_state[3], 64)
        return random_state
    
    def _calculate_separate_matrices(self, notes):
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

        # Normalize matrices
        self._normalize_matrix(self.pitch_matrix)
        self._normalize_matrix(self.duration_matrix)
        self._normalize_matrix(self.velocity_matrix)

    def _normalize_matrix(self, matrix):
        for state in matrix:
            total = sum(matrix[state].values())
            for next_state in matrix[state]:
                matrix[state][next_state] /= total

    def _export_matrix(self, matrix, filename):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            states = sorted(matrix.keys())
            writer.writerow([''] + states)
            for state in states:
                row = [state] + [matrix[state].get(next_state, 0) for next_state in states]
                writer.writerow(row)
                
def map_velocity_to_dynamic(velocity):
    """
    Mapeia velocity MIDI (0-127) para dinâmicas musicais
    
    Mapeamento:
    0-15   → ppp (pianississimo)
    16-31  → pp  (pianissimo)
    32-47  → p   (piano)
    48-63  → mp  (mezzo-piano)
    64-79  → mf  (mezzo-forte)
    80-95  → f   (forte)
    96-111 → ff  (fortissimo)
    112-127→ fff (fortississimo)
    """
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

def find_musescore():
    """Localiza o executável do MuseScore no sistema"""
    # Primeiro tenta usar o comando 'which' ou 'where' do sistema
    system = platform.system()
    
    # Lista de possíveis nomes de executáveis
    possible_names = ['musescore', 'mscore', 'MuseScore', 'musescore3', 'musescore4']
    
    # Tentar encontrar usando shutil.which (funciona em todos os sistemas)
    for name in possible_names:
        musescore_path = shutil.which(name)
        if musescore_path:
            return musescore_path
    
    # Caminhos comuns no Windows
    if system == 'Windows':
        common_paths = [
            r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe",
            r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe",
            r"C:\Program Files (x86)\MuseScore 4\bin\MuseScore4.exe",
            r"C:\Program Files (x86)\MuseScore 3\bin\MuseScore3.exe",
            r"C:\Program Files\MuseScore\bin\MuseScore.exe",
            r"C:\Program Files (x86)\MuseScore\bin\MuseScore.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    
    # Caminhos comuns no macOS
    elif system == 'Darwin':
        common_paths = [
            '/Applications/MuseScore 4.app/Contents/MacOS/mscore',
            '/Applications/MuseScore 3.app/Contents/MacOS/mscore',
            '/Applications/MuseScore.app/Contents/MacOS/mscore',
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    
    # No Linux, geralmente está no PATH, mas vamos verificar alguns locais comuns
    elif system == 'Linux':
        common_paths = [
            '/usr/bin/musescore',
            '/usr/bin/mscore',
            '/usr/local/bin/musescore',
            '/usr/local/bin/mscore',
            '/snap/bin/musescore',
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    
    return None

def open_with_musescore(file_path):
    """Abre um arquivo com o MuseScore"""
    musescore_path = find_musescore()
    
    if not musescore_path:
        return False, "MuseScore não encontrado no sistema"
    
    try:
        # Converter o caminho para absoluto
        abs_file_path = os.path.abspath(file_path)
        
        # Tentar abrir o arquivo
        if platform.system() == 'Windows':
            # No Windows, usar startfile como fallback ou subprocess
            try:
                os.startfile(abs_file_path)
                return True, f"Arquivo aberto com sucesso"
            except:
                subprocess.Popen([musescore_path, abs_file_path])
                return True, f"Arquivo aberto com MuseScore: {musescore_path}"
        else:
            # Linux e macOS
            subprocess.Popen([musescore_path, abs_file_path])
            return True, f"Arquivo aberto com MuseScore: {musescore_path}"
            
    except Exception as e:
        return False, f"Erro ao abrir MuseScore: {str(e)}"

def load_midi_file(file_path):
    """Carrega um arquivo MIDI e extrai as informações de notas"""
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
                articulation = 'normal'
                for art in element.articulations:
                    articulation = art.name
                    break
                voice_data.append((pitch_name, duration, dynamic, articulation, velocity))
            elif isinstance(element, chord.Chord):
                pitch_name = element.sortAscending().pitches[-1].nameWithOctave
                duration = element.duration.quarterLength
                velocity = element.volume.velocity if element.volume and element.volume.velocity else 64
                dynamic = map_velocity_to_dynamic(velocity)
                articulation = 'normal'
                for art in element.articulations:
                    articulation = art.name
                    break
                voice_data.append((pitch_name, duration, dynamic, articulation, velocity))
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
    
    # Evitar durações muito pequenas (menores que fusa)
    if quantized < 0.125:
        quantized = 0.25
    
    # Evitar durações muito grandes (maiores que semibreve)
    if quantized > 4.0:
        quantized = 4.0
        
    return quantized

def quantize_to_measure(duration, remaining_space, quantization):
    """
    Quantiza uma duração para caber no espaço restante do compasso
    
    Args:
        duration: Duração desejada
        remaining_space: Espaço restante no compasso atual
        quantization: Valor de quantização
    
    Returns:
        Duração ajustada que cabe no compasso
    """
    # Primeiro, quantizar normalmente
    quantized = quantize_duration(duration, quantization)
    
    # Se a duração quantizada cabe no espaço restante, usar ela
    if quantized <= remaining_space:
        return quantized
    
    # Caso contrário, ajustar para caber exatamente
    # Tentar durações menores que sejam múltiplos da quantização
    possible_durations = []
    test_duration = quantization
    
    while test_duration <= remaining_space:
        possible_durations.append(test_duration)
        test_duration += quantization
    
    # Se encontrou durações possíveis, usar a maior
    if possible_durations:
        return possible_durations[-1]
    
    # Último recurso: usar o espaço restante exato
    return remaining_space

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

def get_time_signature_value(time_sig_str):
    """
    Retorna o valor em quarterLength de uma fórmula de compasso
    
    Args:
        time_sig_str: String como '4/4', '3/4', '6/8', etc.
    
    Returns:
        Valor em quarterLength (ex: 4/4 = 4.0, 6/8 = 3.0)
    """
    numerator, denominator = map(int, time_sig_str.split('/'))
    
    # Calcular o valor em quarterLength
    # denominador 4 = semínima (1.0)
    # denominador 8 = colcheia (0.5)
    # denominador 2 = mínima (2.0)
    beat_value = 4.0 / denominator
    measure_length = numerator * beat_value
    
    return measure_length

def create_predefined_training_data():
    """Cria dados de treinamento predefinidos para o caso de não usar arquivos MIDI"""
    return [
        ("C5", 1, 64, 'normal', 64), ("C5", 1, 64, 'normal', 64), ("G5", 1, 64, 'normal', 64), ("G5", 1, 64, 'normal', 64),
        ("A5", 1, 64, 'normal', 64), ("A5", 1, 64, 'normal', 64), ("G5", 2, 64, 'normal', 64),
        ("F5", 1, 64, 'normal', 64), ("F5", 1, 64, 'normal', 64), ("E5", 1, 64, 'normal', 64), ("E5", 1, 64, 'normal', 64),
        ("D5", 1, 64, 'normal', 64), ("D5", 1, 64, 'normal', 64), ("C5", 2, 64, 'normal', 64)
    ]

def create_states_from_training_data(training_data):
    """Cria estados a partir de dados de treinamento"""
    return list(set(training_data))

def adjust_pitch_to_range(note_pitch, instrument):
    """Ajusta a altura da nota ao intervalo do instrumento"""
    if note_pitch == 'R':
        return note_pitch
    
    # Remover qualquer sufixo de dobra (#1, #2, etc.)
    base_instrument = instrument.split(" #")[0]
    
    # Obter o range do instrumento base
    if base_instrument in INSTRUMENT_RANGES:
        min_pitch, max_pitch = INSTRUMENT_RANGES[base_instrument]
    else:
        # Fallback para Violin I se o instrumento não for reconhecido
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
    """Retorna o objeto de instrumento correspondente ao nome, suportando dobras"""
    # Remover qualquer sufixo de dobra (#1, #2, etc.)
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
    
    # Personalizar o nome do instrumento para incluir o número da dobra, se existir
    if "#" in instr_name:
        # Extrair o número da dobra
        dobra_num = instr_name.split("#")[1].strip()
        # Personalizar o nome do instrumento
        instr_obj.instrumentName = f"{base_name} {dobra_num}"
    
    return instr_obj

def save_and_show_score(score, timestamp):
    """Salva a partitura em diferentes formatos e tenta abri-la no MuseScore"""
    # Criar diretório para os arquivos se não existir
    output_dir = "generated_scores"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Base do nome do arquivo
    base_filename = f"markov_composition_{timestamp}"
    musescore_message = ""
    
    try:
        # Salvar como MusicXML
        xml_path = os.path.join(output_dir, f"{base_filename}.musicxml")
        score.write('musicxml', fp=xml_path)
        
        # Salvar como MIDI
        midi_path = os.path.join(output_dir, f"{base_filename}.mid")
        score.write('midi', fp=midi_path)
        
        # Tentar abrir no MuseScore
        success, message = open_with_musescore(xml_path)
        
        if success:
            musescore_message = f"✓ Partitura aberta no MuseScore"
        else:
            musescore_message = f"⚠ {message}"
            # Tentar método alternativo do music21
            try:
                score.show()
                musescore_message += " | Tentativa alternativa com music21.show() executada"
            except Exception as e:
                musescore_message += f" | Abra manualmente: {os.path.abspath(xml_path)}"
        
        return xml_path, midi_path, musescore_message
        
    except Exception as e:
        return None, None, f"Erro ao salvar: {str(e)}"

def visualize_multi_voice_melody(melodies, instruments, bpm, time_signature='4/4', time_sig_sequence=None):
    """
    Cria uma partitura a partir das melodias geradas para cada instrumento
    
    Args:
        melodies: Lista de melodias (uma por instrumento)
        instruments: Lista de nomes de instrumentos
        bpm: Tempo em batidas por minuto
        time_signature: Fórmula de compasso inicial ('4/4', '3/4', '2/4', '3/8', '6/8', '12/8')
        time_sig_sequence: Lista de tuplas (measure_number, time_signature) para mudanças sincronizadas
    """
    score = stream.Score()
    score.metadata = metadata.Metadata(title="Melodias Geradas por Cadeias de Markov")

    # Criar o MetronomeMark com o BPM definido pelo usuário
    mm = tempo.MetronomeMark(number=int(bpm))
    
    # Adicionar indicação de tempo no início da partitura
    score.insert(0, mm)
    
    # Adicionar também uma indicação textual do tempo
    tempo_text = tempo.TempoText(f'♩ = {bpm}')
    score.insert(0, tempo_text)
    
    # Criar time signature inicial
    ts = meter.TimeSignature(time_signature)
    score.insert(0, ts)
    
    # Criar dicionário de mudanças de compasso (measure_number -> time_signature)
    time_sig_changes = {}
    if time_sig_sequence:
        for measure_num, ts_str in time_sig_sequence:
            time_sig_changes[measure_num] = ts_str

    # Processar cada instrumento
    for i, (melody, instr_name) in enumerate(zip(melodies, instruments)):
        # Criar a parte para o instrumento
        part = stream.Part()
        
        # Adicionar instrumento e configurações iniciais
        part.insert(0, get_instrument(instr_name))
        part.insert(0, mm)  # Adicionar tempo para cada parte
        part.insert(0, ts)  # Adicionar time signature para cada parte
        
        # Variáveis de controle
        current_measure = stream.Measure(number=1)
        current_ts = time_signature
        measure_length = get_time_signature_value(current_ts)
        current_measure.insert(0, meter.TimeSignature(current_ts))
        current_measure.insert(0, mm)
        
        measure_duration = 0.0
        current_dynamic = None
        measure_count = 1
        
        # Processar cada nota da melodia
        for note_idx, note_data in enumerate(melody):
            pitch_name, duration, dyn, art, vel = note_data
            adjusted_pitch = adjust_pitch_to_range(pitch_name, instr_name)
            
            # Verificar se deve mudar a fórmula de compasso neste compasso (sincronizado)
            if measure_count in time_sig_changes and measure_duration == 0:
                new_ts = time_sig_changes[measure_count]
                if new_ts != current_ts:
                    current_ts = new_ts
                    measure_length = get_time_signature_value(current_ts)
                    current_measure.insert(0, meter.TimeSignature(current_ts))
            
            # Ajustar duração para caber no compasso
            remaining_space = measure_length - measure_duration
            
            if duration > remaining_space and remaining_space > 0:
                # Se a nota não cabe, dividir em duas notas ligadas
                adjusted_duration = remaining_space
            else:
                adjusted_duration = duration
            
            # Criar nota ou pausa
            if adjusted_pitch == 'R':
                n = note.Rest(quarterLength=adjusted_duration)
            else:
                n = note.Note(adjusted_pitch, quarterLength=adjusted_duration)
                n.volume.velocity = vel
                
                # Adicionar dinâmica se mudou
                if dyn != current_dynamic:
                    dyn_mark = dynamics.Dynamic(dyn)
                    current_measure.append(dyn_mark)
                    current_dynamic = dyn
                
                # Adicionar articulação se necessário
                if art != 'normal':
                    try:
                        n.articulations.append(getattr(articulations, art)())
                    except:
                        pass  # Ignorar articulações inválidas
            
            current_measure.append(n)
            measure_duration += adjusted_duration
            
            # Se o compasso está cheio, adicionar à parte e criar novo
            if measure_duration >= measure_length:
                part.append(current_measure)
                measure_count += 1
                current_measure = stream.Measure(number=len(part.getElementsByClass('Measure')) + 1)
                measure_duration = 0.0
                
                # Se havia nota que não coube, adicionar a parte restante
                if duration > adjusted_duration:
                    remaining_duration = duration - adjusted_duration
                    
                    if adjusted_pitch != 'R':
                        remaining_note = note.Note(adjusted_pitch, quarterLength=remaining_duration)
                        remaining_note.volume.velocity = vel
                        # Ligar as notas
                        n.tie = tie.Tie('start')
                        remaining_note.tie = tie.Tie('stop')
                        current_measure.append(remaining_note)
                        measure_duration += remaining_duration
        
        # Adicionar último compasso se houver notas restantes
        if measure_duration > 0:
            # Preencher o compasso com pausa se necessário
            if measure_duration < measure_length:
                rest_duration = measure_length - measure_duration
                current_measure.append(note.Rest(quarterLength=rest_duration))
            part.append(current_measure)
        
        # Fazer notação
        part.makeNotation(inPlace=True)
        
        # Adicionar barra final
        if part.getElementsByClass('Measure'):
            last_measure = part.getElementsByClass('Measure')[-1]
            last_measure.rightBarline = bar.Barline('final')
        
        score.append(part)

    # Configurações finais da partitura
    score.insert(0, layout.SystemLayout(isNew=True))
    
    # Garantir que o tempo está definido em toda a partitura
    for part in score.parts:
        if not part.recurse().getElementsByClass('MetronomeMark'):
            part.insert(0, mm)
    
    # Definir o tempo global da partitura
    score.metronome = mm
    
    # Adicionar timestamp à metadata
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    score.metadata.date = timestamp
    
    # Salvar e mostrar a partitura
    return save_and_show_score(score, timestamp)

class MarkovMusicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Gerador de Música - Cadeia de Markov")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Variáveis de controle
        self.midi_files = []
        self.selected_instruments = []
        self.voice_mappings = {}  # Mapeia instrumentos para vozes MIDI
        self.available_voices = {}  # Armazena as vozes disponíveis de todos os arquivos MIDI
        self.training_data_dict = {}
        self.models = {}
        self.quantization_options = {
            "Semínima": 1.0,
            "Mínima": 2.0,
            "Colcheia": 0.5,
            "Semicolcheia": 0.25
        }
        
        # Configurações padrão
        self.order_var = tk.IntVar(value=1)
        self.quantization_var = tk.StringVar(value="Semicolcheia")
        self.melody_length_var = tk.IntVar(value=200)
        self.bpm_var = tk.IntVar(value=120)
        self.use_midi_var = tk.BooleanVar(value=True)
        self.time_signature_var = tk.StringVar(value="4/4")
        self.random_time_changes_var = tk.BooleanVar(value=False)
        
        # Status e logs
        self.status_var = tk.StringVar(value="Pronto para começar")
        self.log_text = None
        
        # Configurar a interface
        self.create_widgets()
        
    def create_widgets(self):
        """Cria os widgets da interface gráfica"""
        # Notebook (abas)
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 1: Configuração
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuração")
        
        # Aba 2: Log e Status
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Log e Status")
        
        # Aba 3: Sobre
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="Sobre")
        
        # Configurar cada aba
        self.setup_config_tab(config_frame)
        self.setup_log_tab(log_frame)
        self.setup_about_tab(about_frame)
        
        # Barra de status na parte inferior
        status_bar = ttk.Frame(self)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        status_label = ttk.Label(status_bar, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
    def setup_config_tab(self, parent):
        """Configura a aba de configuração"""
        # Criar frames para organizar os widgets
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ---- Frame Esquerdo ----
        # Fonte de dados
        data_frame = ttk.LabelFrame(left_frame, text="Fonte de Dados")
        data_frame.pack(fill=tk.X, pady=5)
        
        use_midi_check = ttk.Checkbutton(data_frame, text="Usar arquivos MIDI", variable=self.use_midi_var)
        use_midi_check.pack(anchor=tk.W, padx=10, pady=5)
        
        midi_files_frame = ttk.Frame(data_frame)
        midi_files_frame.pack(fill=tk.X, padx=10, pady=5)
        
        select_files_btn = ttk.Button(midi_files_frame, text="Selecionar Arquivos MIDI", 
                                      command=self.select_midi_files)
        select_files_btn.pack(side=tk.LEFT)
        
        self.files_label = ttk.Label(midi_files_frame, text="Nenhum arquivo selecionado")
        self.files_label.pack(side=tk.LEFT, padx=10)
        
        # Instrumentos
        instruments_frame = ttk.LabelFrame(left_frame, text="Instrumentos")
        instruments_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        instruments_frame_top = ttk.Frame(instruments_frame)
        instruments_frame_top.pack(fill=tk.X, padx=10, pady=5)
        
        select_instr_btn = ttk.Button(instruments_frame_top, text="Selecionar Instrumentos", 
                                     command=self.select_instruments)
        select_instr_btn.pack(side=tk.LEFT)
        
        map_voices_btn = ttk.Button(instruments_frame_top, text="Mapear Vozes MIDI", 
                                   command=self.map_instrument_voices, state=tk.DISABLED)
        map_voices_btn.pack(side=tk.LEFT, padx=10)
        self.map_voices_btn = map_voices_btn
        
        # Lista de instrumentos selecionados
        instruments_list_frame = ttk.Frame(instruments_frame)
        instruments_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        instruments_list_label = ttk.Label(instruments_list_frame, text="Instrumentos Selecionados:")
        instruments_list_label.pack(anchor=tk.W)
        
        self.instruments_listbox = tk.Listbox(instruments_list_frame)
        self.instruments_listbox.pack(fill=tk.BOTH, expand=True)
        
        # ---- Frame Direito ----
        # Parâmetros
        params_frame = ttk.LabelFrame(right_frame, text="Parâmetros")
        params_frame.pack(fill=tk.X, pady=5)
        
        # Ordem de Markov
        order_frame = ttk.Frame(params_frame)
        order_frame.pack(fill=tk.X, padx=10, pady=5)
        
        order_label = ttk.Label(order_frame, text="Ordem de Markov:")
        order_label.pack(side=tk.LEFT)
        
        order_spinbox = ttk.Spinbox(order_frame, from_=1, to=3, textvariable=self.order_var, width=5)
        order_spinbox.pack(side=tk.LEFT, padx=10)
        
        # Quantização
        quantization_frame = ttk.Frame(params_frame)
        quantization_frame.pack(fill=tk.X, padx=10, pady=5)
        
        quantization_label = ttk.Label(quantization_frame, text="Quantização:")
        quantization_label.pack(side=tk.LEFT)
        
        quantization_combo = ttk.Combobox(quantization_frame, textvariable=self.quantization_var, 
                                         values=list(self.quantization_options.keys()), state="readonly", width=12)
        quantization_combo.pack(side=tk.LEFT, padx=10)
        
        # Comprimento da Melodia
        length_frame = ttk.Frame(params_frame)
        length_frame.pack(fill=tk.X, padx=10, pady=5)
        
        length_label = ttk.Label(length_frame, text="Comprimento da Melodia:")
        length_label.pack(side=tk.LEFT)
        
        length_spinbox = ttk.Spinbox(length_frame, from_=1, to=1000, textvariable=self.melody_length_var, width=5)
        length_spinbox.pack(side=tk.LEFT, padx=10)
        
        # BPM
        bpm_frame = ttk.Frame(params_frame)
        bpm_frame.pack(fill=tk.X, padx=10, pady=5)
        
        bpm_label = ttk.Label(bpm_frame, text="BPM:")
        bpm_label.pack(side=tk.LEFT)
        
        bpm_spinbox = ttk.Spinbox(bpm_frame, from_=1, to=300, textvariable=self.bpm_var, width=5)
        bpm_spinbox.pack(side=tk.LEFT, padx=10)
        
        # Fórmula de Compasso
        time_sig_frame = ttk.Frame(params_frame)
        time_sig_frame.pack(fill=tk.X, padx=10, pady=5)
        
        time_sig_label = ttk.Label(time_sig_frame, text="Fórmula de Compasso:")
        time_sig_label.pack(side=tk.LEFT)
        
        time_sig_options = ['4/4', '3/4', '2/4', '3/8', '6/8', '12/8']
        time_sig_combo = ttk.Combobox(time_sig_frame, textvariable=self.time_signature_var,
                                     values=time_sig_options, state="readonly", width=8)
        time_sig_combo.pack(side=tk.LEFT, padx=10)
        
        # Mudanças aleatórias de compasso
        random_time_check = ttk.Checkbutton(time_sig_frame, text="Mudanças Aleatórias",
                                           variable=self.random_time_changes_var)
        random_time_check.pack(side=tk.LEFT, padx=10)
        
        # Botões de ação
        actions_frame = ttk.Frame(right_frame)
        actions_frame.pack(fill=tk.X, pady=10)
        
        generate_btn = ttk.Button(actions_frame, text="Gerar Música", command=self.generate_music)
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(actions_frame, text="Exportar Análise", command=self.export_analysis)
        export_btn.pack(side=tk.LEFT, padx=5)
        self.export_btn = export_btn
        self.export_btn['state'] = tk.DISABLED
        
        test_musescore_btn = ttk.Button(actions_frame, text="Testar MuseScore", command=self.test_musescore)
        test_musescore_btn.pack(side=tk.LEFT, padx=5)
        
        # Resultado
        result_frame = ttk.LabelFrame(right_frame, text="Resultado")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=10)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.result_text.config(state=tk.DISABLED)
        
    def setup_log_tab(self, parent):
        """Configura a aba de log"""
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        log_label = ttk.Label(log_frame, text="Log de Operações:")
        log_label.pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        clear_btn = ttk.Button(log_frame, text="Limpar Log", command=self.clear_log)
        clear_btn.pack(anchor=tk.E, pady=5)
        
    def setup_about_tab(self, parent):
        """Configura a aba Sobre"""
        about_frame = ttk.Frame(parent)
        about_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_label = ttk.Label(about_frame, text="Gerador de Música - Cadeia de Markov", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        about_text = """
Este aplicativo gera composições musicais utilizando cadeias de Markov.

O sistema pode usar arquivos MIDI existentes como fonte de treinamento ou 
usar um conjunto de dados predefinido. A música gerada é exportada em
formato MusicXML e MIDI, e pode ser aberta automaticamente no MuseScore.

Desenvolvido com Python, Tkinter e Music21.
        """
        
        description = ttk.Label(about_frame, text=about_text, wraplength=400, justify="center")
        description.pack(pady=10)
        
        instructions_label = ttk.Label(about_frame, text="Instruções Básicas:", font=("Arial", 11, "bold"))
        instructions_label.pack(anchor=tk.W, pady=(20, 5))
        
        instructions_text = """
1. Selecione se deseja usar arquivos MIDI (recomendado) ou dados predefinidos
2. Se usar MIDI, selecione os arquivos que servirão de fonte
3. Escolha os instrumentos para a composição
4. Mapeie as vozes MIDI para os instrumentos selecionados
5. Ajuste os parâmetros:
   - Ordem da cadeia de Markov (1-3)
   - Quantização rítmica (Semicolcheia, Colcheia, Semínima, Mínima)
   - Comprimento da melodia (número de notas)
   - BPM (tempo)
   - Fórmula de compasso (4/4, 3/4, 2/4, 3/8, 6/8, 12/8)
   - Mudanças aleatórias (opcional: altera fórmula de compasso aleatoriamente)
6. Clique em "Gerar Música" para criar a composição
7. A partitura será salva e aberta no MuseScore (se disponível)

Dica: Use "Testar MuseScore" para verificar se o MuseScore está instalado antes de gerar.
        """
        
        instructions = ttk.Label(about_frame, text=instructions_text, wraplength=500, justify="left")
        instructions.pack(fill=tk.X)
        
    def log(self, message):
        """Adiciona uma mensagem ao log"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Atualiza a barra de status
        self.status_var.set(message)
        self.update_idletasks()
        
    def clear_log(self):
        """Limpa o log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def update_result(self, message):
        """Atualiza a área de resultado"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, message)
        self.result_text.config(state=tk.DISABLED)
        
    def select_midi_files(self):
        """Permite ao usuário selecionar arquivos MIDI"""
        file_paths = filedialog.askopenfilenames(
            title="Selecione os arquivos MIDI",
            filetypes=[("Arquivos MIDI", "*.mid *.midi")],
            initialdir=os.getcwd()
        )
        
        if file_paths:
            self.midi_files = list(file_paths)
            self.files_label.config(text=f"{len(self.midi_files)} arquivos selecionados")
            self.log(f"Selecionados {len(self.midi_files)} arquivos MIDI")
            
            # Carregar as vozes disponíveis
            self.load_available_voices()
            
            # Habilitar o botão de mapeamento
            self.map_voices_btn['state'] = tk.NORMAL
        else:
            self.log("Nenhum arquivo MIDI selecionado")
    
    def load_available_voices(self):
        """Carrega todas as vozes disponíveis nos arquivos MIDI selecionados"""
        self.available_voices = {}
        
        try:
            self.log("Carregando vozes dos arquivos MIDI...")
            for file_path in self.midi_files:
                filename = os.path.basename(file_path)
                self.log(f"Processando: {filename}")
                
                voices = load_midi_file(file_path)
                
                for voice_name, voice_data in voices:
                    if voice_name in self.available_voices:
                        self.available_voices[voice_name].extend(voice_data)
                    else:
                        self.available_voices[voice_name] = voice_data
            
            self.log(f"Vozes disponíveis carregadas: {len(self.available_voices)}")
        except Exception as e:
            self.log(f"Erro ao carregar vozes: {str(e)}")
            messagebox.showerror("Erro", f"Não foi possível carregar as vozes dos arquivos MIDI:\n{str(e)}")
    
    def select_instruments(self):
        """Abre um diálogo para selecionar instrumentos"""
        InstrumentSelectorDialog(self)
        self.instruments_listbox.delete(0, tk.END)
        for instr in self.selected_instruments:
            self.instruments_listbox.insert(tk.END, instr)
        
        if self.selected_instruments:
            self.log(f"Instrumentos selecionados: {', '.join(self.selected_instruments)}")
    
    def map_instrument_voices(self):
        """Mapeia as vozes MIDI para os instrumentos selecionados"""
        if not self.selected_instruments:
            messagebox.showwarning("Aviso", "Selecione instrumentos primeiro!")
            return
            
        if not self.available_voices:
            messagebox.showwarning("Aviso", "Nenhuma voz MIDI disponível!")
            return
            
        VoiceMappingDialog(self)
        
        if self.voice_mappings:
            mapping_text = []
            for instr, voice in self.voice_mappings.items():
                mapping_text.append(f"{instr} -> {voice}")
            
            self.log(f"Mapeamento de vozes: {', '.join(mapping_text)}")
    
    def generate_music(self):
        """Inicia o processo de geração de música"""
        # Verificar se temos os dados necessários
        if self.use_midi_var.get() and not self.midi_files:
            messagebox.showwarning("Aviso", "Selecione arquivos MIDI primeiro!")
            return
            
        if not self.selected_instruments:
            messagebox.showwarning("Aviso", "Selecione pelo menos um instrumento!")
            return
            
        if self.use_midi_var.get() and not self.voice_mappings:
            messagebox.showwarning("Aviso", "Mapeie as vozes MIDI para os instrumentos primeiro!")
            return
            
        # Iniciar thread para não bloquear a interface
        thread = threading.Thread(target=self._generate_music_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_music_thread(self):
        """Thread para geração de música"""
        try:
            self.log("Iniciando geração de música...")
            self.status_var.set("Gerando música...")
            
            # Preparar dados de treinamento
            self.training_data_dict = {}
            
            if self.use_midi_var.get():
                # Usar dados MIDI mapeados
                for instrument, voice in self.voice_mappings.items():
                    if voice in self.available_voices:
                        self.training_data_dict[instrument] = self.available_voices[voice]
            else:
                # Usar dados predefinidos
                for instrument in self.selected_instruments:
                    self.training_data_dict[instrument] = create_predefined_training_data()
            
            if not self.training_data_dict:
                raise ValueError("Não há dados de treinamento disponíveis")
            
            # Obter parâmetros
            order = self.order_var.get()
            quantization_name = self.quantization_var.get()
            quantization = self.quantization_options[quantization_name]
            melody_length = self.melody_length_var.get()
            bpm = self.bpm_var.get()
            time_signature = self.time_signature_var.get()
            random_time_changes = self.random_time_changes_var.get()
            
            self.log(f"Parâmetros: ordem={order}, quantização={quantization_name}, comprimento={melody_length}, BPM={bpm}, compasso={time_signature}")
            
            # Criar e treinar modelos
            self.models = {}
            melodies = []
            instruments = []
            
            # Agrupar instrumentos base para compartilhar modelos entre dobras
            grouped_instruments = {}
            for instrument in self.training_data_dict.keys():
                base_instr = instrument.split(" #")[0]
                if base_instr not in grouped_instruments:
                    grouped_instruments[base_instr] = []
                grouped_instruments[base_instr].append(instrument)
            
            # Para cada tipo base de instrumento, treinar um modelo único
            for base_instr, instr_list in grouped_instruments.items():
                self.log(f"Treinando modelo para {base_instr}...")
                
                # Usar os dados do primeiro instrumento do grupo para treinar
                training_data = self.training_data_dict[instr_list[0]]
                
                # Quantizar as durações
                quantized_data = [(pitch, quantize_duration(duration, quantization), dynamic, articulation, velocity) 
                                for pitch, duration, dynamic, articulation, velocity in training_data]
                
                # Criar e treinar modelo para este tipo de instrumento
                states = create_states_from_training_data(quantized_data)
                model = MarkovChainMelodyGenerator(states, order)
                model.train(quantized_data)
                
                # Usar o mesmo modelo treinado para todas as dobras deste instrumento
                for instrument in instr_list:
                    self.models[instrument] = model
            
            # Agora, gerar melodias para cada instrumento individual
            # Usar generate_all_sequences() para gerar com matrizes separadas
            for base_instr, instr_list in grouped_instruments.items():
                model = self.models[instr_list[0]]
                self.log(f"Gerando melodias para {base_instr} ({len(instr_list)} instância(s))...")
                
                # Gerar melodias independentes para cada dobra usando matrizes separadas
                melodies_dict = model.generate_all_sequences(instr_list, melody_length)
                
                for instrument in instr_list:
                    melody = melodies_dict[instrument]
                    # Ajustar pitch ao range do instrumento
                    adjusted_melody = [
                        (adjust_pitch_to_range(note[0], instrument), note[1], note[2], note[3], note[4])
                        for note in melody
                    ]
                    melodies.append(adjusted_melody)
                    instruments.append(instrument)
            
            # Visualizar e salvar a partitura
            self.log("Criando partitura...")
            
            # Gerar sequência de mudanças de compasso (sincronizada para todos os instrumentos)
            time_sig_sequence = None
            if random_time_changes:
                # Estimar número de compassos
                # Assumindo duração média de 0.75 por nota e measure_length médio de 3.5
                avg_note_duration = 0.75
                avg_measure_length = 3.5
                estimated_total_duration = melody_length * avg_note_duration
                estimated_measures = int(estimated_total_duration / avg_measure_length) + 10  # +10 para margem
                
                self.log(f"Gerando mudanças aleatórias de compasso (estimativa: ~{estimated_measures} compassos)")
                time_sig_sequence = generate_time_signature_sequence(
                    time_signature, 
                    estimated_measures, 
                    random_changes=True
                )
                
                # Log das mudanças geradas
                changes_text = ", ".join([f"c.{num}:{sig}" for num, sig in time_sig_sequence[:10]])
                if len(time_sig_sequence) > 10:
                    changes_text += "..."
                self.log(f"Mudanças de compasso: {changes_text}")
            
            result = visualize_multi_voice_melody(melodies, instruments, bpm, time_signature, time_sig_sequence)
            
            if len(result) == 3:
                xml_path, midi_path, musescore_msg = result
            else:
                xml_path, midi_path = result
                musescore_msg = ""
            
            if xml_path and midi_path:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                
                result_message = (
                    f"Música gerada com sucesso!\n\n"
                    f"Arquivos gerados:\n"
                    f"- MusicXML: {os.path.basename(xml_path)}\n"
                    f"- MIDI: {os.path.basename(midi_path)}\n\n"
                    f"Localização: pasta 'generated_scores'\n"
                )
                
                self.update_result(result_message)
                self.log("Música gerada com sucesso!")
                
                # Log da abertura do MuseScore
                if musescore_msg:
                    self.log(musescore_msg)
                
                self.status_var.set("Música gerada com sucesso")
                
                # Habilitar botão de exportar análise
                self.export_btn['state'] = tk.NORMAL
            else:
                raise ValueError("Falha ao salvar os arquivos")
                
        except Exception as e:
            error_message = f"Erro na geração de música: {str(e)}"
            self.log(error_message)
            self.update_result(f"Erro:\n{error_message}")
            self.status_var.set("Erro na geração de música")
            
            messagebox.showerror("Erro", error_message)
    
    def export_analysis(self):
        """Exporta análises das cadeias de Markov geradas"""
        if not self.models:
            messagebox.showwarning("Aviso", "Nenhum modelo disponível para exportar!")
            return
            
        # Perguntar diretório para salvar
        export_dir = filedialog.askdirectory(
            title="Selecione o diretório para exportar",
            initialdir=os.getcwd()
        )
        
        if not export_dir:
            return
            
        try:
            self.log("Exportando análises...")
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            
            for instrument, model in self.models.items():
                export_prefix = os.path.join(export_dir, f"markov_analysis_{timestamp}_{instrument}")
                model.export_analysis_data(export_prefix)
            
            self.log(f"Análises exportadas para: {export_dir}")
            messagebox.showinfo("Exportação Concluída", f"Análises exportadas com sucesso para:\n{export_dir}")
        except Exception as e:
            error_message = f"Erro na exportação: {str(e)}"
            self.log(error_message)
            messagebox.showerror("Erro", error_message)
    
    def test_musescore(self):
        """Testa se o MuseScore está instalado e acessível"""
        self.log("Testando instalação do MuseScore...")
        
        musescore_path = find_musescore()
        
        if musescore_path:
            message = (
                f"✓ MuseScore encontrado!\n\n"
                f"Localização: {musescore_path}\n"
                f"Sistema: {platform.system()}\n\n"
                f"O MuseScore será aberto automaticamente ao gerar música."
            )
            self.log(f"MuseScore encontrado em: {musescore_path}")
            messagebox.showinfo("MuseScore Detectado", message)
        else:
            message = (
                f"✗ MuseScore não encontrado\n\n"
                f"Sistema: {platform.system()}\n\n"
                f"Por favor, instale o MuseScore:\n"
                f"- Windows/Mac: https://musescore.org/download\n"
                f"- Linux: sudo apt install musescore\n\n"
                f"Após a instalação, reinicie o aplicativo."
            )
            self.log("MuseScore não encontrado no sistema")
            messagebox.showwarning("MuseScore Não Encontrado", message)

class InstrumentSelectorDialog:
    """Diálogo para selecionar instrumentos com suporte a dobras (múltiplas instâncias)"""
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Selecionar Instrumentos")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centralizar o diálogo
        w = 600
        h = 550
        sw = self.dialog.winfo_screenwidth()
        sh = self.dialog.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        # Lista base de instrumentos disponíveis
        self.base_instruments = list(INSTRUMENT_RANGES.keys())
        
        # Dicionário para armazenar contadores de instâncias
        self.instrument_counts = {}
        for instr in self.base_instruments:
            self.instrument_counts[instr] = 0
            
        # Inicializar a partir da lista atual
        for instr in parent.selected_instruments:
            # Remover sufixo numérico se existir (ex: "Violin I #2" -> "Violin I")
            base_name = instr.split(" #")[0]
            if base_name in self.instrument_counts:
                self.instrument_counts[base_name] += 1
        
        self.create_widgets()
        
        # Esperar até que o diálogo seja fechado
        parent.wait_window(self.dialog)
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="Seleção de Instrumentos com Dobras", 
                                font=("Arial", 12, "bold"))
        title_label.pack(anchor=tk.W)
        
        instructions = ttk.Label(header_frame, 
                               text="Use os botões + e - para adicionar ou remover instâncias de cada instrumento.")
        instructions.pack(anchor=tk.W, pady=(5, 0))
        
        # Tabela para seleção de instrumentos
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Criar um canvas com scrollbar
        canvas_frame = ttk.Frame(table_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Cabeçalhos da tabela
        ttk.Label(scrollable_frame, text="Instrumento", font=("Arial", 10, "bold"), width=20).grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(scrollable_frame, text="Instâncias", font=("Arial", 10, "bold"), width=10).grid(
            row=0, column=1, padx=5, pady=5)
        ttk.Label(scrollable_frame, text="Controles", font=("Arial", 10, "bold"), width=15).grid(
            row=0, column=2, padx=5, pady=5)
        
        # Criar widgets de contagem para cada instrumento
        self.count_vars = {}
        row = 1
        
        for instrument in self.base_instruments:
            # Nome do instrumento
            ttk.Label(scrollable_frame, text=instrument).grid(
                row=row, column=0, padx=5, pady=2, sticky=tk.W)
            
            # Contador
            count_var = tk.IntVar(value=self.instrument_counts[instrument])
            self.count_vars[instrument] = count_var
            
            count_label = ttk.Label(scrollable_frame, textvariable=count_var, width=5)
            count_label.grid(row=row, column=1, padx=5, pady=2)
            
            # Botões de controle
            control_frame = ttk.Frame(scrollable_frame)
            control_frame.grid(row=row, column=2, padx=5, pady=2)
            
            minus_btn = ttk.Button(control_frame, text="-", width=3,
                                 command=lambda i=instrument: self.decrease_count(i))
            minus_btn.pack(side=tk.LEFT, padx=2)
            
            plus_btn = ttk.Button(control_frame, text="+", width=3,
                                command=lambda i=instrument: self.increase_count(i))
            plus_btn.pack(side=tk.LEFT, padx=2)
            
            row += 1
        
        # Área de resumo
        summary_frame = ttk.LabelFrame(frame, text="Instrumentos Selecionados")
        summary_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, height=6)
        self.summary_text.pack(fill=tk.X, pady=5, padx=5)
        
        # Botões de ações rápidas
        quick_actions = ttk.Frame(frame)
        quick_actions.pack(fill=tk.X, pady=(10, 0))
        
        clear_all_btn = ttk.Button(quick_actions, text="Limpar Todos", command=self.clear_all)
        clear_all_btn.pack(side=tk.LEFT, padx=5)
        
        typical_orchestra_btn = ttk.Button(quick_actions, text="Orquestra Padrão", 
                                        command=self.set_typical_orchestra)
        typical_orchestra_btn.pack(side=tk.LEFT, padx=5)
        
        string_quartet_btn = ttk.Button(quick_actions, text="Quarteto de Cordas", 
                                      command=self.set_string_quartet)
        string_quartet_btn.pack(side=tk.LEFT, padx=5)
        
        # Botões de OK e Cancelar
        btn_bottom_frame = ttk.Frame(frame)
        btn_bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        cancel_btn = ttk.Button(btn_bottom_frame, text="Cancelar", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
        
        ok_btn = ttk.Button(btn_bottom_frame, text="OK", command=self.confirm_selection)
        ok_btn.pack(side=tk.RIGHT, padx=5)
        
        # Atualizar o resumo inicial
        self.update_summary()
    
    def increase_count(self, instrument):
        """Aumenta a contagem de um instrumento"""
        current = self.count_vars[instrument].get()
        self.count_vars[instrument].set(current + 1)
        self.update_summary()
    
    def decrease_count(self, instrument):
        """Diminui a contagem de um instrumento"""
        current = self.count_vars[instrument].get()
        if current > 0:
            self.count_vars[instrument].set(current - 1)
            self.update_summary()
    
    def clear_all(self):
        """Limpa todos os contadores"""
        for var in self.count_vars.values():
            var.set(0)
        self.update_summary()
    
    def set_typical_orchestra(self):
        """Configura uma orquestra padrão"""
        self.clear_all()
        orchestra = {
            "Flute": 2,
            "Oboe": 2,
            "Clarinet": 2,
            "Bassoon": 2,
            "Horn": 4,
            "Trumpet": 2,
            "Trombone": 3,
            "Tuba": 1,
            "Violin I": 8,
            "Violin II": 6,
            "Viola": 4,
            "Violoncello": 4,
            "Double Bass": 2
        }
        
        for instr, count in orchestra.items():
            if instr in self.count_vars:
                self.count_vars[instr].set(count)
        
        self.update_summary()
    
    def set_string_quartet(self):
        """Configura um quarteto de cordas"""
        self.clear_all()
        quartet = {
            "Violin I": 1,
            "Violin II": 1,
            "Viola": 1,
            "Violoncello": 1
        }
        
        for instr, count in quartet.items():
            if instr in self.count_vars:
                self.count_vars[instr].set(count)
        
        self.update_summary()
    
    def update_summary(self):
        """Atualiza o texto de resumo com os instrumentos selecionados"""
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        selected = []
        total_count = 0
        
        for instr, var in self.count_vars.items():
            count = var.get()
            if count > 0:
                if count == 1:
                    selected.append(f"{instr}")
                else:
                    selected.append(f"{instr} ({count} instâncias)")
                total_count += count
        
        if selected:
            summary = "Total: " + str(total_count) + " instrumentos\n"
            summary += ", ".join(selected)
            self.summary_text.insert(tk.END, summary)
        else:
            self.summary_text.insert(tk.END, "Nenhum instrumento selecionado")
        
        self.summary_text.config(state=tk.DISABLED)
    
    def confirm_selection(self):
        """Confirma a seleção e fecha o diálogo"""
        selected_instruments = []
        
        for instr, var in self.count_vars.items():
            count = var.get()
            if count > 0:
                if count == 1:
                    selected_instruments.append(instr)
                else:
                    # Adicionar várias instâncias com sufixos numéricos
                    for i in range(1, count + 1):
                        selected_instruments.append(f"{instr} #{i}")
        
        if not selected_instruments:
            messagebox.showwarning("Aviso", "Selecione pelo menos um instrumento!", parent=self.dialog)
            return
        
        # Atualizar a lista de instrumentos selecionados
        self.parent.selected_instruments = selected_instruments
        
        # Limpar mapeamentos existentes
        self.parent.voice_mappings = {}
        
        self.dialog.destroy()

class VoiceMappingDialog:
    """Diálogo para mapear vozes MIDI para instrumentos, com suporte a dobras"""
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Mapear Vozes MIDI")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centralizar o diálogo
        w = 600
        h = 500
        sw = self.dialog.winfo_screenwidth()
        sh = self.dialog.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        self.available_voices = list(parent.available_voices.keys())
        self.selected_instruments = parent.selected_instruments
        self.mappings = {}
        
        # Agrupar instrumentos por tipo base para facilitar o mapeamento de dobras
        self.grouped_instruments = self.group_instruments_by_type()
        
        self.create_widgets()
        
        # Esperar até que o diálogo seja fechado
        parent.wait_window(self.dialog)
    
    def group_instruments_by_type(self):
        """Agrupa instrumentos por tipo base (para dobras)"""
        groups = {}
        
        for instr in self.selected_instruments:
            # Extrair o tipo base (ex: "Violin I #2" -> "Violin I")
            base_type = instr.split(" #")[0]
            
            if base_type not in groups:
                groups[base_type] = []
            
            groups[base_type].append(instr)
        
        return groups
    
    def create_widgets(self):
        """Cria os widgets do diálogo"""
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho
        header_label = ttk.Label(frame, text="Selecione qual voz MIDI usar para cada instrumento:", 
                                font=("Arial", 10, "bold"))
        header_label.pack(anchor=tk.W, pady=(0, 5))
        
        info_label = ttk.Label(frame, 
                            text="Instrumentos com dobras podem usar a mesma voz MIDI ou vozes diferentes.")
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Criar um canvas com scrollbar para a tabela
        canvas_frame = ttk.Frame(frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        table_frame = ttk.Frame(canvas)
        
        table_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=table_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Cabeçalhos da tabela
        headers = ["Instrumento", "Voz MIDI", "Controles"]
        
        for i, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 10, "bold")).grid(
                row=0, column=i, padx=5, pady=5, sticky=tk.W)
        
        # Linhas com instrumentos e comboboxes para vozes
        self.voice_vars = {}
        row = 1
        
        # Adicionar botões de grupo
        for base_type, instruments in self.grouped_instruments.items():
            # Cabeçalho do grupo
            group_label = ttk.Label(table_frame, text=base_type, font=("Arial", 10, "bold", "italic"))
            group_label.grid(row=row, column=0, columnspan=3, padx=5, pady=(10, 5), sticky=tk.W)
            row += 1
            
            # Se tiver mais de uma instância, adicionar controles de grupo
            if len(instruments) > 1:
                ttk.Label(table_frame, text="Dobras:", font=("Arial", 9, "italic")).grid(
                    row=row, column=0, padx=5, pady=2, sticky=tk.W)
                
                # Botão para usar a mesma voz para todas as dobras
                same_voice_btn = ttk.Button(
                    table_frame, 
                    text="Usar Mesma Voz para Todas", 
                    command=lambda bt=base_type: self.use_same_voice_for_group(bt)
                )
                same_voice_btn.grid(row=row, column=1, columnspan=2, padx=5, pady=2, sticky=tk.W)
                row += 1
            
            # Adicionar cada instrumento individual
            for instr in instruments:
                # Nome do instrumento (com destaque para o número da dobra, se existir)
                if "#" in instr:
                    base, num = instr.split(" #")
                    instr_text = f"{base} #{num}"
                else:
                    instr_text = instr
                
                ttk.Label(table_frame, text=instr_text).grid(
                    row=row, column=0, padx=(20, 5), pady=2, sticky=tk.W)
                
                voice_var = tk.StringVar()
                self.voice_vars[instr] = voice_var
                
                voice_combo = ttk.Combobox(table_frame, textvariable=voice_var, 
                                         values=self.available_voices, width=30)
                voice_combo.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
                
                # Pré-selecionar a primeira voz disponível
                if self.available_voices:
                    voice_var.set(self.available_voices[0])
                    
                # Pré-selecionar mapeamento existente se houver
                if instr in self.parent.voice_mappings:
                    voice_var.set(self.parent.voice_mappings[instr])
                
                row += 1
        
        # Botões de ações rápidas
        quick_frame = ttk.Frame(frame)
        quick_frame.pack(fill=tk.X, pady=(10, 0))
        
        random_map_btn = ttk.Button(quick_frame, text="Mapear Aleatoriamente", 
                                  command=self.random_mapping)
        random_map_btn.pack(side=tk.LEFT, padx=5)
        
        clear_map_btn = ttk.Button(quick_frame, text="Limpar Mapeamentos", 
                                 command=self.clear_mappings)
        clear_map_btn.pack(side=tk.LEFT, padx=5)
        
        # Botões de OK e Cancelar
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
        
        ok_btn = ttk.Button(btn_frame, text="OK", command=self.confirm_mappings)
        ok_btn.pack(side=tk.RIGHT, padx=5)
    
    def use_same_voice_for_group(self, base_type):
        """Define a mesma voz MIDI para todas as dobras de um tipo de instrumento"""
        # Selecionar a primeira voz disponível como padrão
        default_voice = self.available_voices[0] if self.available_voices else ""
        
        # Pedir ao usuário para selecionar a voz para o grupo
        voice_dialog = VoiceSelectionDialog(self.dialog, 
                                          f"Selecione uma voz MIDI para todos os {base_type}", 
                                          self.available_voices, 
                                          default_voice)
        
        selected_voice = voice_dialog.result
        if not selected_voice:
            return
        
        # Aplicar a mesma voz para todos os instrumentos deste tipo
        for instr in self.grouped_instruments[base_type]:
            self.voice_vars[instr].set(selected_voice)
    
    def random_mapping(self):
        """Mapeia aleatoriamente as vozes MIDI para os instrumentos"""
        import random
        
        if not self.available_voices:
            messagebox.showwarning("Aviso", "Não há vozes MIDI disponíveis!", parent=self.dialog)
            return
            
        for var in self.voice_vars.values():
            voice = random.choice(self.available_voices)
            var.set(voice)
    
    def clear_mappings(self):
        """Limpa todos os mapeamentos"""
        for var in self.voice_vars.values():
            var.set("")
    
    def confirm_mappings(self):
        """Confirma os mapeamentos e fecha o diálogo"""
        mappings = {}
        missing = []
        
        for instrument, voice_var in self.voice_vars.items():
            voice = voice_var.get()
            if voice:
                mappings[instrument] = voice
            else:
                missing.append(instrument)
        
        if missing:
            instruments_list = "\n".join(missing)
            messagebox.showwarning("Aviso", 
                                f"Os seguintes instrumentos não têm uma voz MIDI mapeada:\n\n{instruments_list}", 
                                parent=self.dialog)
            return
        
        # Atualizar os mapeamentos
        self.parent.voice_mappings = mappings
        self.parent.log(f"Mapeamento de vozes atualizado para {len(mappings)} instrumentos")
        self.dialog.destroy()

class VoiceSelectionDialog:
    """Diálogo simples para selecionar uma voz MIDI"""
    def __init__(self, parent, title, voices, default=None):
        self.result = None
        
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.transient(parent)
        dialog.grab_set()
        
        # Centralizar o diálogo
        w = 400
        h = 200
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        # Frame principal
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Label e combobox
        ttk.Label(frame, text="Selecione a voz MIDI:").pack(anchor=tk.W, pady=(0, 5))
        
        voice_var = tk.StringVar()
        if default:
            voice_var.set(default)
            
        voice_combo = ttk.Combobox(frame, textvariable=voice_var, values=voices, width=40)
        voice_combo.pack(fill=tk.X, pady=5)
        
        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        cancel_btn = ttk.Button(btn_frame, text="Cancelar", 
                              command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
        
        def on_ok():
            self.result = voice_var.get()
            dialog.destroy()
            
        ok_btn = ttk.Button(btn_frame, text="OK", command=on_ok)
        ok_btn.pack(side=tk.RIGHT, padx=5)
        
        # Focar no combobox
        voice_combo.focus_set()
        
        # Esperar até que o diálogo seja fechado
        parent.wait_window(dialog)

def main():
    app = MarkovMusicApp()
    app.mainloop()

if __name__ == "__main__":
    main()