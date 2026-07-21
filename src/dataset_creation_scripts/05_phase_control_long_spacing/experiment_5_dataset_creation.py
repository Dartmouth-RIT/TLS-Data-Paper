"""
experiment_5_dataset_creation.py
================================
Converts the 9 raw long-spacing phase-sweep .npz files from Experiment 5
(memory effect vs inter-pulse delay) into a long-format dataset:
one row per time sample, saved as a pickle and a CSV.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAIN-LANGUAGE PRIMER  (skip if you already work on TLS defects)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THE SETUP
    A small chip (the "sample") sits inside a dilution refrigerator — a fridge
    that reaches ~0.01 kelvin, colder than deep space. The chip sits in a metal
    pipe (a "waveguide") that pipes microwaves in and carries the response out.

WHAT IS BEING STUDIED
    Real materials contain microscopic defects called TWO-LEVEL SYSTEMS (TLS).
    Each one behaves like a tiny quantum switch that can sit in one of two
    states. They are a leading source of noise in superconducting quantum
    computers, so the goal is to understand and control them.

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
    — like two ripples meeting on a pond. The PHASE of the first pulse (where in
    its cycle it starts, like a clock hand's position, 0-360 degrees) is swept
    through a full turn, which changes whether the ripples add or cancel.

    The point of THIS experiment is the gap. It is stretched from 10 ns all the
    way to 600 ns. The ringing dies away in about 100 ns, so as the gap grows
    past that, there is less and less left for the second pulse to interfere
    with — and the ability to steer the response fades out. In effect it
    measures how long the defects "remember" the first pulse.

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

6 columns, one row per time sample:

    col 0 — spacing_ns       gap between the two drive pulses, in nanoseconds
    col 1 — phase_deg        first-pulse phase in degrees, the swept variable
    col 2 — timestamp_ns     time of this sample within the trace (nanoseconds)
    col 3 — elapsed_s        wall-clock seconds since the run started
    col 4 — I                in-phase channel value (ADC units)
    col 5 — Q                quadrature channel value (ADC units)

Only what varies gets a column. This experiment used one chip, one drive
frequency (3400 MHz), one temperature (8 mK) and one pulse width — each would be
a single value repeated on every row, so they are recorded in metadata.json
instead. What remains is the two knobs (gap, phase), the clocks, and the signal.

Total rows: 9 spacings x 121 phases x 1000 time samples
          = 1,089,000

Timestamp spacing: 1 / 552.96 MHz ~ 1.8084 ns per sample

RECORDING ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    spacing_ns (10, 30, 50, 100, 200, 300, 400, 500, 600)
      -> phase_deg (0, 3, 6, ..., 360  -- 121 values, axis 1 of the .npz)
           -> timestamp_ns (0 ... ~1806.6 ns -- 1000 values, axis 2 of the .npz)

Each .npz file is named:
    308_freq_3400_spacing_{spacing_us}_ID_Shipley_phase_8mK_20251012_132853.npz
       |         |                |         |            |    |
       |         |                |         |            |    +-- run datetime
       |         |                |         |            +------- temperature set point
       |         |                |         +-------------------- sweep type
       |         |                +------------------------------ sample ID
       |         +----------------------------------------------- spacing (MICROSECONDS)
       +--------------------------------------------------------- pulse width (AWG ticks)

and contains:
    IQ_avg_matrix      (2, 121, 1000)   axis 0 -> [I, Q]
                                        axis 1 -> 121 phase steps
                                        axis 2 -> 1000 time samples
    pulse_phase_array  (121,)  int64    the phase axis, IN THE FILE
    time_stamp_list    (121,)  datetime64[s]   wall clock per phase point

Unlike Figures 3 and 4, the swept axis is stored in the file rather than being
implied by the plotting code, so this script reads pulse_phase_array directly
and validates it instead of hard-coding np.arange(0, 361, 3).

Note that filenames express spacing in MICROSECONDS (0.01) while this dataset
stores NANOSECONDS (10), so that the values are exactly representable in
float32. See experiment 4's README for the reasoning.

Pulse width is fixed at 308 AWG clock ticks for all files:
    pulse_width_ns = 308 / 9830.4 * 1000 ~= 31.33 ns

NOTE ON OVERLAP WITH EXPERIMENT 12
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
These 9 files are byte-identical to the 3400 MHz half of experiment 12's 8 mK
folder (verified by hash). Experiment 5 is the 8 mK / 3400 MHz slice of the same
acquisition campaign that produced Experiment 12; both are released separately so
that each dataset stands alone.

OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    05_phase_control_long_spacing/experiment_5/experiment_5_dataset_long.pkl
    05_phase_control_long_spacing/experiment_5/experiment_5_dataset_long.csv
    05_phase_control_long_spacing/metadata.json
    05_phase_control_long_spacing/column_info.json

    payload["data"]          shape (1_089_000, 6), float32
    payload["columns"]       shape (6,)
    payload["attrs"]         experiment metadata (mirrors metadata.json)
    payload["column_doc"]    per-column semantics (mirrors column_info.json)

To load in Python:

    import pickle
    import pandas as pd

    with open("experiment_5_dataset_long.pkl", "rb") as fh:
        payload = pickle.load(fh)
    df = pd.DataFrame(payload["data"], columns=payload["columns"])

    # one ring-down trace (1000 rows):
    mask  = (df["spacing_ns"] == 600) & (df["phase_deg"] == 0)
    trace = df[mask].sort_values("timestamp_ns")

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    python experiment_5_dataset_creation.py --data_dir /path/to/npz_data_base

    Optional arguments:
        --output_dir  where to write experiment_5/ (default: next to this script)
        --no_csv      skip the CSV (pickle only)
"""

