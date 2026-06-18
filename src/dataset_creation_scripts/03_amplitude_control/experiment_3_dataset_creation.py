"""
experiment_3_dataset_creation.py
================================
Converts the 18 raw amplitude/spacing-sweep .npy files from Experiment 3
(coherent-control amplitude sweep) into a long-format dataset: one row per time
sample, saved as a pickle and a CSV.

THE MEASUREMENT — like striking a bell
    A short microwave pulse (~31 ns) is fired at the chip. It excites the
    defects. When the pulse stops, the defects keep re-radiating for a while:
    a fading echo, exactly like a bell still ringing after it is struck. That
    fading echo is the RING-DOWN, and recording it is the whole measurement.
    The technique's name, BCTDS, just labels this pulse-and-listen method.

WHAT I AND Q ARE  (the only things actually measured)
    The returning microwave is a wave. Describing a wave takes two numbers: how
    big it is, and where it is in its cycle. The detector (a "homodyne"
    receiver) reports those as two coordinates, I and Q. Picture the tip of a
    rotating arrow:

        I = the arrow's horizontal position
        Q = the arrow's vertical position

        arrow length = signal strength = sqrt(I^2 + Q^2)
        arrow angle  = phase           = atan2(Q, I)

    I and Q are the ONLY quantities the instrument measures. Strength, phase
    and frequency spectra are all just arithmetic on them — which is why this
    dataset stores I and Q and nothing derived from them.

WHAT THIS PARTICULAR EXPERIMENT DOES
    TWO pulses are fired a short gap apart. The second lands while the defects
    are still ringing from the first, so the two responses overlap and interfere
    — like two ripples meeting on a pond.

    The knob being turned here is HOW HARD the first pulse hits: its amplitude
    is stepped from 0 (no first pulse at all) up to nearly full power, in 100
    steps. The second pulse is held at a fixed, gentler strength throughout. A
    harder first strike leaves the defects ringing more strongly, which changes
    what the second pulse interferes with — so the amplitude knob steers the
    combined response. Steering it this way is what "coherent control" means.

    A second knob is the gap between the pulses (0-50 ns). The gap matters
    because the ringing dies away in roughly 100 ns: wait too long and there is
    nothing left for the second pulse to interfere with.

    This is the companion to Experiment 4: same rig, same two-pulse protocol,
    same chips. Experiment 3 sweeps the first pulse's STRENGTH; Experiment 4
    sweeps its PHASE.

HARDWARE AND UNIT WORDS USED BELOW
    AWG     the generator that builds the pulses. It counts time in "ticks"
            (its own clock steps), not in nanoseconds.
    ADC     the digitiser that samples the returning signal, 552.96 million
            times per second — one sample every ~1.8 ns.
    RFSoC   the instrument box containing both of the above.
    ticks   AWG clock steps. 308 ticks = 31.33 ns.
    a.u.    "arbitrary units" — the instrument's raw numbers, not volts.
    mK      millikelvin. 10 mK = 0.01 degrees above absolute zero.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Long format" means the table is tall and thin: every row is ONE instant in
time from ONE measurement, and the columns repeat the settings that were in
force at that instant. It is the shape pandas, SQL and most ML tooling expect.
One complete ring-down trace = 1000 consecutive rows.

7 columns, one row per time sample:

    col 0 — sample_id        which chip (0=AlOx, 1=111_oxide, 2=silicon)
    col 1 — frequency_MHz    drive frequency in MHz (fixed per sample)
    col 2 — spacing_ns       gap between the two drive pulses, in nanoseconds
    col 3 — amplitude_arb    first-pulse amplitude, the swept variable
    col 4 — timestamp_ns     time of this sample within the trace (nanoseconds)
    col 5 — I                in-phase channel value (ADC units)
    col 6 — Q                quadrature channel value (ADC units)

Only what varies gets a column. The pulse width was identical for every
measurement here, so it would be one value repeated on every row; it is
recorded in metadata.json instead.


Total rows: 3 samples x 6 spacings x 100 amplitudes x 1000 time samples
          = 1,800,000

Timestamp spacing: 1 / 552.96 MHz ~ 1.8084 ns per sample

RECORDING ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    sample (AlOx, 111_oxide, silicon)
      -> spacing_ns (0, 10, 20, 30, 40, 50)
           -> amplitude_arb (0, 300, 600, ..., 29700  -- 100 values, axis 1)
                -> timestamp_ns (0 ... ~1806.6 ns -- 1000 values, axis 2)

Each .npy file is named:
    {sample}_308_freq_{frequency_MHz}_spacing_{spacing_us}_IQ_avg_matrix.npy
and has shape (2, 100, 1000):
    axis 0 -> [I_matrix, Q_matrix]
    axis 1 -> 100 amplitude steps (np.arange(0, 30000, 300))
    axis 2 -> 1000 time samples (at 552.96 MHz ADC clock)

Note that filenames express spacing in MICROSECONDS (0.01) while this dataset
stores NANOSECONDS (10), so that the values are exactly representable in float32.

Pulse width is fixed at 308 AWG clock ticks for all files:
    pulse_width_ns = 308 / 9830.4 * 1000 ~= 31.33 ns

The three broadband *_HFSS_calibrated_3-5_GHz_IQ_avg_matrix.npy files in the
same folder are a different measurement (a 3-5 GHz frequency sweep) and are not
part of this dataset.

THE WHOLE TRACE IS KEPT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All 1000 time samples of every trace are written out. Nothing is cropped,
filtered or reduced anywhere in this script.

OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    03_amplitude_control/experiment_3/experiment_3_dataset_long.pkl
    03_amplitude_control/experiment_3/experiment_3_dataset_long.csv
    03_amplitude_control/metadata.json
    03_amplitude_control/column_info.json

    payload["data"]          shape (1_800_000, 7), float32
    payload["columns"]       shape (7,)
    payload["sample_names"]  shape (3,)  -- maps sample_id -> name string
    payload["attrs"]         experiment metadata (mirrors metadata.json)
    payload["column_doc"]    per-column semantics (mirrors column_info.json)

metadata.json and column_info.json are regenerated on every run, so they can
never drift from the code that produced the dataset.

To load in Python:

    import pickle
    import pandas as pd

    with open("experiment_3_dataset_long.pkl", "rb") as fh:
        payload = pickle.load(fh)
    df = pd.DataFrame(payload["data"], columns=payload["columns"])

    # one ring-down trace (1000 rows):
    mask  = ((df["sample_id"] == 0) & (df["spacing_ns"] == 10)
             & (df["amplitude_arb"] == 1500))
    trace = df[mask].sort_values("timestamp_ns")

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    python experiment_3_dataset_creation.py --data_dir /path/to/matrix_npy_save_folder

    Optional arguments:
        --output_dir  where to write experiment_3/ (default: next to this script)
        --no_csv      skip the CSV (pickle only)
"""

