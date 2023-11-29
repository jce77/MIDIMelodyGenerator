import copy
import math
import os
import sys
from enum import Enum
import mido
from mido import MidiFile, MidiTrack, MetaMessage
import random
from pathlib import Path

'''

MIDI Melody Generator - A program that just generates the midi file for a melody

Whole note: 4 beats
Half note: 2 beats
Quarter note: 1 beat
Eighth note: 0.5 beats
Sixteenth note: 0.25 beats
Thirty-second note: 0.125 beats
And so on...

'''

# region constants

SEED_MOD_GENERATE_MELODY_RUN_COMMANDS = 836501245
SEED_MOD_GENERATE_TIME_PATTERN_COMMAND = 481726453


# endregion


# region Data-types


class Pattern:
    def __init__(self, name, time_signature, p_note_times):
        """
        name: string\n
        time_signature: string\n
        p_note_times: PNT[]
        """
        self.name = name
        self.time_signature = time_signature
        self.p_note_times = p_note_times

    def __str__(self):
        pnt_str = ", ".join(str(pnt) for pnt in self.p_note_times)
        return f"Pattern(name={self.name}, time_signature={self.time_signature}, p_note_times=[{pnt_str}])"


# PNT for Pattern Note Time
class PNT:
    def __init__(self, play_time, rest_time):
        """
        play_time: float - Time in beats\n
        rest_time: float - Time in beats
        """
        self.play_time = play_time
        self.rest_time = rest_time

    def __str__(self):
        return f"({self.play_time}, {self.rest_time})"


class ScaleDefinition:
    def __init__(self, intervals):
        """
        intervals: int[] the pitch changes that happen in a scale
        """
        self.intervals = intervals


class Key(Enum):
    A = 1
    ASharp = 2
    B = 3
    C = 4
    CSharp = 5
    D = 6
    DSharp = 7
    E = 8
    F = 9
    FSharp = 10
    G = 11
    GSharp = 12


class Note:
    def __init__(self, octave, key, beats, after_wait_beats):
        """
        octave: int\n
        key: Key\n
        beats: float - time in beats\n
        after_wait_beats: float - time in beats
        """
        self.octave = octave
        self.key = key
        self.beats = beats
        self.after_wait_beats = after_wait_beats

    def __str__(self):
        return f"Octave {self.octave}, Key {self.key}, Beats {self.beats}, After_wait_beats {self.after_wait_beats}"


class TimeSignature(Enum):
    FourFour = (4, 4)
    ThreeFour = (3, 4)
    SixEight = (6, 8)


class Melody:
    def __init__(self, tempo=120):
        """
        notes: Note[]\n
        key_signature: Key\n
        time_signature: (int,int)\n
        tempo: int
        """
        self.notes = []
        self.key_signature = Key.C
        self.time_signature = (4, 4)
        self.tempo = tempo


class PitchPattern:
    def __init__(self, name, pitch_changes):
        """
        name: string\n
        pitch_changes: int[]
        """
        self.name = name  # string
        self.pitch_changes = pitch_changes  # integer list

    def __str__(self):
        pitch_changes_str = ', '.join(map(str, self.pitch_changes))
        return f"name {self.name}, pitch_changes [{pitch_changes_str}]"


class DirectionPattern:
    def __init__(self, name, direction_changes):
        """
        name: string\n
        direction_changes: int[]
        """
        self.name = name  # string
        self.direction_changes = direction_changes  # integer list

    def __str__(self):
        direction_changes_str = ', '.join(map(str, self.direction_changes))
        return f"name {self.name}, direction_changes [{direction_changes_str}]"


class TimePattern:
    def __init__(self, name, key_signature, beat_times):
        """
        name: string\n
        key_signature: string\n
        beat_times: PNT[]
        """
        self.name = name
        self.key_signature = key_signature
        self.beat_times = beat_times

    def __str__(self):
        beat_times_str = ', '.join([f"({pnt.play_time}, {pnt.rest_time})" for pnt in self.beat_times])
        return f"name {self.name}, key_signature {self.key_signature}, " \
               f"beat_times [{beat_times_str}]"


# endregion

# region Variables

""" direction_patterns refers to jumps from the current position in the scale """

# Define scales
scales = {
    'major': ScaleDefinition([2, 2, 1, 2, 2, 2, 1]),  # Common in classical, pop, and happy/festive music
    'minor': ScaleDefinition([2, 1, 2, 2, 1, 2, 2]),
    # Versatile and used in various genres, can convey a sad or dramatic mood

    'dorian': ScaleDefinition([2, 1, 2, 2, 2, 1, 2]),
    # Often used in medieval and Celtic music, has a slightly folkloric feel
    'mixolydian': ScaleDefinition([2, 2, 1, 2, 2, 1, 2]),
    # Common in rock, blues, and folk music, has a bluesy sound
    'phrygian': ScaleDefinition([1, 2, 2, 2, 1, 2, 2]),
    # Used in flamenco and Spanish music, has a distinctive exotic quality

    'harmonic_minor': ScaleDefinition([2, 1, 2, 2, 1, 3, 1]),
    # Has a mysterious and exotic quality, often used in fantasy and horror music
    'melodic_minor': ScaleDefinition([2, 1, 2, 2, 2, 2, 1]),
    # Used in jazz and various contemporary genres, provides a unique flavor
    'whole_tone': ScaleDefinition([2, 2, 2, 2, 2, 2]),
    # Has a dreamy and surreal quality, often used in impressionistic music

    'pentatonic_major': ScaleDefinition([2, 2, 3, 2, 3]),
    # Simple and widely used in folk, country, and blues music
    'pentatonic_minor': ScaleDefinition([3, 2, 2, 3, 2]),
    # Versatile and often used in various world music traditions

    'octatonic_whole_half': ScaleDefinition([2, 2, 1, 2, 2, 1, 2, 2]),
    # Used in horror and suspenseful music, provides an eerie and unsettling atmosphere
    'octatonic_half_whole': ScaleDefinition([1, 2, 2, 2, 1, 2, 2, 2]),
    # Similar to the whole-half variant, also used in horror and mysterious contexts

    'enigmatic': ScaleDefinition([1, 3, 2, 2, 2, 1, 1]),
    # Uncommon and exotic, used for creating tension and intrigue
    'neapolitan_major': ScaleDefinition([1, 2, 2, 2, 2, 2, 1]),
    # Has a classical and rich sound, used in classical and romantic music
    'neapolitan_minor': ScaleDefinition([1, 2, 2, 2, 1, 3, 1]),
    # Similar to neapolitan major but with a minor third

    # Add more scales as needed
}


# endregion

# region Data sorting functions