import os
import json
import pickle
import argparse
import numpy as np
from tqdm import tqdm

# Only one sample in this experiment.
SAMPLES = [("Shipley", 0)]
SAMPLE_MATERIAL = {
    "Shipley": "Sapphire substrate with spin-coated Shipley 1813 photoresist"
}

# The one note the chip is struck at, 3.4 GHz. Unlike Experiment 4 this uses a
# single chip and a single frequency; the gap between pulses is the variable.
DRIVE_FREQUENCY_MHZ = 3400

# generate_fig_5.py: exp_ID = "Shipley_phase_8mK_20251012_132853"
EXP_ID = "Shipley_phase_8mK_20251012_132853"
TEMPERATURE_MK = 8

# THE VARIABLE OF THIS EXPERIMENT: the gap between the two pulses, one value
# per file, stretched from 10 ns to 600 ns. The defects stop ringing after
# ~100 ns, so the later gaps deliberately reach well past the point where
# there is anything left to interfere with.
# Filenames use MICROSECONDS; we store nanoseconds because 0.01 has no exact
# float32 representation and 10 does.
SPACING_LIST_NS = [10, 30, 50, 100, 200, 300, 400, 500, 600]

# Where in its cycle the first pulse starts — 121 settings covering one full
# turn of the "clock hand". Unlike Experiment 4, these .npz files store this
# axis inside them, so the script READS it and checks it against this list
# rather than assuming it.
EXPECTED_PHASE_DEG = np.arange(0, 361, 3)  # 121 values

# How long each pulse lasts. The generator counts in its own clock steps
# ("ticks"), so 308 ticks must be converted to nanoseconds to mean anything.
PULSE_WIDTH_TICKS = 308
AWG_CLOCK_MHZ = 9830.4  # pulse generator's clock -> 1 tick   ~= 0.1017 ns
ADC_CLOCK_MHZ = 552.96  # digitiser's clock       -> 1 sample ~= 1.8084 ns
N_TIME_SAMPLES = 1000   # how many instants are recorded per ring-down

PULSE_WIDTH_NS = (PULSE_WIDTH_TICKS / AWG_CLOCK_MHZ) * 1000  # ~= 31.33 ns
# The clock along each recorded trace. The digitiser samples every ~1.8 ns, so
# 1000 samples covers ~1.81 microseconds. Identical for every measurement, so
# it is built once and reused.
TIMESTAMPS_NS = (np.arange(N_TIME_SAMPLES) / ADC_CLOCK_MHZ) * 1000