import os
import json
import pickle
import argparse
import numpy as np
from tqdm import tqdm

# The three chips measured. Each is a different material, so each hosts a
# different population of defects.
#   Sample name -> (sample_id, drive frequency in MHz)
# The drive frequency differs per sample because each chip was driven at a
# frequency where its defects ring for a long time (a strong resonance) —
# the clearest signal to study.
SAMPLES = [
    ("AlOx", 0, 3657),
    ("111_oxide", 1, 4254),
    ("silicon", 2, 4424),
]

SAMPLE_MATERIAL = {
    "AlOx": "Sapphire substrate with 2 nm ALD AlOx layer",
    "111_oxide": "Silicon (111), native SiOx surface layer",
    "silicon": "Silicon with silicon oxide",
}

# The gap between the end of pulse 1 and the start of pulse 2, one value per
# file. At 0 the two pulses touch and become one long pulse; at 50 ns the
# defects have had time to partly stop ringing before pulse 2 lands.
# Filenames express these in MICROSECONDS ("0.0", "0.01", ... "0.05"); we store
# nanoseconds because 0.01 has no exact float32 representation and 10 does.
SPACING_LIST_NS = [0, 10, 20, 30, 40, 50]

# THE KNOB THIS EXPERIMENT SWEEPS: how hard the first pulse hits, in the
# instrument's arbitrary units. 100 settings from 0 (no first pulse at all) to
# 29700 (nearly full power). This is axis 1 of every .npy file.
AMPLITUDE_LIST = np.arange(0, 30000, 300)  # -> [0, 300, 600, ..., 29700]