def get_time_probabilities(file_name):
    if not file_name.endswith(".timeprobabilities"):
        file_name += ".timeprobabilities"
    beat_probabilities = []
    wait_probabilities = []
    try:
        with open("time_probabilities/" + file_name, 'r') as file:
            # Read all lines into a list
            lines = file.readlines()
            for line in lines:
                data = line.strip()
                if len(data) < 3 or data[0] == '#':
                    continue
                if data.startswith("Beat"):
                    try:
                        parts = data.split()
                        # Attempt to convert the parts to floats
                        value = float(parts[1])
                        magnitude = float(parts[2])
                        beat_probabilities.append([value, magnitude])
                    except (ValueError, IndexError):
                        print("   error reading line " + str(data))
                        continue
                elif data.startswith("Rest"):
                    try:
                        parts = data.split()
                        # Attempt to convert the parts to floats
                        value = float(parts[1])
                        magnitude = float(parts[2])
                        wait_probabilities.append([value, magnitude])
                    except (ValueError, IndexError):
                        print("   error reading line " + str(data))
                        continue
    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found.")
        return None
    return beat_probabilities, wait_probabilities


def get_direction_probabilities(file_name):
    if not file_name.endswith(".directionprobabilities"):
        file_name += ".directionprobabilities"
    probabilities = []
    try:
        with open("direction_probabilities/" + file_name, 'r') as file:
            # Read all lines into a list
            lines = file.readlines()
            for line in lines:
                data = line.strip()
                if len(data) < 3 or data[0] == '#':
                    continue
                try:
                    parts = data.split()
                    # Attempt to convert the parts to floats
                    value = int(parts[0])
                    magnitude = float(parts[1])
                    probabilities.append([value, magnitude])
                except (ValueError, IndexError):
                    continue
    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found.")
        return None
    return probabilities


def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            # Read all lines into a list
            lines = file.readlines()
            return lines
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None


def get_time_patterns(time_patterns_file):
    time_patterns_file = "time_patterns/" + time_patterns_file
    print("time pattern file: " + str(time_patterns_file))
    if not Path(time_patterns_file).exists():
        print("File not found")
        return None

    time_patterns = []

    with open(time_patterns_file, 'r') as file:
        current_pattern = None

        for line in file:
            line = line.strip()
            if len(line) < 3 or line[0] == "#":
                continue

            if line.startswith("pattern="):
                if current_pattern is not None:
                    time_patterns.append(current_pattern)
                pattern_name = line[len("pattern="):]
                current_pattern = TimePattern(pattern_name, None, [])

            elif line.startswith("time_signature="):
                current_pattern.key_signature = line[len("time_signature="):]

            else:
                beat_times = [float(time) for time in line.split()]
                pnt_objects = [PNT(beat_times[i], beat_times[i + 1]) for i in range(0, len(beat_times), 2)]
                current_pattern.beat_times.extend(pnt_objects)

        # Add the last pattern
        if current_pattern is not None:
            time_patterns.append(current_pattern)

    return time_patterns


def get_pitch_patterns(pitch_patterns_file):
    pitch_patterns_file = "pitch_patterns/" + pitch_patterns_file
    file_path = Path(pitch_patterns_file)

    if not file_path.exists():
        print("File not found")
        return None

    pitch_patterns = []

    with open(file_path, 'r') as file:
        current_pattern = None

        for line in file:
            line = line.strip()
            if len(line) < 3 or line[0] == "#":
                continue

            if line.startswith("pattern="):
                if current_pattern is not None:
                    pitch_patterns.append(current_pattern)
                pattern_name = line[len("pattern="):]
                current_pattern = PitchPattern(pattern_name, [])

            else:
                pitch_changes = [int(change) for change in line.split()]
                current_pattern.pitch_changes.extend(pitch_changes)

        # Add the last pattern
        if current_pattern is not None:
            pitch_patterns.append(current_pattern)

    return pitch_patterns


def get_direction_patterns(direction_patterns_file):
    direction_patterns_file = "direction_patterns/" + direction_patterns_file
    file_path = Path(direction_patterns_file)

    if not file_path.exists():
        print("File not found: " + direction_patterns_file)
        return None

    pitch_patterns = []

    with open(file_path, 'r') as file:
        current_pattern = None

        for line in file:
            line = line.strip()

            if len(line) < 3 or line[0] == "#":
                continue

            if line.startswith("pattern="):
                if current_pattern is not None:
                    pitch_patterns.append(current_pattern)
                pattern_name = line[len("pattern="):]
                current_pattern = DirectionPattern(pattern_name, [])

            else:
                parts = line.strip().split()

                try:
                    for i in range(len(parts)):
                        parts[i] = int(parts[i])
                    current_pattern.direction_changes = parts
                except (ValueError, IndexError) as e:
                    print("SKIPPING DATA LINE: " + line)
                    continue

        # Add the last pattern
        if current_pattern is not None:
            pitch_patterns.append(current_pattern)

    return pitch_patterns


# endregion

# region Helper functions


def lehmer_seed_combine(seed, i):
    a, m = 23, 4567  # Adjust these parameters as needed
    combined_seed = (a * seed) % m
    combined_seed ^= i
    return combined_seed


def transpose_note(note, pitch_shift):
    new_key_value = (note.key.value + pitch_shift - 1) % 12 + 1
    new_octave = note.octave + (note.key.value + pitch_shift - 1) // 12

    new_key = Key(new_key_value)
    new_note = Note(new_octave, new_key, note.beats, note.after_wait_beats)

    return new_note


def generate_scale_keys(scale_name, key, starting_octave=1):
    global scales

    scale_intervals = scales.get(scale_name.lower()).intervals
    if scale_intervals is None:
        raise ValueError(f"Unknown scale: {scale_name}")

    scale_keys = [key]
    current_octave = starting_octave

    for interval in scale_intervals:
        current_key_value = (scale_keys[-1].value + interval - 1) % len(Key) + 1
        # If the current key is 1 (which corresponds to GSharp), increase the octave
        if current_key_value == 1:
            current_octave += 1
        scale_keys.append(Key(current_key_value))

    # Adjust the octave of the first key
    scale_keys[0] = Key(scale_keys[0].value)

    return scale_keys


def key_below(current_key):
    # Get the previous key based on enum values
    previous_key_value = (current_key.value - 1) % len(Key)

    # If the current key is the first one (enum value 1), return the last key
    if current_key.value == 1:
        return Key(len(Key))

    # Otherwise, return the key with the calculated value
    return Key(previous_key_value)


def note_exists_in_scale(note, scale_keys):
    # getting current position inside the scale
    current_index_in_scale_keys = -1
    for i in range(len(scale_keys)):
        if scale_keys[i].value == note.key.value:
            current_index_in_scale_keys = i
    if current_index_in_scale_keys == -1:
        return False
    return True


