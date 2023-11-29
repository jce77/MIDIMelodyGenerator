# MIDIMelodyGenerator
 Allows for generation of MIDI files based on input parameters.

## Getting Started

This program is run by run parameters and data files. To get started, first look at the example data files inside the folders: `direction_patterns`, `direction_probabilities`, and `time_patterns`.

- `direction_probabilities` folder contains data for how `direction_patterns` are generated.
- `direction_patterns` folder contains data that determines how the generator travels around the scale.
- `time_patterns` folder contains data that determines how long beats and rests last.

The `-generate direction pattern` command shown below can be used to assist with the generation of `direction_patterns`. This command also requires setting up time_pattern data, which I don't currently have a generation function for.

## Generate Melody Run Command

```bash
  # 1. Command starts with this -----------------------------------------------------------------
  -generate melody
  # 2. Setting the musical scale to use ---------------------------------------------------------
  -scale scale_name (default 'major', see below for all options.)
  # 3. Setting the key to play in ---------------------------------------------------------------
  -key keyname (default 'C', see below for all options.)
  # 4. Setting the octave to start in -----------------------------------------------------------
  -octave number (default '3')
  # 5.1 Option A Setting the direction patterns filename if using your own data. ----------------
  -directions filename min_to_use max_to_use (default 'example 1 3')
           NOTE: This is for using your own direction_patterns data only. Use
           '-direction_probabilities' instead to auto generate data. 
  # 5.2 Option B Setting the direction pattern probabilities file to use to  --------------------
  # auto generate data. The numbers are for pattern size and count.
  -direction_probabilities filename pattern_size pattern_count (default 'example 8 60')
           NOTE: This overwrites the '-directions' command.
  # 6.1 Option A Setting the time patterns filename if using your own data. ---------------------
  -times filename min_to_use max_to_use (default 'example 1 3')
  # 6.2 Option B Setting the time pattern probabilities file to use to --------------------------
  # auto generate data. The numbers are for pattern size and count.
  -time_probabilities filename pattern_size pattern_count (default 'example' 8 60)
           NOTE: This overwrites the '-times' command.
  # 7. Setting the ouput file name with appears in the output folder ----------------------------
  -output_file filename (default 'melody_generated')
  # 8. Setting the % of the notes in the scale to use in generation.-----------------------------
  -scale_percentage value (by default 1, must be between 0.0 and 1.0)
  # 9. Setting the seed to use for generation if needed. ----------------------------------------
  -seed value (default uses a random number)
```

Starting with '-generate melody', enter command after command on a single line.

The times file must exist inside the 'time_patterns' folder, and the directions file must exist
inside the 'direction_patterns' folder. That is unless using the auto generation functions.  

All possible scale values: 

       major, minor, dorian, mixolydian, phrygian, 
       harmonic_minor, melodic_minor, whole_tone, pentatonic_major, 
       pentatonic_minor, octatonic_whole_half, octatonic_half_whole, enigmatic, 
       neapolitan_major, neapolitan_minor

All possible key values:

       A, ASharp, B, C, CSharp, D, DSharp, E, 
       F, FSharp, G, GSharp

## Generate Direction Pattern Run Command

```bash
-generate direction pattern
commands:
  -probabilities file_name (default 'example'. the file inside the direction_probabilities folder)
  -size number (default 8. the size of each generated pattern.)
  -patterns number (default 60. the number of patterns to generate.)
```
Starting with '-generate direction pattern', enter command after command on a single line.

--------------------------------------------------------------------------------
For updates and documentation, please visit: [https://github.com/jce77/MIDIMelodyGenerator  ](https://github.com/jce77/MIDIMelodyGenerator  )

To make a donation, please visit: [https://ko-fi.com/jcecode](https://ko-fi.com/jcecode)

--------------------------------------------------------------------------------