# How long each pulse lasts. The generator counts in its own clock steps
# ("ticks"), so 308 ticks must be converted to nanoseconds to be meaningful.
PULSE_WIDTH_TICKS = 308
AWG_CLOCK_MHZ = 9830.4  # pulse generator's clock -> 1 tick   ~= 0.1017 ns
ADC_CLOCK_MHZ = 552.96  # digitiser's clock       -> 1 sample ~= 1.8084 ns
N_TIME_SAMPLES = 1000   # how many instants are recorded per ring-down

PULSE_WIDTH_NS = (PULSE_WIDTH_TICKS / AWG_CLOCK_MHZ) * 1000  # ~= 31.33 ns

# The clock along each recorded trace. The digitiser samples every ~1.8 ns, so
# 1000 samples covers ~1.81 microseconds. Identical for every measurement, so
# it is built once and reused.
TIMESTAMPS_NS = (np.arange(N_TIME_SAMPLES) / ADC_CLOCK_MHZ) * 1000
# -> [0.000, 1.808, 3.617, ..., 1806.641]  ns

# The second pulse is held at this strength throughout while the first is swept.
PULSE2_AMPLITUDE_AU = 10000

# Only what actually varies gets a column. The pulse width was identical for
# every measurement here, so it would be one value repeated on every row — it
# lives in metadata.json instead.
COLUMN_NAMES = [
    "sample_id",
    "frequency_MHz",
    "spacing_ns",
    "amplitude_arb",
    "timestamp_ns",
    "I",
    "Q",
]

# Column name -> position, so the code below never hard-codes an index.
COL = {name: i for i, name in enumerate(COLUMN_NAMES)}

SAMPLE_NAMES = [name for name, _, _ in SAMPLES]

PICKLE_PROTOCOL = 4  # readable by Python 3.4+


# ─────────────────────────────────────────────────────────────────────────────
# METADATA — mirrored into metadata.json / column_info.json and into the pickle
# ─────────────────────────────────────────────────────────────────────────────


def build_metadata() -> dict:
    """
    Everything true of the experiment as a whole, rather than of any one row:
    which chips, which fridge, which clock rates, how the pulses were set up.

    This is written into the pickle AND to metadata.json, because a CSV can only
    hold a grid of numbers — it has nowhere to record that the fridge was at
    10 mK. Without this, the numbers alone are not interpretable.
    """
    return {
        "experiment_id": "experiment_3",
        "title": "Amplitude Control (Two-Pulse Coherent Control)",
        "data_type": "raw",
        "description": (
            "Raw BCTDS homodyne I/Q measurements of a two-pulse coherent-control "
            "protocol on TLS defect ensembles, measured on three different samples. "
            "The amplitude of the first pulse is swept while the inter-pulse spacing "
            "is varied, probing amplitude-controlled memory effects between the two "
            "pulses. Only the in-phase (I) and quadrature (Q) signals are measured; "
            "magnitude, phase, and FFT spectra are computable from them and are not "
            "stored."
        ),
        "samples": [
            {
                "sample_id": sid,
                "name": name,
                "material": SAMPLE_MATERIAL[name],
                "drive_frequency_MHz": freq,
            }
            for name, sid, freq in SAMPLES
        ],
        "apparatus": {
            "refrigerator": "Bluefors LD400 dilution refrigerator",
            "temperature": "< 10 mK",
            "waveguide": "WR-229 rectangular waveguide, 3-6 GHz passband, TE10 mode",
            "detection": "homodyne (in-phase I, quadrature Q)",
            "electronics": "RFSoC",
        },
        "clocks": {
            "awg_clock_MHz": AWG_CLOCK_MHZ,
            "adc_readout_clock_MHz": ADC_CLOCK_MHZ,
        },
        "timing": {
            "note": (
                "The instrument specifies and records time in integer hardware clock "
                "cycles, converted to nanoseconds using the relevant clock rate. Pulse "
                "duration is fixed for this experiment; the first pulse's amplitude is "
                "the primary swept variable."
            ),
            "pulse_duration": {
                "hardware_unit": "AWG clock ticks",
                "clock_MHz": AWG_CLOCK_MHZ,
                "one_tick_ns": 1000 / AWG_CLOCK_MHZ,
                "formula": "pulse_width_ns = ticks / 9830.4 * 1000",
                "fixed_ticks": PULSE_WIDTH_TICKS,
                "resulting_ns": PULSE_WIDTH_NS,
            },
            "time_axis": {
                "hardware_unit": "ADC samples",
                "clock_MHz": ADC_CLOCK_MHZ,
                "one_sample_ns": 1000 / ADC_CLOCK_MHZ,
                "formula": "timestamp_ns = sample_index / 552.96 * 1000",
                "n_samples": N_TIME_SAMPLES,
                "resulting_range_ns": [0.0, float(TIMESTAMPS_NS[-1])],
            },
        },
        "sweep": {
            "sample": {"n": len(SAMPLES), "values": SAMPLE_NAMES},
            "inter_pulse_spacing": {
                "n": len(SPACING_LIST_NS),
                "unit": "ns",
                "values": SPACING_LIST_NS,
            },
            "amplitude": {
                "n": len(AMPLITUDE_LIST),
                "unit": "arb",
                "range": [int(AMPLITUDE_LIST[0]), int(AMPLITUDE_LIST[-1])],
                "step": 300,
            },
            "time_samples_per_trace": N_TIME_SAMPLES,
        },
        "constant_drive_parameters": {
            "pulse_width_ns": PULSE_WIDTH_NS,
            "pulse_width_ticks": PULSE_WIDTH_TICKS,
            "num_pulses": 2,
            "pulse_shape": "square",
            "pulse2_amplitude_au": PULSE2_AMPLITUDE_AU,
            "pulse_phase": "the phase of both pulses is fixed for this experiment",
            "amplitude_note": (
                "The swept amplitude_arb column is the FIRST pulse's amplitude; the "
                "second pulse is held at a fixed ~10000 a.u. reference. That second "
                "value is recorded nowhere in the raw files — neither in the "
                "filenames nor in the arrays."
            ),
        },
    }