def jump_notes_position_in_scale(note, scale_keys, jump_direction):
    # if the scale contains a final key which is the same as the first key, just remove it
    if scale_keys[len(scale_keys) - 1] == scale_keys[0]:
        del scale_keys[len(scale_keys) - 1]

    # show user info about the generate operation
    print("jump_notes_position_in_scale() ================================================== \n" +
          "note=" + str(note) + ", "
                                "scale_keys=" + str(scale_keys) + ", "
                                                                  "jump_direction=" + str(jump_direction))

    # getting current position inside the scale
    current_index_in_scale_keys = 0
    for i in range(len(scale_keys)):
        if scale_keys[i].value == note.key.value:
            current_index_in_scale_keys = i
    if jump_direction > 0:  # going forwards
        for i in range(jump_direction):
            current_index_in_scale_keys += 1
            if current_index_in_scale_keys == len(scale_keys):
                current_index_in_scale_keys = 0
                note.octave += 1
            note.key = scale_keys[current_index_in_scale_keys]
    elif jump_direction < 0:  # going backwards
        for i in range(abs(jump_direction)):
            current_index_in_scale_keys -= 1
            # this works this way because the last note of every scale is the first note, so skip it
            if current_index_in_scale_keys == -1:
                current_index_in_scale_keys = len(scale_keys) - 1
                note.octave -= 1
            note.key = scale_keys[current_index_in_scale_keys]
    print("Jumped to " + str(note))
    return note


def get_note_below(note):
    # Get the previous key using the key_below function
    previous_key = key_below(note.key)

    # Adjust the octave if the key was reduced from 'A' to 'GSharp'
    new_octave = note.octave - 1 if previous_key == Key.GSharp else note.octave

    # Create a new Note with the reduced key and adjusted octave
    new_note = Note(new_octave, previous_key, note.beats)
    return new_note


def write_to_midi(path, melody, beat_count):
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)
    ticks_per_beat = 480  # You may adjust this based on your tempo and desired resolution

    # in case the pitch is off in the output and needs to be shifted
    library_alignment_value = -4
    max_tick = beat_count * ticks_per_beat
    ticks_added = 0

    for note in melody.notes:
        pitch = note.key.value + (note.octave + 1) * 12 + library_alignment_value
        duration_in_ticks = int(note.beats * ticks_per_beat)

        # checking if there is enough space left
        ticks_added += duration_in_ticks
        if ticks_added > max_tick:
            ticks_added -= duration_in_ticks
            break
        track.append(mido.Message('note_on', note=pitch, velocity=64, time=0))
        track.append(mido.Message('note_off', note=pitch, velocity=64, time=duration_in_ticks))

        # checking if there is enough space left
        ticks_added += int(note.after_wait_beats * ticks_per_beat)
        if ticks_added > max_tick:
            ticks_added -= int(note.after_wait_beats * ticks_per_beat)
            break
        # should add equal blank space to the length of the beat
        track.append(mido.Message('note_on', note=0, velocity=0, time=int(note.after_wait_beats * ticks_per_beat)))
        track.append(mido.Message('note_off', note=0, velocity=0, time=0))

    if ticks_added < max_tick:
        unfilled_space = max_tick - ticks_added
        track.append(mido.Message('note_on', note=0, velocity=0, time=int(unfilled_space)))
        track.append(mido.Message('note_off', note=0, velocity=0, time=0))
        print("Added " + str(unfilled_space) + " of blank space.")


    microseconds_per_minute = 60000000  # Number of microseconds in a minute
    tempo_microseconds_per_beat = int(microseconds_per_minute / melody.tempo)
    track.append(MetaMessage('set_tempo', tempo=tempo_microseconds_per_beat))

    path = "output/" + path
    midi.save(path)


def generate_random_indexes(input_list, seed, min_to_max_time_pattern_count):
    random.seed(seed)

    indexes_list = [index for index, _ in enumerate(input_list)]

    selected_indexes = []
    count = random.randint(min_to_max_time_pattern_count[0], min_to_max_time_pattern_count[1])

    for _ in range(count):
        if not indexes_list:
            break
        selected_index = random.choice(indexes_list)
        selected_indexes.append(selected_index)
        indexes_list.remove(selected_index)

    return selected_indexes


# endregion

# region run parameter processing

def generate_melody_run_commands(segments):
    print("RUNNING  ARGUMENTS FOR generate_melody_run_commands ")

    # region Setting defaults
    scale = "major"
    key = Key.C
    octave = 3

    # Option A
    direction_patterns_file = "example"
    min_direction_patterns = 1
    max_direction_patterns = 3

    # Option B
    direction_probabilities_file = ""
    direction_pattern_size = 8
    direction_pattern_count = 60

    # Option A
    time_patterns_file = "example"
    min_time_patterns = 1
    max_time_patterns = 3

    # Option B
    time_probabilities_file = ""
    time_pattern_size = 8
    time_pattern_count = 60

    output_filename = "melody_generated"
    scale_percentage = 1
    seed = random.randint(100000000, 999999999)

    # endregion

    # region Reading command arguments and setting variables

    i = 0
    while i < len(segments):
        segment = segments[i].strip()

        if segment == '-generate melody':
            i += 1
        elif segment.startswith('-scale'):
            scale = segments[i][len('-scale'):].strip()
            i += 1
        elif segment.startswith('-key'):
            key_str = segments[i][len('-key'):].strip()
            try:
                key = Key[key_str]
            except KeyError:
                print(f"Error: Invalid key value: {key_str}")
                sys.exit(1)
            i += 1
        elif segment.startswith('-octave'):
            octave = int(segments[i][len('-octave'):].strip())
            i += 1
        elif segment.startswith('-directions'):
            parts = segments[i].split()
            direction_patterns_file = parts[1]
            min_direction_patterns = int(parts[2])
            max_direction_patterns = int(parts[3])
            i += 1
        elif segment.startswith('-direction_probabilities'):
            parts = segments[i].split()
            direction_probabilities_file = parts[1]
            direction_pattern_size = int(parts[2])
            direction_pattern_count = int(parts[3])
            i += 1
        elif segment.startswith('-times'):
            parts = segments[i].split()
            time_patterns_file = parts[1]
            min_time_patterns = int(parts[2])
            max_time_patterns = int(parts[3])
            i += 1
        elif segment.startswith('-time_probabilities'):
            parts = segments[i].split()
            time_probabilities_file = parts[1]
            time_pattern_size = int(parts[2])
            time_pattern_count = int(parts[3])
            i += 1
        elif segment.startswith('-output_file'):
            output_filename = segments[i][len('-output_file'):].strip()
            i += 1
        elif segment.startswith('-percentage_of_scale'):
            scale_percentage = float(segments[i][len('-percentage_of_scale'):].strip())
            i += 1
        elif segment.startswith('-seed'):
            seed = int(segments[i][len('-seed'):].strip())
            i += 1
        else:
            print(f"Warning: Unrecognized command: {segment}")
            i += 1

    print("scale=" + str(scale))
    print("key=" + str(key))
    print("octave=" + str(octave))
    print("direction_patterns_file=" + str(direction_patterns_file))
    print("min_direction_patterns=" + str(min_direction_patterns))
    print("max_direction_patterns=" + str(max_direction_patterns))
    print("direction_probabilities_file=" + str(direction_probabilities_file))
    print("direction_pattern_size=" + str(direction_pattern_size))
    print("direction_pattern_count=" + str(direction_pattern_count))
    print("time_patterns_file=" + str(time_patterns_file))
    print("min_time_patterns=" + str(min_time_patterns))
    print("max_time_patterns=" + str(max_time_patterns))
    print("time_probabilities_file=" + str(time_probabilities_file))
    print("time_pattern_size=" + str(time_pattern_size))
    print("time_pattern_count=" + str(time_pattern_count))
    print("output_filename=" + str(output_filename))
    print("scale_percentage=" + str(scale_percentage))
    print("seed=" + str(seed))

    # endregion

    # region Generating direction patterns if needed
    direction_probabilities_file = direction_probabilities_file.strip()
    if not direction_probabilities_file.endswith(".directionprobabilities"):
        direction_probabilities_file += ".directionprobabilities"

    # if an existing path was
    print("Checking " + "direction_probabilities/" + direction_probabilities_file)
    if len(direction_probabilities_file) > 1 and os.path.exists(
            "direction_probabilities/" + direction_probabilities_file):
        print("Generating direction patterns")
        direction_patterns_file = "autogenerated"
        # so now just create a file with the direction patterns and change direction_patterns_file
        # NOTE, an array is inserted so it wont use any run commands this way
        generate_direction_pattern_command([], direction_probabilities_file,
                                           direction_pattern_size, direction_pattern_count, direction_patterns_file)
        pass

    # endregion

    # region Generating time patterns if needed
    time_probabilities_file = time_probabilities_file.strip()
    if not time_probabilities_file.endswith(".timeprobabilities"):
        time_probabilities_file += ".timeprobabilities"

    # if an existing path was
    print("Checking " + "time_probabilities/" + time_probabilities_file)
    if len(time_probabilities_file) > 1 and os.path.exists(
            "time_probabilities/" + time_probabilities_file):
        print("Generating time patterns")
        time_patterns_file = "autogenerated"
        # so now just create a file with the direction patterns and change direction_patterns_file
        # NOTE, an array is inserted so it wont use any run commands this way
        generate_time_pattern_command([], time_probabilities_file,
                                      time_pattern_size, time_pattern_count, time_patterns_file, seed)

        pass

    # endregion

    # region Error checking

    print("Not yet implemented")

    # endregion

    # region Running command

    generate_from_scale_direction_and_time(output_filename,
                                           # in the key of
                                           key,
                                           # using the scale
                                           scale,
                                           # percentage of scale to use (0.0 - 1.0)
                                           scale_percentage,
                                           # starting octave
                                           octave,
                                           # seed
                                           seed,
                                           # time patterns file ---------------------
                                           time_patterns_file,
                                           [min_time_patterns, max_time_patterns],  # ^^ min to max possible to use
                                           # direction patterns file ---------------------
                                           direction_patterns_file,
                                           [min_direction_patterns, max_direction_patterns],
                                           # ^^ min to max possible to use
                                           )

    # endregion


