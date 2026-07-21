"""
experiment_2_dataset_creation.py
================================
Converts the 42 raw pulse-width-sweep .npy files from Experiment 2 into a
long-format dataset: one row per time sample, saved as a pickle and a CSV.

THE MEASUREMENT — like striking a bell
    A short microwave pulse is fired at the chip. It excites the defects. When
    the pulse stops, the defects keep re-radiating for a while: a fading echo,
    exactly like a bell still ringing after it is struck. That fading echo is
    the RING-DOWN, and recording it is the whole measurement. The technique's
    name, BCTDS, just labels this pulse-and-listen method.

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
    Only ONE pulse here — no interference, no phase sweep. Two knobs are turned.

    First, HOW LONG the pulse lasts: 42 settings from about 5 ns to about 214
    ns. A brief tap and a long push excite the defects differently, and the
    ring-down that follows changes shape accordingly.

    Second, WHICH NOTE the pulse is played at: the drive frequency is stepped
    across 4100-4599 MHz in 1 MHz steps (500 settings), asking the chip "which
    notes do you ring at?".

    Every combination is measured, so the result is a 42 x 500 grid, each cell
    holding one complete ring-down recording.

HARDWARE AND UNIT WORDS USED BELOW
    AWG     the generator that builds the pulses. It counts time in "ticks"
            (its own clock steps), not in nanoseconds.
    ADC     the digitiser that samples the returning signal, 552.96 million
            times per second — one sample every ~1.8 ns.
    RFSoC   the instrument box containing both of the above.
    ticks   AWG clock steps. 1 tick = ~0.1017 ns.
    a.u.    "arbitrary units" — the instrument's raw numbers, not volts.
    mK      millikelvin. 10 mK = 0.01 degrees above absolute zero.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Long format" means the table is tall and thin: every row is ONE instant in
time from ONE measurement, and the columns repeat the settings that were in
force at that instant. It is the shape pandas, SQL and most ML tooling expect.
One complete ring-down trace = 1000 consecutive rows.

5 columns, one row per time sample:

    col 0 — pulse_width_ns   how long the drive pulse lasted (swept variable)
    col 1 — frequency_MHz    drive frequency in MHz (swept variable)
    col 2 — timestamp_ns     time of this sample within the trace (nanoseconds)
    col 3 — I                in-phase channel value (ADC units)
    col 4 — Q                quadrature channel value (ADC units)

There is no sample_id column: this experiment used a single chip. Which chip it
was is recorded in metadata.json.

Total rows: 42 pulse widths x 500 frequencies x 1000 time samples
          = 21,000,000

This is the largest dataset in the series by row count. The CSV runs to roughly
a gigabyte and takes a few minutes to write; use --no_csv to skip it.

Timestamp spacing: 1 / 552.96 MHz ~ 1.8084 ns per sample

RECORDING ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    pulse_width (50, 100, 150, ..., 2100 ticks  -- 42 files)
      -> frequency_MHz (4100, 4101, ..., 4599  -- 500 values, axis 1 of the .npy)
           -> timestamp_ns (0 ... ~1806.6 ns -- 1000 values, axis 2 of the .npy)

Each .npy file is named for its pulse width in AWG ticks:
    {ticks}_IQ_avg_matrix_0.npy        e.g. 300_IQ_avg_matrix_0.npy
and has shape (2, 500, 1000):
    axis 0 -> [I_matrix, Q_matrix]
    axis 1 -> 500 drive frequencies (np.arange(4100, 4600, 1), in MHz)
    axis 2 -> 1000 time samples (at 552.96 MHz ADC clock)

The other files sitting in the same folder — full_record_log_mag.npy,
full_record_phase_fft.npy, slice_*_at_diff_widths.npy, peak_plot_data.npz,
phase_fft_slice_and_avg.npz — are DERIVED results, not raw measurements, and are
not part of this dataset.

pulse_width_ns is a converted value (ticks / 9830.4 * 1000), so it lands on
awkward numbers like 5.0863 and 30.5176 that a computer cannot store exactly.
Testing one for equality is therefore unreliable — it can match NOTHING and
return an empty result with no error:

    df[df.pulse_width_ns == 30.5176]              # may match nothing
    df[np.isclose(df.pulse_width_ns, 30.5176)]    # do this instead

frequency_MHz is whole numbers, so == is exact and safe there.
The 42 available pulse widths are listed in metadata.json under
sweep.pulse_width.values_ns.

THE WHOLE TRACE IS KEPT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All 1000 time samples of every trace are written out. Nothing is cropped,
filtered or reduced anywhere in this script.

OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    02_pulse_width_sweep/experiment_2/experiment_2_dataset_long.pkl
    02_pulse_width_sweep/experiment_2/experiment_2_dataset_long.csv
    02_pulse_width_sweep/metadata.json
    02_pulse_width_sweep/column_info.json

    payload["data"]        shape (21_000_000, 5), float32
    payload["columns"]     shape (5,)
    payload["attrs"]       experiment metadata (mirrors metadata.json)
    payload["column_doc"]  per-column semantics (mirrors column_info.json)

metadata.json and column_info.json are regenerated on every run, so they can
never drift from the code that produced the dataset.

To load in Python:

    import pickle
    import numpy as np
    import pandas as pd

    with open("experiment_2_dataset_long.pkl", "rb") as fh:
        payload = pickle.load(fh)
    df = pd.DataFrame(payload["data"], columns=payload["columns"])

    # one ring-down trace (1000 rows):
    mask  = np.isclose(df["pulse_width_ns"], 30.5176) & (df["frequency_MHz"] == 4254)
    trace = df[mask].sort_values("timestamp_ns")

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    python experiment_2_dataset_creation.py --data_dir /path/to/matrix_npy

    Optional arguments:
        --output_dir  where to write experiment_2/ (default: next to this script)
        --no_csv      skip the CSV (pickle only)
"""