def build_column_info() -> dict:
    """
    A description of each of the 7 columns: its units, whether it is something
    we MEASURED or a setting we CHOSE, where its value came from, and what it
    physically means. Written to column_info.json.

    The measured/chosen split matters: only I and Q were measured. Everything
    else is a knob setting or a clock reading, recorded alongside so each row
    stands on its own.
    """
    return {
        "dataset": "experiment_3_amplitude_control",
        "format": "long (one row per time sample)",
        "n_rows": len(SAMPLES) * len(SPACING_LIST_NS) * len(AMPLITUDE_LIST) * N_TIME_SAMPLES,
        "n_columns": len(COLUMN_NAMES),
        "schema_rule": (
            "The filename holds everything constant within a file (sample, pulse "
            "width, frequency, spacing); the array axes hold everything that varies "
            "(amplitude, time) together with the measured I/Q."
        ),
        "columns": [
            {
                "name": "sample_id",
                "dtype": "float32",
                "unit": "categorical index",
                "role": "coordinate (categorical)",
                "measured": False,
                "varies_within_file": False,
                "computed_from": "filename token 1; see sample_names in the pickle",
                "values": {"0": "AlOx", "1": "111_oxide", "2": "silicon"},
                "n_unique": 3,
                "description": (
                    "Which sample the measurement was taken on. 0 = AlOx (sapphire + "
                    "2 nm ALD AlOx), 1 = 111_oxide (Si(111) native oxide), 2 = "
                    "silicon (silicon + silicon oxide)."
                ),
            },
            {
                "name": "frequency_MHz",
                "dtype": "float32",
                "unit": "MHz",
                "role": "coordinate (fixed per sample)",
                "measured": False,
                "varies_within_file": False,
                "computed_from": "filename field 'freq_XXXX'",
                "values": {"AlOx": 3657, "111_oxide": 4254, "silicon": 4424},
                "n_unique": 3,
                "description": (
                    "Drive frequency, held fixed for each sample at a strong "
                    "ring-down resonance. Both pulses fire at this frequency."
                ),
            },
            {
                "name": "spacing_ns",
                "dtype": "float32",
                "unit": "ns",
                "role": "coordinate (swept input)",
                "measured": False,
                "varies_within_file": False,
                "computed_from": "filename field 'spacing_X' (microseconds) x 1000",
                "values": SPACING_LIST_NS,
                "n_unique": len(SPACING_LIST_NS),
                "description": (
                    "Inter-pulse spacing: the gap between the end of the first drive "
                    "pulse and the start of the second. Stored in nanoseconds rather "
                    "than the filenames' microseconds so that the values are exactly "
                    "representable in float32. At spacing = 0 the two pulses are "
                    "contiguous, forming one double-length pulse."
                ),
            },
            {
                "name": "amplitude_arb",
                "dtype": "float32",
                "unit": "arb",
                "role": "coordinate (primary swept input)",
                "measured": False,
                "varies_within_file": True,
                "computed_from": "np.arange(0, 30000, 300); axis 1 of the raw .npy",
                "range": [int(AMPLITUDE_LIST[0]), int(AMPLITUDE_LIST[-1])],
                "n_unique": len(AMPLITUDE_LIST),
                "description": (
                    "Amplitude of the FIRST drive pulse — the primary swept variable "
                    "(100 values, 0 to 29700, step 300). At 0 there is effectively no "
                    "first pulse, which serves as the baseline. The second pulse is "
                    "held at a fixed ~10000 a.u. reference throughout. Whole numbers, "
                    "so == filtering is exact and safe."
                ),
            },
            {
                "name": "timestamp_ns",
                "dtype": "float32",
                "unit": "ns",
                "role": "coordinate (time axis)",
                "measured": False,
                "varies_within_file": True,
                "computed_from": "ADC sample index -> ns:  timestamp_ns = sample_index / 552.96 * 1000",
                "range": [0.0, float(TIMESTAMPS_NS[-1])],
                "n_unique": N_TIME_SAMPLES,
                "description": (
                    "Time of the sample within the recorded trace, measured from "
                    "t = 0 (start of the recorded window). Sample spacing = 1.8084 "
                    "ns, set by the 552.96 MHz readout clock. All 1000 samples are "
                    "kept; the trace is never trimmed."
                ),
            },
            {
                "name": "I",
                "dtype": "float32",
                "unit": "ADC arbitrary units",
                "role": "measured observable (raw)",
                "measured": True,
                "varies_within_file": True,
                "computed_from": "IQ_matrix[0] - loaded directly from the raw .npy",
                "description": (
                    "Raw in-phase homodyne signal, exactly as acquired (averaged over "
                    "shots). Note this is the measured signal, distinct from the "
                    "swept drive amplitude in amplitude_arb."
                ),
            },
            {
                "name": "Q",
                "dtype": "float32",
                "unit": "ADC arbitrary units",
                "role": "measured observable (raw)",
                "measured": True,
                "varies_within_file": True,
                "computed_from": "IQ_matrix[1] - loaded directly from the raw .npy",
                "description": (
                    "Raw quadrature homodyne signal, exactly as acquired (averaged "
                    "over shots). Combined with I to compute magnitude and phase."
                ),
            },
        ],
        "computable_not_stored": {
            "magnitude": "sqrt(I^2 + Q^2)  ==  abs(I + 1j*Q)",
            "phase": "atan2(Q, I)  ==  angle(I + 1j*Q)",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# I/O
# ─────────────────────────────────────────────────────────────────────────────


def save_pickle(payload: dict, path: str):
    with open(path, "wb") as fh:
        pickle.dump(payload, fh, protocol=PICKLE_PROTOCOL)


def load_pickle(path: str) -> dict:
    with open(path, "rb") as fh:
        return pickle.load(fh)


def write_csv(data: np.ndarray, columns: list, path: str, chunk_rows: int = 500_000):
    """
    Write the table to CSV half a million rows at a time.

    Done in chunks rather than all at once because converting millions of rows to
    text in one go would need a large amount of memory simultaneously. The header
    is written only for the first chunk; the rest append underneath.
    """
    import pandas as pd

    n = len(data)
    first = True
    with open(path, "w", newline="", encoding="utf-8") as fh:
        for start in tqdm(range(0, n, chunk_rows), desc="CSV", unit="chunk"):
            df = pd.DataFrame(data[start : start + chunk_rows], columns=columns)
            df.to_csv(fh, index=False, header=first)
            first = False


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────


def build_dataset(data_dir: str, output_dir: str, write_csv_file: bool = True):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(output_dir, "experiment_3")
    os.makedirs(output_dir, exist_ok=True)
    pkl_path = os.path.join(output_dir, "experiment_3_dataset_long.pkl")
    csv_path = os.path.join(output_dir, "experiment_3_dataset_long.csv")

    n_samples = len(SAMPLES)
    n_spacings = len(SPACING_LIST_NS)
    n_amps = len(AMPLITUDE_LIST)
    n_total_rows = n_samples * n_spacings * n_amps * N_TIME_SAMPLES  # 1,800,000

    print(f"\nFormat          : long (one row per time sample)")
    print(f"Samples         : {n_samples}  ({SAMPLE_NAMES})")
    print(f"Spacings        : {n_spacings}  ({SPACING_LIST_NS} ns)")
    print(f"Amplitudes      : {n_amps}  ({AMPLITUDE_LIST[0]}-{AMPLITUDE_LIST[-1]}, "
          f"step 300)")
    print(f"Time samples    : {N_TIME_SAMPLES} per measurement")
    print(f"Total rows      : {n_samples} x {n_spacings} x {n_amps} x "
          f"{N_TIME_SAMPLES} = {n_total_rows:,}")
    print(f"Columns         : {COLUMN_NAMES}\n")

    # Make the whole output table up front and fill it in, rather than growing it
    # row by row (which would be far slower). float32 = 4 bytes per number, so
    # 1,800,000 rows x 8 columns ~= 55 MB held in memory.
    data_all = np.empty((n_total_rows, len(COLUMN_NAMES)), dtype=np.float32)

    # Tracks how many rows have been filled so far; every trace adds 1000.
    row_idx = 0

    # Walk the files in a fixed order: each chip, then each pulse gap. That
    # pairing (sample + gap) is exactly one file on disk.
    for sample_name, sample_id, freq_mhz in tqdm(SAMPLES, desc="Samples"):

        for spacing_ns in SPACING_LIST_NS:

            # Rebuild the filename as it appears on disk. The files were named in
            # microseconds, so convert back from our nanoseconds. Zero is written
            # "0.0" rather than "0", so it gets a special case.
            spacing_us = spacing_ns / 1000
            spacing_str = "0.0" if spacing_ns == 0 else f"{spacing_us:g}"

            filename = (
                f"{sample_name}_{PULSE_WIDTH_TICKS}_freq_{freq_mhz}"
                f"_spacing_{spacing_str}_IQ_avg_matrix.npy"
            )
            filepath = os.path.join(data_dir, filename)

            if not os.path.exists(filepath):
                print(f"  WARNING: file not found -> {filename}  (skipping)")
                continue

            # One file holds a 3-D block of numbers, shape (2, 100, 1000):
            #   axis 0 -> 2      : the I channel and the Q channel
            #   axis 1 -> 100    : one entry per amplitude setting
            #   axis 2 -> 1000   : one entry per instant in the ring-down
            IQ_matrix = np.load(filepath)  # shape (2, 100, 1000)

            # SAFETY CHECK, and it matters: Experiment 4's files have IDENTICAL
            # names but hold 121 phase settings on axis 1 instead of 100
            # amplitude settings. Nothing in the filename says which knob was
            # swept, so the array's shape is the only way to tell the two apart.
            # Without this check, pointing --data_dir at the wrong folder would
            # silently produce a dataset labelled "amplitude" that actually
            # contains phases.
            if IQ_matrix.shape != (2, n_amps, N_TIME_SAMPLES):
                print(
                    f"  WARNING: {filename} has shape {IQ_matrix.shape}, expected "
                    f"(2, {n_amps}, {N_TIME_SAMPLES}) — skipping. An axis-1 length "
                    f"of 121 means this is a phase sweep (Experiment 4), not an "
                    f"amplitude sweep."
                )
                continue

            I_matrix = IQ_matrix[0]  # shape (100, 1000) — I for every amplitude
            Q_matrix = IQ_matrix[1]  # shape (100, 1000) — Q for every amplitude

            # Each amplitude setting gives one 1000-point ring-down trace, which
            # becomes 1000 consecutive rows of the output table.
            for amp_idx, amplitude in enumerate(AMPLITUDE_LIST):

                end_idx = row_idx + N_TIME_SAMPLES

                # Columns 0-4 are the settings in force for this trace. They do
                # not change during the 1000 instants, so the same value is
                # written down the whole block. That repetition is deliberate:
                # it makes every row independently filterable.
                data_all[row_idx:end_idx, COL["sample_id"]] = sample_id
                data_all[row_idx:end_idx, COL["frequency_MHz"]] = freq_mhz
                data_all[row_idx:end_idx, COL["spacing_ns"]] = spacing_ns
                data_all[row_idx:end_idx, COL["amplitude_arb"]] = amplitude

                # Columns 5-7 do change instant to instant: the clock, and the
                # two measured channels. All 1000 samples are copied — the trace
                # is never trimmed.
                data_all[row_idx:end_idx, COL["timestamp_ns"]] = TIMESTAMPS_NS
                data_all[row_idx:end_idx, COL["I"]] = I_matrix[amp_idx]  # all 1000
                data_all[row_idx:end_idx, COL["Q"]] = Q_matrix[amp_idx]  # all 1000

                row_idx += N_TIME_SAMPLES

    data_final = data_all[:row_idx]

    # ── Save ──────────────────────────────────────────────────────────────────
    print(f"\nSaving to {pkl_path} ...")

    payload = {
        "data": data_final,
        "columns": COLUMN_NAMES,
        "sample_names": SAMPLE_NAMES,
        "attrs": build_metadata(),
        "column_doc": build_column_info(),
    }
    save_pickle(payload, pkl_path)

    # Regenerate the sidecar JSONs so they can never drift from this script.
    meta_path = os.path.join(script_dir, "metadata.json")
    cols_path = os.path.join(script_dir, "column_info.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(build_metadata(), fh, indent=2)
    with open(cols_path, "w", encoding="utf-8") as fh:
        json.dump(build_column_info(), fh, indent=2)

    print(f"\nDone!")
    print(f"  Shape       : ({row_idx:,}, {len(COLUMN_NAMES)})   — rows x columns")
    print(f"  Pickle      : {pkl_path}  ({os.path.getsize(pkl_path)/1024**2:.1f} MB)")
    print(f"  metadata    : {meta_path}")
    print(f"  column_info : {cols_path}")

    # ── Sanity checks ─────────────────────────────────────────────────────────
    # These do not change the data. They re-derive facts we already expect to be
    # true and shout if any of them is not, so that a silently broken conversion
    # (a missing file, a wrong axis, a rounding trap) cannot pass unnoticed.
    print(f"\nRunning sanity checks ...")
    errors = []

    # Did every file arrive? 18 files x 100 amplitudes x 1000 instants should
    # give exactly 1,800,000 rows. A short count means a file was missing.
    if row_idx != n_total_rows:
        errors.append(
            f"  [FAIL] Row count: got {row_idx:,}, expected {n_total_rows:,} "
            f"— likely caused by missing .npy files"
        )
    else:
        print(f"  [PASS] Row count: {row_idx:,} = {n_samples} samples x {n_spacings} "
              f"spacings x {n_amps} amplitudes x {N_TIME_SAMPLES} samples")

    n_nan = int(np.sum(np.isnan(data_final)))
    n_inf = int(np.sum(np.isinf(data_final)))
    if n_nan > 0 or n_inf > 0:
        errors.append(f"  [FAIL] Data contains {n_nan} NaN and {n_inf} Inf values")
    else:
        print(f"  [PASS] No NaN or Inf values in dataset")

    # Are the measured numbers the right size? What comes BACK from the chip is a
    # few thousand a.u.; the 30000 in amplitude_arb is how hard we SHOUT, not
    # what we hear. Seeing 30000-sized numbers in I/Q would mean the drive and
    # the response had been confused somewhere.
    I_col = data_final[:, COL["I"]]
    Q_col = data_final[:, COL["Q"]]
    I_min, I_max = float(I_col.min()), float(I_col.max())
    Q_min, Q_max = float(Q_col.min()), float(Q_col.max())
    if min(I_min, Q_min) < -10000 or max(I_max, Q_max) > 10000:
        errors.append(
            f"  [FAIL] I/Q values outside expected readout range: "
            f"I=[{I_min:.0f}, {I_max:.0f}], Q=[{Q_min:.0f}, {Q_max:.0f}]"
        )
    else:
        print(f"  [PASS] I/Q readout range: I=[{I_min:.1f}, {I_max:.1f}], "
              f"Q=[{Q_min:.1f}, {Q_max:.1f}]")

    for col_idx, name, expected in [
        (COL["sample_id"], "sample IDs", n_samples),
        (COL["spacing_ns"], "spacings", n_spacings),
        (COL["amplitude_arb"], "amplitudes", n_amps),
        (COL["timestamp_ns"], "time samples", N_TIME_SAMPLES),
    ]:
        got = len(np.unique(data_final[:, col_idx]))
        if got != expected:
            errors.append(f"  [FAIL] Expected {expected} unique {name}, got {got}")
        else:
            print(f"  [PASS] Unique {name}: {got}")

    # Guards against a subtle rounding trap, and the reason spacing is stored in
    # nanoseconds rather than the filenames' microseconds. A computer cannot
    # write 0.01 exactly in this number format, so a filter like
    # `df.spacing_us == 0.01` can silently match NOTHING — returning an empty
    # result with no error, which is the worst kind of bug. Whole numbers like 10
    # are stored exactly, so the filter always works. This check proves it.
    spacing_64 = data_final[:, COL["spacing_ns"]].astype(np.float64)
    n_at_10 = int((spacing_64 == 10).sum())
    if n_at_10 == 0:
        errors.append(f"  [FAIL] spacing_ns == 10 matches no rows after float64 upcast")
    else:
        print(f"  [PASS] spacing_ns exact under float64 upcast "
              f"({n_at_10:,} rows at 10 ns)")

    ts_col = data_final[:, COL["timestamp_ns"]]
    ts_min, ts_max = float(ts_col.min()), float(ts_col.max())
    expected_ts_max = ((N_TIME_SAMPLES - 1) / ADC_CLOCK_MHZ) * 1000
    if ts_min < -0.1 or abs(ts_max - expected_ts_max) > 1.0:
        errors.append(
            f"  [FAIL] Timestamp range unexpected: [{ts_min:.3f}, {ts_max:.3f}] ns "
            f"(expected [0.000, {expected_ts_max:.3f}])"
        )
    else:
        print(f"  [PASS] Timestamp range: [{ts_min:.3f}, {ts_max:.3f}] ns")

    # Read the saved file back and confirm it is identical to what was in memory
    # — i.e. that nothing was lost or corrupted in the writing.
    reloaded = load_pickle(pkl_path)
    if not np.array_equal(reloaded["data"], data_final):
        errors.append(f"  [FAIL] Pickle round-trip: reloaded data differs from memory")
    elif list(reloaded["columns"]) != COLUMN_NAMES:
        errors.append(f"  [FAIL] Pickle round-trip: columns differ from memory")
    else:
        print(f"  [PASS] Pickle round-trip: reloaded array matches exactly")

    if errors:
        print(f"\n  {len(errors)} sanity check(s) FAILED:")
        for e in errors:
            print(e)
    else:
        print(f"\n  All sanity checks passed.")

    # ── CSV ───────────────────────────────────────────────────────────────────
    if write_csv_file:
        print(f"\nWriting CSV to {csv_path} ...")
        write_csv(data_final, COLUMN_NAMES, csv_path)
        print(f"  CSV         : {csv_path}  "
              f"({os.path.getsize(csv_path)/1024**2:.1f} MB, {row_idx:,} rows)")


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND LINE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    _script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Build the Experiment 3 raw IQ dataset (long format) as a "
        "pickle and a CSV."
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="Folder containing the *_IQ_avg_matrix.npy files "
        "(matrix_npy_save_folder)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=_script_dir,
        help="Where to write experiment_3/ (default: next to this script)",
    )
    parser.add_argument(
        "--no_csv", action="store_true", help="Skip the CSV, write only the pickle"
    )
    args = parser.parse_args()

    build_dataset(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        write_csv_file=not args.no_csv,
    )