# region Generating direction patterns

def generate_direction_pattern_command(segments, direction_probabilities_file, pattern_size, pattern_count,
                                       output_file):
    print("RUNNING  ARGUMENTS FOR generate_direction_pattern_command ")

    # region reading command arguments

    if len(segments) > 1:
        i = 0
        while i < len(segments):
            segment = segments[i].strip()

            if segment == '-generate direction pattern':
                i += 1
            elif segment.startswith('-probabilities'):
                direction_probabilities_file = segments[i].split()[1].strip()
                i += 1
            elif segment.startswith('-size'):
                if i + 1 < len(segments):
                    pattern_size = int(segments[i].split()[1].strip())
                    i += 1
                else:
                    print("Error: Missing value for -size command.")
                    sys.exit(1)
            elif segment.startswith('-patterns'):
                try:
                    pattern_count = int(segments[i].split()[1].strip())
                    i += 1
                except IndexError:
                    print("Error: Missing value for -patterns command.")
                    sys.exit(1)
                except ValueError:
                    print(f"Error: Invalid value for -patterns command: {segments[i].split()[1].strip()}")
                    sys.exit(1)
            else:
                print(f"Warning: Unrecognized command: {segment}")
                i += 1

        print("direction_probabilities_file=" + str(direction_probabilities_file))
        print("pattern_count=" + str(pattern_count))
        print("pattern_size=" + str(pattern_size))

    # endregion

    # region Main

    # getting probabilities of each step's outcome
    probabilities = get_direction_probabilities(direction_probabilities_file)
    weights = []
    total_weight = 0

    output_text = ""

    for x in probabilities:
        total_weight += x[1]
        weights.append(total_weight)

    for i in range(pattern_count):
        pattern = [0]
        j = 0
        while j < pattern_size:
            reset = False
            rand_number = random.uniform(0.0, total_weight)
            last_move = 0
            # checking which value to use next
            for w in range(len(weights)):
                if rand_number < weights[w]:
                    value = probabilities[w][0]

                    # region Wildcards

                    # repeat last move wildcard, which moves in the same direction again
                    if value == 9999:
                        # in this case the wildcard will not be viable, try another roll
                        if i == 0:
                            reset = True
                            break
                        else:
                            # repeat the last move
                            pattern.append(pattern[len(pattern) - 1])
                            # print("WILDCARD 0 WAS USED")

                    # endregion

                    # standard, just add the value found
                    else:
                        pattern.append(probabilities[w][0])

                    break

            # if resetting, continue and try again
            if reset:
                continue

            j += 1

        output_text += "pattern=Pattern " + str(i) + "\n"
        output_text += ' '.join(map(str, pattern)) + "\n"
    # endregion

    if len(output_file) > 3:
        print("Writing to output file " + output_file)
        output_file = output_file.strip()
        if not output_file.endswith(".directionpatterns"):
            output_file += ".directionpatterns"
        full_path = "direction_patterns/" + output_file
        path = Path(full_path)
        # Ensure the folder exists, create it if necessary
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output_text)
    else:
        print(output_text)


# endregion

# region Generating time patterns