import os
import json
import pickle
import argparse
import numpy as np
from tqdm import tqdm


# ONE chip only, which is why there is no sample_id column. Recorded here so the
# fact is not lost; it also goes into metadata.json.
SAMPLE_NAME = "Si_111_native_oxide"
SAMPLE_MATERIAL = "Silicon (111), native SiOx surface layer"
SAMPLE_SUPPLIER = "WaferPro"

# FIRST SWEPT KNOB: how long the drive pulse lasts, in the generator's own clock
# steps. 42 settings from 50 to 2100 ticks — roughly 5 ns to 214 ns. Each value
# is one file on disk, and the tick count IS the filename.
PULSE_WIDTH_TICKS_LIST = np.arange(50, 2101, 50)  # 42 values, in ticks

# SECOND SWEPT KNOB: which note the chip is struck at. 500 settings, 1 MHz
# apart. This is axis 1 of every file.
FREQUENCY_LIST_MHZ = np.arange(4100, 4600, 1)  # 500 values

AWG_CLOCK_MHZ = 9830.4  # pulse generator's clock -> 1 tick   ~= 0.1017 ns
ADC_CLOCK_MHZ = 552.96  # digitiser's clock       -> 1 sample ~= 1.8084 ns
N_TIME_SAMPLES = 1000   # how many instants are recorded per ring-down

N_PULSE_WIDTHS = len(PULSE_WIDTH_TICKS_LIST)  # 42
N_FREQUENCIES = len(FREQUENCY_LIST_MHZ)  # 500

# Convert the generator's tick counts into physical nanoseconds, once.
# -> [5.086, 10.173, ..., 213.623] ns
PULSE_WIDTHS_NS = (PULSE_WIDTH_TICKS_LIST / AWG_CLOCK_MHZ) * 1000

# The clock along each recorded trace. The digitiser samples every ~1.8 ns, so
# 1000 samples covers ~1.81 microseconds. Identical for every measurement, so
# it is built once and reused.
TIMESTAMPS_NS = (np.arange(N_TIME_SAMPLES) / ADC_CLOCK_MHZ) * 1000
# -> [0.000, 1.808, 3.617, ..., 1806.641]  ns

# How hard the pulse pushes, in the instrument's arbitrary units. Fixed here —
# this experiment varies duration and frequency, not strength.
DRIVE_AMPLITUDE_AU = 30000

# Five columns, exactly as the original release had them. Deliberately no
# sample_id (a single chip) and no tick count (see the filtering note above).
COLUMN_NAMES = ["pulse_width_ns", "frequency_MHz", "timestamp_ns", "I", "Q"]

PICKLE_PROTOCOL = 4  # readable by Python 3.4+


def npy_filename(ticks: int) -> str:
    """The file for one pulse width. The tick count is the whole name."""
    return f"{ticks}_IQ_avg_matrix_0.npy"


# ─────────────────────────────────────────────────────────────────────────────
# METADATA — mirrored into metadata.json / column_info.json and into the pickle
# ─────────────────────────────────────────────────────────────────────────────