# Drive amplitudes: same two-pulse protocol as Experiment 4, but the values are
# not recorded
# they appear in neither the filenames nor the .npz contents. Left unasserted.
PULSE1_AMPLITUDE_AU = None
PULSE2_AMPLITUDE_AU = None

# Pulse positions in the raw trace, in the same frame as the timestamp_ns column.
# Measured from the pulse envelope (threshold at 30% of peak: samples 442 -> 461).
# As in Experiment 4, the SECOND pulse is ANCHORED — it sits at the same place for
# every spacing — and the first pulse moves earlier as the spacing grows; verified
# across all 9 spacings.
PULSE2_START_NS = 801.14
PULSE2_END_NS = 831.87


def pulse1_start_ns(spacing_ns: float) -> float:
    """First-pulse start in raw-trace ns (pulse 2 anchored, pulse 1 slides)."""
    return PULSE2_START_NS - spacing_ns - PULSE_WIDTH_NS


# Only what actually varies gets a column. This experiment used ONE chip, ONE
# drive frequency (3400 MHz), ONE temperature (8 mK) and ONE pulse width — each
# would be a single value repeated on every row. They live in metadata.json.
# What is left is the two knobs (gap, phase) plus the clocks and the signal.
COLUMN_NAMES = [
    "spacing_ns",
    "phase_deg",
    "timestamp_ns",
    "elapsed_s",
    "I",
    "Q",
]

# Column name -> position, so the code below never hard-codes an index.
COL = {name: i for i, name in enumerate(COLUMN_NAMES)}

SAMPLE_NAMES = [name for name, _ in SAMPLES]
PICKLE_PROTOCOL = 4


def npz_filename(spacing_ns: int) -> str:
    """Filename on disk for a given spacing. Filenames use microseconds."""
    spacing_us = spacing_ns / 1000
    return (
        f"{PULSE_WIDTH_TICKS}_freq_{DRIVE_FREQUENCY_MHZ}"
        f"_spacing_{spacing_us:g}_ID_{EXP_ID}.npz"
    )


# ─────────────────────────────────────────────────────────────────────────────
# METADATA
# ─────────────────────────────────────────────────────────────────────────────