def generate_time_pattern_command(segments, time_probabilities_file, pattern_size, pattern_count, output_file, seed):
    print("Generating time pattern into file: " + output_file)
    # print("RUNNING  ARGUMENTS FOR generate_time_pattern_command, SEED=" + str(seed))
    sub_seed = lehmer_seed_combine(seed, SEED_MOD_GENERATE_TIME_PATTERN_COMMAND)
    seed_modifier = 32

    # region reading command arguments

    if len(segments) > 1:
        i = 0
        while i < len(segments):
            segment = segments[i].strip()

            if segment == '-generate time pattern':
                i += 1
            elif segment.startswith('-probabilities'):
                time_probabilities_file = segments[i].split()[1].strip()
                i += 1
            elif segment.startswith('-size'):
                if i + 1 < len(segments):
                    pattern_size = int(segments[i].split()[1].strip())
                    i += 1
                else:
                    print("Error: Missing value for -size command.")
                    sys.exit(1)
            elif segment.startswith('-patterns'):
                try:
                    pattern_count = int(segments[i].split()[1].strip())
                    i += 1
                except IndexError:
                    print("Error: Missing value for -patterns command.")
                    sys.exit(1)
                except ValueError:
                    print(f"Error: Invalid value for -patterns command: {segments[i].split()[1].strip()}")
                    sys.exit(1)
            else:
                print(f"Warning: Unrecognized command: {segment}")
                i += 1

        print("time_probabilities_file=" + str(time_probabilities_file))
        print("pattern_count=" + str(pattern_count))
        print("pattern_size=" + str(pattern_size))

    # endregion

    # region Main

    # getting probabilities of each step's outcome
    beat_probabilities, rest_probabilities = get_time_probabilities(time_probabilities_file)

    # print("Beat chances: " + str(beat_probabilities))
    # print("Rest chances: " + str(rest_probabilities))

    # probabilities = get_time_probabilities(time_probabilities_file)
    beat_weights = []
    rest_weights = []
    total_beats_weight = 0
    total_rests_weight = 0

    output_text = ""

    for x in beat_probabilities:
        total_beats_weight += x[1]
        beat_weights.append(total_beats_weight)

    for x in rest_probabilities:
        total_rests_weight += x[1]
        rest_weights.append(total_rests_weight)

    # print("beat_weights: " + str(beat_weights))
    # print("total_beats_weight: " + str(total_beats_weight))
    # print("rest_weights: " + str(rest_weights))
    # print("total_rests_weight: " + str(total_rests_weight))
    # print("Getting beat pattern with count: " + str(pattern_count) + " and size " + str(pattern_size))

    output_text = "# SEED=" + str(seed) + ", FILE=time_probabilities/" + str(time_probabilities_file) + "\n"

    for i in range(pattern_count):
        beats = []
        rests = []
        output_text += "pattern=Pattern " + str(i) + "\n"
        output_text += "time_signature=FourFour\n"

        next_beat_value = 0
        next_rest_value = 0

        j = 0
        while j < pattern_size:
            reset = False
            # region checking which beat value to add next
            random.seed(lehmer_seed_combine(sub_seed, seed_modifier))
            seed_modifier += 32
            rand_number = random.uniform(0.0, total_beats_weight)
            for w in range(len(beat_weights)):
                if rand_number < beat_weights[w]:
                    value = beat_probabilities[w][0]

                    # region Wildcards

                    # repeat last move wildcard, which moves in the same time again
                    if value == 9999:
                        # in this case the wildcard will not be viable, try another roll
                        if j == 0:
                            reset = True
                            break
                        else:
                            # repeat the last move
                            next_beat_value = beats[len(beats) - 1]
                            # print("WILDCARD 0 WAS USED")

                    # endregion

                    # standard, just add the value found
                    else:
                        next_beat_value = beat_probabilities[w][0]

                    break

            # endregion

            # region checking which rest value to add next
            random.seed(lehmer_seed_combine(sub_seed, seed_modifier))
            seed_modifier += 32
            rand_number = random.uniform(0.0, total_beats_weight)
            for w in range(len(rest_weights)):
                if rand_number < rest_weights[w]:
                    value = rest_probabilities[w][0]

                    # region Wildcards

                    # repeat last move wildcard, which moves in the same time again
                    if value == 9999:
                        # in this case the wildcard will not be viable, try another roll
                        if j == 0:
                            reset = True
                            break
                        else:
                            # repeat the last move
                            next_rest_value = rests[len(rests) - 1]
                            # print("WILDCARD 0 WAS USED")

                    # endregion

                    # standard, just add the value found
                    else:
                        next_rest_value = rest_probabilities[w][0]

                    break

            # endregion

            #  reset if there is an error, like the repeat-last wildcard being used for a first value
            if reset:
                continue

            j += 1
            # append the values found this iteration
            beats.append(next_beat_value)
            rests.append(next_rest_value)
            output_text += str(next_beat_value) + " " + str(next_rest_value) + "\n"

        # print("Beat pattern: " + str(beats))
        # print("Rest pattern: " + str(rests))

    # endregion

    if len(output_file) > 3:
        print("Writing to output file " + output_file)
        output_file = output_file.strip()
        if not output_file.endswith(".timepatterns"):
            output_file += ".timepatterns"
        full_path = "time_patterns/" + output_file
        path = Path(full_path)
        # Ensure the folder exists, create it if necessary
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output_text)
    else:
        print(output_text)


# endregion


def main_function(arguments):
    print("process_command_line ---------------------------------------")
    command = ' '.join(arguments[1:])
    segments = command.split('-')
    segments = [segment.strip() for segment in segments if segment.strip()]
    for i in range(len(segments)):
        segments[i] = "-" + segments[i]

    for i in range(len(segments)):
        if segments[i].startswith("-generate melody"):
            generate_melody_run_commands(segments)
            pass
        elif segments[i].startswith("-generate direction pattern"):
            # defaults are set here for this way
            generate_direction_pattern_command(segments, "example", 8, 60, "example")
            pass
        # print(f"Segment: {segments[i]}")


# endregion

# region Scale to midi example


def scale_to_midi_example(filename, scale_name, root_key, starting_octave):
    scale_keys = generate_scale_keys(scale_name, root_key, starting_octave)
    melody = Melody(tempo=90)
    beat_size = 0.25
    # Setting up the melody
    melody.notes = []
    melody_start_index = -1
    for i in range(len(scale_keys)):
        if scale_keys[i].value == root_key.value:
            melody_start_index = i

    if melody_start_index == -1:
        print("ERROR, scale_keys do not contain root_key")
        exit(1)

    last_key_value = scale_keys[melody_start_index].value
    for i in range(len(scale_keys)):
        next_key = scale_keys[i]
        # if it overflows past GSharp and goes to A
        if next_key.value < last_key_value:
            starting_octave += 1
        # wait time here is half of beat time
        melody.notes.append(Note(starting_octave, next_key, beat_size, beat_size / 2))
        last_key_value = next_key.value

    # Print the melody notes
    print("NOTES:")
    for note in melody.notes:
        print(str(note.key) + ", Oct: " + str(note.octave))

    melody.key_signature = root_key
    melody.time_signature = (4, 4)

    write_to_midi(filename + '.mid', melody, 8)


# endregion

# region generate_from_scale_direction_and_time