def build_metadata() -> dict:
    """
    Everything true of the experiment as a whole, rather than of any one row:
    which chip, which fridge, which clock rates, how the pulse was set up.

    This is written into the pickle AND to metadata.json, because a CSV can only
    hold a grid of numbers — it has nowhere to record that the fridge was at
    10 mK, or which chip this was. Without it the numbers are not interpretable.
    """
    return {
        "experiment_id": "experiment_2",
        "title": "Pulse-Width Sweep",
        "data_type": "raw",
        "description": (
            "Raw BCTDS homodyne I/Q measurements of two-level-system (TLS) defect "
            "ensembles in a silicon native-oxide sample, recorded while sweeping the "
            "duration of a single square microwave drive pulse across 500 drive "
            "frequencies. Only the in-phase (I) and quadrature (Q) signals are "
            "measured; magnitude, phase, and FFT spectra are computable from them "
            "and are not stored."
        ),
        "sample": {
            "name": SAMPLE_NAME,
            "material": SAMPLE_MATERIAL,
            "supplier": SAMPLE_SUPPLIER,
            "defect_host": "surface native oxide layer",
            "note": "A single chip was used, so the dataset has no sample_id column.",
        },
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
                "cycles. These are converted to nanoseconds using the relevant clock "
                "rate. Pulse duration and the time axis use two independent clock "
                "domains."
            ),
            "pulse_duration": {
                "hardware_unit": "AWG clock ticks",
                "clock_MHz": AWG_CLOCK_MHZ,
                "one_tick_ns": 1000 / AWG_CLOCK_MHZ,
                "formula": "pulse_width_ns = ticks / 9830.4 * 1000",
                "swept_ticks": "50, 100, ..., 2100 (42 values, step 50)",
                "resulting_range_ns": [
                    round(float(PULSE_WIDTHS_NS[0]), 3),
                    round(float(PULSE_WIDTHS_NS[-1]), 3),
                ],
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
            "pulse_width": {
                "n": N_PULSE_WIDTHS,
                "unit": "ns",
                "range": [
                    round(float(PULSE_WIDTHS_NS[0]), 3),
                    round(float(PULSE_WIDTHS_NS[-1]), 3),
                ],
                "ticks": PULSE_WIDTH_TICKS_LIST.tolist(),
                "values_ns": [round(float(v), 4) for v in PULSE_WIDTHS_NS],
            },
            "drive_frequency": {
                "n": N_FREQUENCIES,
                "unit": "MHz",
                "range": [int(FREQUENCY_LIST_MHZ[0]), int(FREQUENCY_LIST_MHZ[-1])],
                "step_MHz": 1,
            },
            "time_samples_per_trace": N_TIME_SAMPLES,
        },
        "constant_drive_parameters": {
            "drive_amplitude_au": DRIVE_AMPLITUDE_AU,
            "num_pulses": 1,
            "pulse_shape": "square",
            "amplitude_note": (
                "The drive amplitude is recorded nowhere in the raw files — neither "
                "in the filenames nor in the arrays."
            ),
        },
        "filtering_caveat": (
            "pulse_width_ns is a converted value (ticks / 9830.4 * 1000) and lands on "
            "numbers a computer cannot store exactly, so `df.pulse_width_ns == "
            "30.5176` may silently match nothing. Use np.isclose() instead. The 42 "
            "exact values are listed under sweep.pulse_width.values_ns. "
            "frequency_MHz is whole numbers, so == is safe there."
        ),
    }