def build_metadata(run_start_iso: str = None) -> dict:
    return {
        "experiment_id": "experiment_5",
        "title": "Phase Control at Long Inter-Pulse Spacing",
        "data_type": "raw",
        "description": (
            "Raw BCTDS homodyne I/Q measurements of a two-pulse phase coherent-"
            "control protocol on a sapphire sample with spin-coated Shipley 1813 "
            "photoresist, driven at 3.4 GHz. The phase of the first pulse is swept "
            "through a full turn while the inter-pulse delay is varied from 10 to "
            "600 ns, spanning the ~100 ns ring-down lifetime, to show how coherent "
            "control is lost as the delay exceeds the bath's memory. Only the "
            "in-phase (I) and quadrature (Q) signals are measured; magnitude, "
            "phase, and FFT spectra are computable from them and are not stored."
        ),
        "samples": [
            {
                "sample_id": sid,
                "name": name,
                "material": SAMPLE_MATERIAL[name],
                "drive_frequency_MHz": DRIVE_FREQUENCY_MHZ,
            }
            for name, sid in SAMPLES
        ],
        "apparatus": {
            "refrigerator": "Bluefors LD400 dilution refrigerator",
            "temperature": f"{TEMPERATURE_MK} mK (set point, from the filename)",
            "waveguide": "WR-229 rectangular waveguide, 3-6 GHz passband, TE10 mode",
            "detection": "homodyne (in-phase I, quadrature Q)",
            "electronics": "RFSoC",
        },
        "clocks": {
            "awg_clock_MHz": AWG_CLOCK_MHZ,
            "adc_readout_clock_MHz": ADC_CLOCK_MHZ,
        },
        "timing": {
            "pulse_duration": {
                "hardware_unit": "AWG clock ticks",
                "clock_MHz": AWG_CLOCK_MHZ,
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
        "pulse_geometry": {
            "frame": "raw-trace nanoseconds, the same frame as timestamp_ns",
            "pulse2_start_ns": round(PULSE2_START_NS, 2),
            "pulse2_end_ns": round(PULSE2_END_NS, 2),
            "pulse2_is_anchored": True,
            "pulse1_start_ns_by_spacing_ns": {
                str(s): round(pulse1_start_ns(s), 2) for s in SPACING_LIST_NS
            },
            "note": (
                "The second pulse is fixed in time for every spacing; the first "
                "pulse moves earlier as the delay grows. The post-pulse ring-down "
                "therefore begins at the same absolute time in every file, so "
                "timestamp_ns is directly comparable across spacings."
            ),
            "source": (
                "Measured from the pulse envelope in the raw data (threshold at "
                "30% of peak magnitude): samples 442 -> 461."
            ),
        },
        "sweep": {
            "sample": {"n": 1, "values": SAMPLE_NAMES},
            "drive_frequency": {"n": 1, "unit": "MHz", "values": [DRIVE_FREQUENCY_MHZ]},
            "inter_pulse_spacing": {
                "n": len(SPACING_LIST_NS),
                "unit": "ns",
                "values": SPACING_LIST_NS,
                "note": "The inter-pulse delay spans 10 to 600 ns, bracketing the "
                "~100 ns ring-down lifetime.",
            },
            "pulse_phase": {
                "n": len(EXPECTED_PHASE_DEG),
                "unit": "deg",
                "range": [0, 360],
                "step": 3,
                "note": "Read from pulse_phase_array in each .npz, not assumed. "
                "0 and 360 deg are the same physical point, acquired independently.",
            },
            "time_samples_per_trace": N_TIME_SAMPLES,
        },
        "constant_drive_parameters": {
            "pulse_width_ns": PULSE_WIDTH_NS,
            "pulse_width_ticks": PULSE_WIDTH_TICKS,
            "num_pulses": 2,
            "pulse_shape": "square",
            "pulse1_amplitude_au": PULSE1_AMPLITUDE_AU,
            "pulse2_amplitude_au": PULSE2_AMPLITUDE_AU,
            "amplitude_note": (
                "This experiment uses the same two-pulse protocol as Experiment 4, but "
                "does not restate the drive amplitudes, and they appear in neither "
                "the filenames nor the .npz contents. Experiment 4 used 30000 a.u. "
                "(first pulse) and 10000 a.u. (second); that is NOT asserted here. "
                "Confirm with the team before relying on it."
            ),
        },
        "overlap_with_other_experiments": {
            "experiment_12": (
                "These 9 files are byte-identical to the 3400 MHz half of "
                "experiment 12's 8 mK folder (verified by hash). Experiment 5 is the "
                "8 mK / 3400 MHz slice of the same acquisition campaign that "
                "produced Experiment 12 (shared run ID "
                f"'{EXP_ID}'). Both are released separately so each dataset stands "
                "alone."
            )
        },
        "acquisition": {
            "run_id": EXP_ID,
            "run_start_utc": run_start_iso,
            "elapsed_s_note": (
                "elapsed_s is wall-clock seconds since run_start_utc, taken from "
                "the time_stamp_list array inside each .npz (one entry per phase "
                "point). Stored as elapsed seconds rather than an absolute epoch "
                "because float32 cannot represent Unix timestamps to better than "
                "~128 s."
            ),
        },
    }


def build_column_info() -> dict:
    return {
        "dataset": "experiment_5_phase_control_long_spacing",
        "format": "long (one row per time sample)",
        "n_rows": len(SPACING_LIST_NS) * len(EXPECTED_PHASE_DEG) * N_TIME_SAMPLES,
        "n_columns": len(COLUMN_NAMES),
        "schema_rule": (
            "The filename holds everything constant within a file (sample, pulse "
            "width, frequency, spacing, temperature); the array axes hold what "
            "varies (phase, time) together with the measured I/Q. The phase axis "
            "and the per-phase wall clock are stored inside the .npz."
        ),
        "columns": [
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
                "description": "Gap between the end of the first pulse and the "
                "start of the second, 10 to 600 ns. Stored in nanoseconds rather "
                "than the filenames' microseconds so the values are exact in "
                "float32. Spans the ~100 ns ring-down lifetime.",
            },
            {
                "name": "phase_deg",
                "dtype": "float32",
                "unit": "deg",
                "role": "coordinate (primary swept input)",
                "measured": False,
                "varies_within_file": True,
                "computed_from": "pulse_phase_array, stored in each .npz; axis 1",
                "range": [0, 360],
                "n_unique": len(EXPECTED_PHASE_DEG),
                "description": "Phase of the FIRST pulse; the primary swept "
                "variable. The second pulse's phase is held fixed. 0 and 360 deg "
                "are the same physical point, acquired independently.",
            },
            {
                "name": "timestamp_ns",
                "dtype": "float32",
                "unit": "ns",
                "role": "coordinate (time axis)",
                "measured": False,
                "varies_within_file": True,
                "computed_from": "sample_index / 552.96 * 1000; axis 2",
                "range": [0.0, float(TIMESTAMPS_NS[-1])],
                "n_unique": N_TIME_SAMPLES,
                "description": "Time within the recorded trace. Directly comparable "
                "across spacings because the second pulse is anchored.",
            },
            {
                "name": "elapsed_s",
                "dtype": "float32",
                "unit": "s",
                "role": "acquisition metadata",
                "measured": False,
                "varies_within_file": True,
                "computed_from": "time_stamp_list in each .npz, minus the run start",
                "description": "Wall-clock seconds since the run started, recorded "
                "once per phase point. Gives the acquisition order and allows drift "
                "over the run to be checked. Constant across the 1000 time samples "
                "of a single trace.",
            },
            {
                "name": "I",
                "dtype": "float32",
                "unit": "ADC arbitrary units",
                "role": "measured observable (raw)",
                "measured": True,
                "varies_within_file": True,
                "computed_from": "IQ_avg_matrix[0], loaded directly from the .npz",
                "description": "Raw in-phase homodyne signal, averaged over shots.",
            },
            {
                "name": "Q",
                "dtype": "float32",
                "unit": "ADC arbitrary units",
                "role": "measured observable (raw)",
                "measured": True,
                "varies_within_file": True,
                "computed_from": "IQ_avg_matrix[1], loaded directly from the .npz",
                "description": "Raw quadrature homodyne signal, averaged over "
                "shots. Combined with I to compute magnitude and phase.",
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
    """Write the array to CSV in chunks, to bound memory use."""
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
    output_dir = os.path.join(output_dir, "experiment_5")
    os.makedirs(output_dir, exist_ok=True)
    pkl_path = os.path.join(output_dir, "experiment_5_dataset_long.pkl")
    csv_path = os.path.join(output_dir, "experiment_5_dataset_long.csv")

    n_spacings = len(SPACING_LIST_NS)
    n_phases = len(EXPECTED_PHASE_DEG)
    n_total_rows = n_spacings * n_phases * N_TIME_SAMPLES  # 1,089,000

    print(f"\nFormat          : long (one row per time sample)")
    print(f"Sample          : {SAMPLE_NAMES[0]} (sapphire + Shipley 1813)")
    print(f"Frequency       : {DRIVE_FREQUENCY_MHZ} MHz")
    print(f"Temperature     : {TEMPERATURE_MK} mK")
    print(f"Spacings        : {n_spacings}  ({SPACING_LIST_NS} ns)")
    print(f"Phases          : {n_phases}  (0-360 deg, step 3)")
    print(f"Time samples    : {N_TIME_SAMPLES} per measurement")
    print(f"Total rows      : {n_spacings} x {n_phases} x {N_TIME_SAMPLES} "
          f"= {n_total_rows:,}")
    print(f"Columns         : {COLUMN_NAMES}\n")

    # ── Pass 1: find the run start, so elapsed_s is relative to it ────────────
    run_start = None
    for spacing_ns in SPACING_LIST_NS:
        path = os.path.join(data_dir, npz_filename(spacing_ns))
        if not os.path.exists(path):
            continue
        with np.load(path, allow_pickle=True) as z:
            t0 = z["time_stamp_list"][0]
        run_start = t0 if run_start is None else min(run_start, t0)
    if run_start is None:
        raise FileNotFoundError(
            f"No Experiment 5 .npz files found in {data_dir}\n"
            f"Expected e.g. {npz_filename(SPACING_LIST_NS[0])}"
        )
    print(f"Run start (from time_stamp_list): {run_start}\n")

    # ── Pass 2: build ────────────────────────────────────────────────────────
    data_all = np.empty((n_total_rows, len(COLUMN_NAMES)), dtype=np.float32)
    row_idx = 0
    sample_id = SAMPLES[0][1]

    for spacing_ns in tqdm(SPACING_LIST_NS, desc="Spacings"):

        filename = npz_filename(spacing_ns)
        filepath = os.path.join(data_dir, filename)

        if not os.path.exists(filepath):
            print(f"  WARNING: file not found -> {filename}  (skipping)")
            continue

        with np.load(filepath, allow_pickle=True) as z:
            IQ_matrix = z["IQ_avg_matrix"]
            phase_array = z["pulse_phase_array"]
            time_stamps = z["time_stamp_list"]

        if IQ_matrix.shape != (2, n_phases, N_TIME_SAMPLES):
            print(f"  WARNING: {filename} has shape {IQ_matrix.shape}, expected "
                  f"(2, {n_phases}, {N_TIME_SAMPLES}) — skipping")
            continue

        # The phase axis is in the file; verify rather than assume.
        if not np.array_equal(phase_array, EXPECTED_PHASE_DEG):
            print(f"  WARNING: {filename} pulse_phase_array does not match "
                  f"np.arange(0, 361, 3) — using the file's own axis")

        # Wall-clock time, i.e. when this reading was actually taken in the lab.
        # Stored as SECONDS SINCE THE RUN STARTED rather than a calendar date:
        # float32 cannot hold a full unix timestamp accurately (it would be wrong
        # by ~2 minutes), but a few thousand elapsed seconds it stores exactly.
        # Not to be confused with timestamp_ns — that is the fast axis WITHIN one
        # ring-down (nanoseconds); this is the slow axis ACROSS the run (seconds).
        elapsed = (time_stamps - run_start).astype("timedelta64[s]").astype(np.float64)

        I_matrix = IQ_matrix[0]
        Q_matrix = IQ_matrix[1]

        for phase_idx, phase_deg in enumerate(phase_array):

            end_idx = row_idx + N_TIME_SAMPLES

            data_all[row_idx:end_idx, COL["spacing_ns"]] = spacing_ns
            data_all[row_idx:end_idx, COL["phase_deg"]] = phase_deg
            data_all[row_idx:end_idx, COL["timestamp_ns"]] = TIMESTAMPS_NS
            data_all[row_idx:end_idx, COL["elapsed_s"]] = elapsed[phase_idx]
            data_all[row_idx:end_idx, COL["I"]] = I_matrix[phase_idx]  # all 1000
            data_all[row_idx:end_idx, COL["Q"]] = Q_matrix[phase_idx]  # all 1000

            row_idx += N_TIME_SAMPLES

    data_final = data_all[:row_idx]

    # ── Save ─────────────────────────────────────────────────────────────────
    run_start_iso = str(run_start)
    print(f"\nSaving to {pkl_path} ...")

    payload = {
        "data": data_final,
        "columns": COLUMN_NAMES,
        "attrs": build_metadata(run_start_iso),
        "column_doc": build_column_info(),
    }
    save_pickle(payload, pkl_path)

    meta_path = os.path.join(script_dir, "metadata.json")
    cols_path = os.path.join(script_dir, "column_info.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(build_metadata(run_start_iso), fh, indent=2)
    with open(cols_path, "w", encoding="utf-8") as fh:
        json.dump(build_column_info(), fh, indent=2)

    print(f"\nDone!")
    print(f"  Shape       : ({row_idx:,}, {len(COLUMN_NAMES)})")
    print(f"  Pickle      : {pkl_path}  ({os.path.getsize(pkl_path)/1024**2:.1f} MB)")
    print(f"  metadata    : {meta_path}")
    print(f"  column_info : {cols_path}")

    # ── Sanity checks ────────────────────────────────────────────────────────
    print(f"\nRunning sanity checks ...")
    errors = []

    if row_idx != n_total_rows:
        errors.append(f"  [FAIL] Row count: got {row_idx:,}, expected {n_total_rows:,}")
    else:
        print(f"  [PASS] Row count: {row_idx:,} = {n_spacings} spacings x "
              f"{n_phases} phases x {N_TIME_SAMPLES} samples")

    # I and Q must never be NaN. (Unlike experiment 11, nothing in this
    # experiment is legitimately missing.)
    iq = data_final[:, [COL["I"], COL["Q"]]]
    n_nan = int(np.isnan(iq).sum())
    if n_nan:
        errors.append(f"  [FAIL] I/Q contain {n_nan} NaN values")
    else:
        print(f"  [PASS] No NaN in I/Q")

    I_min, I_max = float(data_final[:, COL["I"]].min()), float(data_final[:, COL["I"]].max())
    Q_min, Q_max = float(data_final[:, COL["Q"]].min()), float(data_final[:, COL["Q"]].max())
    print(f"  [INFO] I range: [{I_min:.1f}, {I_max:.1f}]   "
          f"Q range: [{Q_min:.1f}, {Q_max:.1f}]")

    for col_idx, name, expected in [
        (COL["spacing_ns"], "spacings", n_spacings),
        (COL["phase_deg"], "phases", n_phases),
        (COL["timestamp_ns"], "time samples", N_TIME_SAMPLES),
    ]:
        got = len(np.unique(data_final[:, col_idx]))
        if got != expected:
            errors.append(f"  [FAIL] Expected {expected} unique {name}, got {got}")
        else:
            print(f"  [PASS] Unique {name}: {got}")

    # spacing_ns must survive a float64 upcast (microseconds would not)
    spacing_64 = data_final[:, COL["spacing_ns"]].astype(np.float64)
    n_at_600 = int((spacing_64 == 600).sum())
    if n_at_600 == 0:
        errors.append(f"  [FAIL] spacing_ns == 600 matches no rows after upcast")
    else:
        print(f"  [PASS] spacing_ns exact under float64 upcast "
              f"({n_at_600:,} rows at 600 ns)")

    el = data_final[:, COL["elapsed_s"]]
    print(f"  [INFO] elapsed_s range: [{el.min():.0f}, {el.max():.0f}] s "
          f"({(el.max()-el.min())/60:.1f} min run)")

    reloaded = load_pickle(pkl_path)
    if not np.array_equal(reloaded["data"], data_final):
        errors.append("  [FAIL] Pickle round-trip: reloaded data differs")
    else:
        print(f"  [PASS] Pickle round-trip: reloaded array matches exactly")

    if errors:
        print(f"\n  {len(errors)} sanity check(s) FAILED:")
        for e in errors:
            print(e)
    else:
        print(f"\n  All sanity checks passed.")

    # ── CSV ──────────────────────────────────────────────────────────────────
    if write_csv_file:
        print(f"\nWriting CSV to {csv_path} ...")
        write_csv(data_final, COLUMN_NAMES, csv_path)
        print(f"  CSV         : {csv_path}  "
              f"({os.path.getsize(csv_path)/1024**2:.1f} MB, {row_idx:,} rows)")


if __name__ == "__main__":

    _script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Build the Experiment 5 raw IQ dataset (long format) as a pickle "
        "and a CSV."
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="Folder containing the Experiment 5 *.npz files (npz_data_base)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=_script_dir,
        help="Where to write experiment_5/ (default: next to this script)",
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