def generate_from_scale_direction_and_time(filename, root_key, scale_name, scale_use_percentage, starting_octave,
                                           seed,
                                           time_patterns_file, min_to_max_time_pattern_count,
                                           direction_patterns_file, min_to_max_direction_pattern_count):
    # region Initial setup

    beat_count = 8 # add changing this later

    scale_keys = generate_scale_keys(scale_name, root_key, starting_octave)
    seed_modifier = 32
    print("RUNNING generate_melody()")
    if not direction_patterns_file.endswith(".directionpatterns"):
        direction_patterns_file += ".directionpatterns"

    if not time_patterns_file.endswith(".timepatterns"):
        time_patterns_file += ".timepatterns"

    # endregion

    # region Removing values from scale if needed, to simplify the pieces being made

    if scale_use_percentage < 1:
        print("SCALE ARE: " + str(scale_keys))

        remove_values_count = int(math.floor(len(scale_keys) * scale_use_percentage))
        for i in range(remove_values_count):
            random.seed(lehmer_seed_combine(seed, seed_modifier))
            seed_modifier += 32
            # removed anything
            scale_keys.pop(random.randint(0, len(scale_keys) - 2))

        print("SCALE REDUCED TO: " + str(scale_keys))

    # endregion

    # region Error checking

    if len(min_to_max_time_pattern_count) != 2:
        print("min_to_max_time_pattern_count must be a list with two integers")
        exit(1)

    if len(min_to_max_direction_pattern_count) != 2:
        print("min_to_max_direction_pattern_count must be a list with two integers")
        exit(1)

    # endregion

    # region Heading text

    print("\n")
    print("Generating Melody: filename=" + str(filename) + ".mid" +
          ", root_key=" + str(root_key) +
          ", scale_name=" + str(scale_name) +
          ", starting_octave=" + str(starting_octave) +
          ", seed=" + str(seed) +
          ", time_patterns_file=" + str(time_patterns_file) +
          ", min_to_max_time_pattern_count=" + str(min_to_max_time_pattern_count),
          ", direction_patterns_file=" + str(direction_patterns_file) +
          ", min_to_max_direction_pattern_count=" + str(min_to_max_direction_pattern_count)
          )

    # endregion

    # region Getting all direction patterns

    all_direction_patterns = get_direction_patterns(direction_patterns_file)
    if all_direction_patterns is None or len(all_direction_patterns) == 0:
        print("ERROR, cannot find file in time_patterns folder or nothing is inside the file.")
        exit(1)

    # print("\nPRINTING DIRECTION PATTERNS\n")
    # for pattern in all_direction_patterns:
    #     print(str(pattern))
    # print("\n")

    # endregion

    # region Getting all time patterns

    all_time_patterns = get_time_patterns(time_patterns_file)
    if all_time_patterns is None or len(all_time_patterns) == 0:
        print("ERROR, cannot find file in time_patterns folder or nothing is inside the file.")
        exit(1)

    # print("\nPRINTING TIME PATTERNS\n")
    # for pattern in all_time_patterns:
    #     print(str(pattern))
    # print("\n")

    # endregion

    # region Choosing which direction patterns will be available for this output

    # getting direction patterns
    use_time_indexes = generate_random_indexes(all_direction_patterns, lehmer_seed_combine(seed, seed_modifier),
                                               min_to_max_direction_pattern_count)
    seed_modifier += 32
    # print("Direction indexes: " + str(use_time_indexes))
    direction_patterns = []
    for i in use_time_indexes:
        direction_patterns.append(all_direction_patterns[i])
        print(direction_patterns[len(direction_patterns) - 1])
        print(direction_patterns[len(direction_patterns) - 1].direction_changes[0])
        if i > 0 and direction_patterns[len(direction_patterns) - 1].direction_changes[0] == 0:
            # deleting the first zero since it indicates playing the first note in the data
            del direction_patterns[len(direction_patterns) - 1].direction_changes[0]
        # print("Using time pattern: " + all_direction_patterns[i].name)

    # getting time_patterns
    use_time_indexes = generate_random_indexes(all_time_patterns, lehmer_seed_combine(seed, seed_modifier),
                                               min_to_max_time_pattern_count)
    seed_modifier += 32
    # print("Time indexes: " + str(use_time_indexes))
    time_patterns = []
    for i in use_time_indexes:
        time_patterns.append(all_time_patterns[i])
        # print("Using time pattern: " + all_time_patterns[i].name)

    # endregion

    # scale_keys contains the scale. time_patterns contains the beat timing. direction_patterns contains the jumps
    # to make around the scale

    # region Getting the scale

    # the first tiny example i did has what i need for this.
    # should be easy enough to have the beat times paired with the steps around the scale.

    # endregion

    # region Second test

    print("Using the scale:")

    print("SCALE KEYS: " + str(scale_keys))

    # direction_pattern = direction_patterns[0]
    # current_direction_pattern_index = 0

    melody = Melody(tempo=90)
    melody.notes = []

    # id rather start at a random position within the key
    # sounds bad having it always start with the same note
    index = random.randint(0, len(scale_keys) - 1)
    print("INDEX was " + str(index) + ", list size is " + str(len(scale_keys)))
    start_key = scale_keys[index]

    # getting up the first position before the pitch changes happen
    current_note_position = Note(starting_octave, start_key, 0.5, 0.5)

    melody.notes.append(current_note_position)

    if not note_exists_in_scale(current_note_position, scale_keys):
        print("WARNING: The key " + current_note_position.key +
              " does not exist inside the scale: " + str(scale_keys) + ", stopping now.")
        exit(1)
    time_pattern_i = 0
    current_time_pattern_index = 0
    time_passed = 0

    # deciding on next direction_patter
    random.seed(lehmer_seed_combine(seed, seed_modifier))
    seed_modifier *= 32
    next_direction_pattern_index = random.randint(0, len(direction_patterns) - 1)
    direction_change_index = 0

    while time_passed < beat_count:
        direction_change = direction_patterns[next_direction_pattern_index].direction_changes[direction_change_index]

        random.seed(lehmer_seed_combine(seed, seed_modifier))
        seed_modifier += 32

        play_time = time_patterns[time_pattern_i].beat_times[current_time_pattern_index].play_time
        rest_time = time_patterns[time_pattern_i].beat_times[current_time_pattern_index].rest_time
        time_passed = time_passed + play_time + rest_time
        current_note_position = Note(
            current_note_position.octave,
            current_note_position.key,
            play_time,
            rest_time)
        current_note_position = jump_notes_position_in_scale(current_note_position, scale_keys, direction_change)

        melody.notes.append(current_note_position)

        current_time_pattern_index += 1
        if current_time_pattern_index == len(time_patterns[time_pattern_i].beat_times):
            current_time_pattern_index = 0

        print("ADDED NOTE " + str(melody.notes[len(melody.notes) - 1]))

        direction_change_index += 1
        if direction_change_index == len(direction_patterns[next_direction_pattern_index].direction_changes):
            # set next random pattern
            random.seed(lehmer_seed_combine(seed, seed_modifier))
            seed_modifier *= 32
            next_direction_pattern_index = random.randint(0, len(direction_patterns) - 1)
            direction_change_index = 0
        pass


    '''
    for direction_change in direction_patterns[0].direction_changes:
        current_note_position = Note(
            current_note_position.octave,
            current_note_position.key,
            time_patterns[time_pattern_i].beat_times[current_time_pattern_index].play_time,
            time_patterns[time_pattern_i].beat_times[current_time_pattern_index].rest_time)
        current_note_position = jump_notes_position_in_scale(current_note_position, scale_keys, direction_change)
        melody.notes.append(current_note_position)
        current_time_pattern_index += 1
        if current_time_pattern_index == len(time_patterns[time_pattern_i].beat_times):
            current_time_pattern_index = 0
        print("ADDED NOTE " + str(melody.notes[len(melody.notes) - 1]))
    '''

    print("MELODY FOUND")
    for x in melody.notes:
        print("     " + str(x))
    write_to_midi(filename + '.mid', melody, 8)
    return