def build_column_info() -> dict:
    """
    A description of each of the 5 columns: its units, whether it is something
    we MEASURED or a setting we CHOSE, where its value came from, and what it
    physically means. Written to column_info.json.

    The measured/chosen split matters: only I and Q were measured. Everything
    else is a knob setting or a clock reading, recorded alongside so each row
    stands on its own.
    """
    return {
        "dataset": "experiment_2_pulse_width_sweep",
        "format": "long (one row per time sample)",
        "n_rows": N_PULSE_WIDTHS * N_FREQUENCIES * N_TIME_SAMPLES,
        "n_columns": len(COLUMN_NAMES),
        "schema_rule": (
            "The filename holds the one value that is constant within a file (the "
            "pulse width); the array axes hold what varies (frequency, time) "
            "together with the measured I/Q."
        ),
        "columns": [
            {
                "name": "pulse_width_ns",
                "dtype": "float32",
                "unit": "ns",
                "role": "coordinate (swept input)",
                "measured": False,
                "varies_within_file": False,
                "computed_from": "the filename's tick count / 9830.4 * 1000",
                "n_unique": N_PULSE_WIDTHS,
                "range": [
                    round(float(PULSE_WIDTHS_NS[0]), 3),
                    round(float(PULSE_WIDTHS_NS[-1]), 3),
                ],
                "description": (
                    "How long the single drive pulse lasted. One of the two swept "
                    "variables: 42 values from ~5 ns to ~214 ns, set on the generator "
                    "as 50 to 2100 clock ticks in steps of 50. CAVEAT: these are "
                    "converted values that cannot be stored exactly, so use "
                    "np.isclose() rather than == when filtering."
                ),
            },
            {
                "name": "frequency_MHz",
                "dtype": "float32",
                "unit": "MHz",
                "role": "coordinate (swept input)",
                "measured": False,
                "varies_within_file": True,
                "n_unique": N_FREQUENCIES,
                "range": [int(FREQUENCY_LIST_MHZ[0]), int(FREQUENCY_LIST_MHZ[-1])],
                "description": (
                    "Drive frequency — the other swept variable. 500 values from 4100 "
                    "to 4599 MHz in 1 MHz steps. Each frequency gets its own "
                    "single-pulse ring-down trace. Whole numbers, so == filtering is "
                    "exact and safe."
                ),
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
                    "30000 a.u. drive amplitude."
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

    Done in chunks rather than all at once because converting 21 million rows to
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
    output_dir = os.path.join(output_dir, "experiment_2")
    os.makedirs(output_dir, exist_ok=True)
    pkl_path = os.path.join(output_dir, "experiment_2_dataset_long.pkl")
    csv_path = os.path.join(output_dir, "experiment_2_dataset_long.csv")

    n_total_rows = N_PULSE_WIDTHS * N_FREQUENCIES * N_TIME_SAMPLES  # 21,000,000

    print(f"\nFormat          : long (one row per time sample)")
    print(f"Sample          : {SAMPLE_NAME} ({SAMPLE_MATERIAL})")
    print(f"Pulse widths    : {N_PULSE_WIDTHS}  ({PULSE_WIDTHS_NS[0]:.3f}-"
          f"{PULSE_WIDTHS_NS[-1]:.3f} ns, from {PULSE_WIDTH_TICKS_LIST[0]}-"
          f"{PULSE_WIDTH_TICKS_LIST[-1]} ticks)")
    print(f"Frequencies     : {N_FREQUENCIES}  ({FREQUENCY_LIST_MHZ[0]}-"
          f"{FREQUENCY_LIST_MHZ[-1]} MHz, step 1)")
    print(f"Time samples    : {N_TIME_SAMPLES} per measurement")
    print(f"Total rows      : {N_PULSE_WIDTHS} x {N_FREQUENCIES} x "
          f"{N_TIME_SAMPLES} = {n_total_rows:,}")
    print(f"Columns         : {COLUMN_NAMES}")
    print(f"Memory needed   : ~{n_total_rows*len(COLUMN_NAMES)*4/1024**3:.2f} GB "
          f"for the array alone\n")

    # Make the whole output table up front and fill it in, rather than growing it
    # row by row (which would be far slower). float32 = 4 bytes per number, so
    # 21,000,000 rows x 5 columns ~= 400 MB held in memory.
    data_all = np.empty((n_total_rows, len(COLUMN_NAMES)), dtype=np.float32)

    # Tracks how many rows have been filled so far; every trace adds 1000.
    row_idx = 0
    n_files = 0

    # One file per pulse width. Within it, one trace per drive frequency.
    for ticks, pulse_width_ns in tqdm(
        list(zip(PULSE_WIDTH_TICKS_LIST, PULSE_WIDTHS_NS)), desc="Pulse widths"
    ):

        filename = npy_filename(ticks)
        filepath = os.path.join(data_dir, filename)

        if not os.path.exists(filepath):
            print(f"  WARNING: file not found -> {filename}  (skipping)")
            continue

        # One file holds a 3-D block of numbers, shape (2, 500, 1000):
        #   axis 0 -> 2      : the I channel and the Q channel
        #   axis 1 -> 500    : one entry per drive frequency
        #   axis 2 -> 1000   : one entry per instant in the ring-down
        IQ_matrix = np.load(filepath)  # shape (2, 500, 1000)

        # Guard against a file that is not what we expect — a wrong folder, a
        # truncated acquisition, or one of the DERIVED products that sit in the
        # same directory as the raw sweeps.
        if IQ_matrix.shape != (2, N_FREQUENCIES, N_TIME_SAMPLES):
            print(f"  WARNING: {filename} has shape {IQ_matrix.shape}, expected "
                  f"(2, {N_FREQUENCIES}, {N_TIME_SAMPLES}) — skipping")
            continue

        I_matrix = IQ_matrix[0]  # shape (500, 1000) — I for every frequency
        Q_matrix = IQ_matrix[1]  # shape (500, 1000) — Q for every frequency
        n_files += 1

        # Each frequency gives one 1000-point ring-down trace, which becomes
        # 1000 consecutive rows of the output table.
        for freq_idx, freq_mhz in enumerate(FREQUENCY_LIST_MHZ):

            end_idx = row_idx + N_TIME_SAMPLES

            # Columns 0-1 are the settings in force for this trace. They do not
            # change during the 1000 instants, so the same value is written down
            # the whole block. That repetition is deliberate: it makes every row
            # independently filterable.
            data_all[row_idx:end_idx, 0] = pulse_width_ns
            data_all[row_idx:end_idx, 1] = freq_mhz

            # Columns 2-4 do change instant to instant: the clock, and the two
            # measured channels. All 1000 samples are copied — never trimmed.
            data_all[row_idx:end_idx, 2] = TIMESTAMPS_NS
            data_all[row_idx:end_idx, 3] = I_matrix[freq_idx]  # all 1000 samples
            data_all[row_idx:end_idx, 4] = Q_matrix[freq_idx]  # all 1000 samples

            row_idx += N_TIME_SAMPLES

        del IQ_matrix, I_matrix, Q_matrix

    data_final = data_all[:row_idx]

    # ── Save ──────────────────────────────────────────────────────────────────
    print(f"\nFiles ingested  : {n_files} of {N_PULSE_WIDTHS}")
    print(f"Saving to {pkl_path} ...")

    payload = {
        "data": data_final,
        "columns": COLUMN_NAMES,
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

    # Did every file arrive? 42 files x 500 frequencies x 1000 instants should
    # give exactly 21,000,000 rows. A short count means a file was missing.
    if row_idx != n_total_rows:
        errors.append(
            f"  [FAIL] Row count: got {row_idx:,}, expected {n_total_rows:,} "
            f"— likely caused by missing .npy files"
        )
    else:
        print(f"  [PASS] Row count: {row_idx:,} = {N_PULSE_WIDTHS} pulse widths x "
              f"{N_FREQUENCIES} frequencies x {N_TIME_SAMPLES} samples")

    n_nan = int(np.sum(np.isnan(data_final)))
    n_inf = int(np.sum(np.isinf(data_final)))
    if n_nan > 0 or n_inf > 0:
        errors.append(f"  [FAIL] Data contains {n_nan} NaN and {n_inf} Inf values")
    else:
        print(f"  [PASS] No NaN or Inf values in dataset")

    # Are the measured numbers the right size? What comes BACK from the chip is a
    # few thousand a.u.; the 30000 figure is how hard we SHOUT, not what we hear.
    # Seeing 30000-sized numbers here would mean the drive and the response had
    # been confused somewhere.
    I_col = data_final[:, 3]
    Q_col = data_final[:, 4]
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
        (0, "pulse widths", N_PULSE_WIDTHS),
        (1, "frequencies", N_FREQUENCIES),
        (2, "time samples", N_TIME_SAMPLES),
    ]:
        got = len(np.unique(data_final[:, col_idx]))
        if got != expected:
            errors.append(f"  [FAIL] Expected {expected} unique {name}, got {got}")
        else:
            print(f"  [PASS] Unique {name}: {got}")

    # frequency_MHz holds whole numbers, which ARE stored exactly, so equality
    # filtering on it is safe at any precision. (pulse_width_ns is not — see the
    # filtering caveat in the module docstring.)
    f64 = data_final[:, 1].astype(np.float64)
    n_at = int((f64 == 4254).sum())
    if n_at == 0:
        errors.append("  [FAIL] frequency_MHz == 4254 matches no rows after upcast")
    else:
        print(f"  [PASS] frequency_MHz exact under float64 upcast "
              f"({n_at:,} rows at 4254 MHz)")

    ts_col = data_final[:, 2]
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
    same = np.array_equal(reloaded["data"], data_final)
    cols_ok = list(reloaded["columns"]) == COLUMN_NAMES
    del reloaded
    if not same:
        errors.append(f"  [FAIL] Pickle round-trip: reloaded data differs from memory")
    elif not cols_ok:
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
        print(f"  (expect roughly {n_total_rows*55/1024**3:.1f} GB and a few minutes)")
        write_csv(data_final, COLUMN_NAMES, csv_path)
        print(f"  CSV         : {csv_path}  "
              f"({os.path.getsize(csv_path)/1024**2:.1f} MB, {row_idx:,} rows)")


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND LINE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    _script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Build the Experiment 2 raw IQ dataset (long format) as a "
        "pickle and a CSV."
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="Folder containing the {ticks}_IQ_avg_matrix_0.npy files (matrix_npy)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=_script_dir,
        help="Where to write experiment_2/ (default: next to this script)",
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