# endregion

# region Generating with pitch and time patterns


def generate_from_time_and_pitch_patterns(filename, root_key, scale_name, starting_octave, length_in_seconds, seed,
                                          time_patterns_file, min_to_max_time_pattern_count,
                                          pitch_patterns_file, min_to_max_pitch_pattern_count):
    # region Initial setup

    seed_modifier = 64
    print("RUNNING generate_melody()")
    if not time_patterns_file.endswith(".timepatterns"):
        time_patterns_file += ".timepatterns"
    if not pitch_patterns_file.endswith(".pitchpatterns"):
        pitch_patterns_file += ".pitchpatterns"

    # endregion

    # region Error checking

    if len(min_to_max_time_pattern_count) != 2:
        print("min_to_max_time_pattern_count must be a list with two integers")
        exit(1)

    if len(min_to_max_pitch_pattern_count) != 2:
        print("min_to_max_pitch_pattern_count must be a list with two integers")
        exit(1)

    # endregion

    # region Heading text

    print("\n")
    print("Generating Melody: filename=" + str(filename) + ".mid" +
          ", root_key=" + str(root_key) +
          ", scale_name=" + str(scale_name) +
          ", starting_octave=" + str(starting_octave) +
          ", length_in_seconds=" + str(length_in_seconds) +
          ", seed=" + str(seed) +
          ", time_patterns_file=" + str(time_patterns_file) +
          ", pitch_patterns_file=" + str(pitch_patterns_file)
          )

    # endregion

    # region Getting all time patterns

    all_time_patterns = get_time_patterns(time_patterns_file)
    if all_time_patterns is None or len(all_time_patterns) == 0:
        print("ERROR, cannot find file in time_patterns folder or nothing is inside the file.")
        exit(1)

    # print("\nPRINTING TIME PATTERNS\n")
    # for pattern in all_time_patterns:
    #     print(str(pattern))
    # print("\n")

    # endregion

    # region Getting all pitch patterns

    all_pitch_patterns = get_pitch_patterns(pitch_patterns_file)
    if all_pitch_patterns == None or len(all_pitch_patterns) == 0:
        print("ERROR, cannot find file in pitch_patterns folder or nothing is inside the file.")

    # print("\nPRINTING PITCH PATTERNS\n")
    # for pattern in all_pitch_patterns:
    #     print(str(pattern))
    # print("\n")

    # endregion

    # region Getting time_patterns and pitch_patterns

    # getting time_patterns

    use_time_indexes = generate_random_indexes(all_time_patterns, lehmer_seed_combine(seed, seed_modifier),
                                               min_to_max_time_pattern_count)
    seed_modifier += 32
    # print("Time indexes: " + str(use_time_indexes))
    time_patterns = []
    for i in use_time_indexes:
        time_patterns.append(all_time_patterns[i])
        # print("Using time pattern: " + all_time_patterns[i].name)

    # getting pitch_patterns now
    use_pitch_indexes = generate_random_indexes(all_pitch_patterns, lehmer_seed_combine(seed, seed_modifier),
                                                min_to_max_pitch_pattern_count)
    seed_modifier += 32
    # print("Pitch indexes: " + str(use_pitch_indexes))
    pitch_patterns = []
    for i in use_pitch_indexes:
        pitch_patterns.append(all_pitch_patterns[i])
        # print("Using pitch pattern: " + all_pitch_patterns[i].name)

    # endregion

    # region First test, combining one time and pitch pattern

    time_pattern = time_patterns[0]
    pitch_pattern = pitch_patterns[0]
    current_time_pattern_index = 0
    print("TYPE " + str(type(time_pattern.beat_times[current_time_pattern_index])))

    melody = Melody(tempo=90)
    melody.notes = []

    # getting up the first position before the pitch changes happen
    current_note_position = Note(starting_octave, root_key, [], [])
    melody.notes.append(Note(current_note_position.octave, current_note_position.key,
                             time_pattern.beat_times[current_time_pattern_index].play_time,
                             time_pattern.beat_times[current_time_pattern_index].rest_time))
    current_time_pattern_index += 1
    if current_time_pattern_index == len(time_pattern.beat_times):
        current_time_pattern_index = 0

    for pitch_change in pitch_pattern.pitch_changes:

        current_note_position = transpose_note(current_note_position, pitch_change)

        # so right here I need to alter current_note_position based on the pitch

        melody.notes.append(Note(current_note_position.octave, current_note_position.key,
                                 time_pattern.beat_times[current_time_pattern_index].play_time,
                                 time_pattern.beat_times[current_time_pattern_index].rest_time))
        current_time_pattern_index += 1
        if current_time_pattern_index == len(time_pattern.beat_times):
            current_time_pattern_index = 0

    melody_start_index = -1

    write_to_midi(filename + '.mid', melody, 8)

    # endregion


# endregion

# region User prompts

def show_instructions():
    global scales
    scale_names = []
    for scale in scales:
        scale_names.append(scale)
    help_text = "\n\nWelcome to the MIDI Melody Generator, a program that allows for generation\n " \
                "of MIDI files based on input parameters.\n\n"
    help_text += "-----------------------------------------------------\n"
    help_text += "Getting started:\n\n"
    help_text += "This program is run by run parameters and data files. To get started\n"
    help_text += "first look at the example data files inside the folders:\n"
    help_text += "   direction_patterns, direction_probabilities, and time_patterns.\n"
    help_text += "direction_probabilities folder contains data for how direction_patterns are generated.\n"
    help_text += "direction_patterns folder contains data that determines how the generator travels\n"
    help_text += "around the scale.\n"
    help_text += "time_patterns folder contains data that determines how long beats and rests last.\n"
    help_text += "\nThe '-generate direction pattern' command shown below can be used to assist with generation of \n"
    help_text += "the direction_patterns. This command also requires setting up time_pattern data which I don't currently\n"
    help_text += "have a generation function for.\n"
    help_text += "-------------------------------------------------------------------------------------------------\n"

    help_text += "Generate Melody Run Command: \n\n"
    help_text += "  # 1. Command starts with this -----------------------------------------------------------------\n"
    help_text += "  -generate melody\n" \
                 "  # 2. Setting the musical scale to use ---------------------------------------------------------\n" \
                 "  -scale scale_name (default 'major', see below for all options.)\n" \
                 "  # 3. Setting the key to play in ---------------------------------------------------------------\n" \
                 "  -key keyname (default 'C', see below for all options.)\n" \
                 "  # 4. Setting the octave to start in -----------------------------------------------------------\n" \
                 "  -octave number (default '3')\n" \
                 "  # 5.1 Option A Setting the direction patterns filename if using your own data. ----------------\n" \
                 "  -directions filename min_to_use max_to_use (default 'example 1 3')\n" \
                 "           NOTE: This is for using your own direction_patterns data only. Use\n" \
                 "           '-direction_probabilities' instead to auto generate data. \n" \
                 "  # 5.2 Option B Setting the direction pattern probabilities file to use to  --------------------\n" \
                 "  # auto generate data. The numbers are for pattern size and count.\n" \
                 "  -direction_probabilities filename pattern_size pattern_count (default 'example 8 60')\n" \
                 "           NOTE: This overwrites the '-directions' command.\n" \
                 "  # 6.1 Option A Setting the time patterns filename if using your own data. ---------------------\n" \
                 "  -times filename min_to_use max_to_use (default 'example 1 3')\n" \
                 "  # 6.2 Option B Setting the time pattern probabilities file to use to --------------------------\n" \
                 "  # auto generate data. The numbers are for pattern size and count.\n" \
                 "  -time_probabilities filename pattern_size pattern_count (default 'example' 8 60)\n" \
                 "           NOTE: This overwrites the '-times' command.\n" \
                 "  # 7. Setting the ouput file name with appears in the output folder ----------------------------\n" \
                 "  -output_file filename (default 'melody_generated')\n" \
                 "  # 8. Setting the % of the notes in the scale to use in generation.-----------------------------\n" \
                 "  -scale_percentage value (by default 1, must be between 0.0 and 1.0)\n" \
                 "  # 9. Setting the seed to use for generation if needed. ----------------------------------------\n" \
                 "  -seed value (default uses a random number)\n" \
                 "-------------------------------------------------------------------------------------------------\n" \
                 "\n" \
                 "Starting with '-generate melody', enter command after command on a single line.\n\n" \
                 "The times file must exist inside the 'time_patterns' folder, and the directions file must exist\n" \
                 "inside the 'direction_patterns' folder. That is unless using the auto generation functions. " \
                 " \n\n"

    help_text += "All possible scale values: \n       "
    for i in range(len(scale_names)):
        help_text += scale_names[i]
        if i < (len(scale_names) - 1):
            help_text += ", "
        if i % 4 == 0 and i != (len(scale_names) - 1) and i != 0:
            help_text += "\n       "
    help_text += "\n\n"

    help_text += "All possible key values:\n       "
    key_values = [key.name for key in Key]
    for i, key in enumerate(key_values):
        help_text += key
        if i < (len(key_values) - 1):
            help_text += ", "
        if i % 7 == 0 and i != (len(key_values) - 1) and i != 0:
            help_text += "\n       "
    help_text += "\n"

    help_text += "-------------------------------------------------------------------------------------------------\n"
    help_text += "Generate Direction Pattern Run Command: \n\n"
    help_text += "-generate direction pattern\n" \
                 "commands:\n" \
                 "  -probabilities file_name (default 'example'. the file inside the\n " \
                 "     direction_probabilities folder)\n" \
                 "  -size number (default 8. the size of each generated pattern.)\n" \
                 "  -patterns number (default 60. the number of patterns to generate.)\n" \
                 "\n" \
                 "Starting with '-generate direction pattern', enter command after command on a single line.\n"
    help_text += "-------------------------------------------------------------------------------------------------\n"

    # leave here for creating more elements here
    # help_text += "Command    \n"
    # help_text += "     -mode \n"
    # help_text += "Description:\n"
    # help_text += "     -d is the \n"

    print(help_text)


# endregion

if __name__ == '__main__':

    # region (Not implemented yet) using command line parameters for running

    if len(sys.argv) > 2:
        show_instructions()
        main_function(sys.argv)
    else:
        show_instructions()

    exit(0)

    # Check if the correct number of command-line arguments is provided
    # if len(sys.argv) < 2:
    #     print("Usage: python script.py <file_path>")
    #     sys.exit(1)  # Exit with an error code

    # Get the file path from the command-line argument and load patterns
    # file_path = "time_patterns/" + sys.argv[1]

    # Check if the file exists (currently parameters are not used, so not implemented)

    # if not os.path.isfile(file_path):
    #     print(f"Error: File '{file_path}' not found.")
    #     sys.exit(1)  # Exit with an error code

    # endregion

    # region 0. Other stuff

    # region 0.1 Generate Direction Patterns

    do_this = False
    if do_this:
        # region Main
        '''
        # getting probabilities of each step's outcome
        probabilities = get_direction_probabilities("example")

        # number of values in the pattern
        pattern_count = 60
        # number of values in the pattern
        pattern_size = 8

        weights = []
        total_weight = 0
        for x in probabilities:
            total_weight += x[1]
            weights.append(total_weight)

        for i in range(pattern_count):
            pattern = [0]
            j = 0
            while j < pattern_size:
                reset = False
                rand_number = random.uniform(0.0, total_weight)
                last_move = 0
                # checking which value to use next
                for w in range(len(weights)):
                    if rand_number < weights[w]:
                        value = probabilities[w][0]

                        # region Wildcards

                        # repeat last move wildcard, which moves in the same direction again
                        if value == 9999:
                            # in this case the wildcard will not be viable, try another roll
                            if i == 0:
                                reset = True
                                break
                            else:
                                # repeat the last move
                                pattern.append(pattern[len(pattern) - 1])
                                # print("WILDCARD 0 WAS USED")

                        # endregion

                        # standard, just add the value found
                        else:
                            pattern.append(probabilities[w][0])

                        break

                # if resetting, continue and try again
                if reset:
                    continue

                j += 1

            print("pattern=Pattern " + str(i))
            print(' '.join(map(str, pattern)) + "\n")
        '''
        # endregion

    # endregion

    # endregion

    # region Try 1: scale to midi example

    do_this = False
    if do_this:
        scale_to_midi_example('scale_example', 'minor', Key.A, 2)

    # endregion

    # region Try 2: generate_from_time_and_pitch_patterns
    ''' This method works okay, although it was a cheap shortcut and not much better then
     just using music AI. My original idea of using scales is better, I may still use the time 
     patterns. But the pitch patterns that ChatGPT gives are not the best, its almost like
     they all come from stock music themselves. '''

    do_this = False
    if do_this:
        # this will only work when both files have the same name
        patterns_to_use = "example"
        generate_from_time_and_pitch_patterns('melody_generated',
                                              # in the key of
                                              Key.C, 'minor',
                                              # starting octave
                                              4,
                                              # max length in seconds
                                              60,
                                              # seed
                                              random.randint(100000000, 999999999),
                                              # time patterns file ---------------------
                                              patterns_to_use,
                                              [1, 3],  # ^^ min to max possible to use
                                              # pitch patterns file --------------------
                                              patterns_to_use,
                                              [1, 3],  # ^^ min to max possible to use
                                              )

    # endregion

    # region Try 3: generate_from_scale_and_direction_patterns

    # -generate melody -scale mixolydian -key C -octave 4 -times germaniccelticanglo 1 3 -directions tiny_jumps 2 6 -sp 0.4

    # -generate melody
    # mandatory commands:
    #   -scale scale_name
    #   -key keyname
    #   -octave number
    #   -d filename min_to_use max_to_use
    #   -t filename min_to_use max_to_use
    # optional commands:
    #   -sp value (scale percentage, by default 1, between 0.0 and 1.0)
    #   -seed value (random by default, or 0 for random if using an output filename and a random seed)
    #   -output_file filename

    # endregion
