"""
experiment_13_dataset_creation.py
=================================
Converts the 2 raw broadband .npy files from Experiment 13
(BCTDS before and after a thermal cycle) into a long-format dataset:
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
    Only ONE pulse here — no interference, no phase sweep. Instead the pulse's
    FREQUENCY is stepped across the band (3000 settings, 1 MHz apart), which
    asks the chip "which notes do you ring at?".

    The point of THIS experiment is what happens when you warm the chip all the
    way to room temperature and cool it back down — a "thermal cycle". The same
    measurement is taken twice, three days apart, with a warm-up in between and
    nothing else touched. The defects are not permanently fixed in place: warming
    reshuffles them, so the chip rings at a noticeably different set of notes the
    second time. The two cooldowns are what this dataset compares.

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

5 columns, one row per time sample:

    col 0 — cooldown_index   which cooldown (1 = before, 2 = after thermal cycle)
    col 1 — frequency_MHz    drive frequency in MHz — the swept variable
    col 2 — timestamp_ns     time of this sample within the trace (nanoseconds)
    col 3 — I                in-phase channel value (ADC units)
    col 4 — Q                quadrature channel value (ADC units)

Only what varies gets a column. A single chip was used and both cooldowns sat at
the same ~22 mK, so those would be one value repeated on every row; they are
recorded in metadata.json instead.

Total rows: 2 cooldowns x 3000 frequencies x 1000 time samples
          = 6,000,000

Timestamp spacing: 1 / 552.96 MHz ~ 1.8084 ns per sample

RECORDING ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Files are loaded in the order defined by generate_fig_13.py:

    cooldown_index (1 = "shipley", 2 = "shipley_2nd")
      -> frequency_MHz (2000, 2001, ..., 4999  -- 3000 values, axis 1 of the .npy)
           -> timestamp_ns (0 ... ~1806.6 ns -- 1000 values, axis 2 of the .npy)

Each .npy file is named:
    shipley_IQ_avg_matrix.npy       (cooldown 1, before thermal cycling)
    shipley_2nd_IQ_avg_matrix.npy   (cooldown 2, after thermal cycling)

and has shape (2, 3000, 1000):
    axis 0 -> [I_matrix, Q_matrix]
    axis 1 -> 3000 drive frequencies (np.arange(2000, 5000, 1), in MHz)
    axis 2 -> 1000 time samples (at 552.96 MHz ADC clock)

These filenames are far less informative than the other experiments' — they
carry only the sample and the cooldown. The frequency axis comes from
generate_fig_13.py; the temperature is not recorded in the raw files at all.

PULSE WIDTH IS NOT RECORDED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unlike every other experiment in this series, neither the filename nor
generate_fig_13.py states the pulse duration, so this dataset has NO
pulse_width_ns column. The pulse envelope measured from the data spans raw
samples 36 -> 58 (65.1 -> 104.9 ns), which is wider than the 308-tick /
31.33 ns pulse used elsewhere; the 308-tick value is therefore NOT assumed
here.

OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    13_thermal_cycle/experiment_13/experiment_13_dataset_long.pkl
    13_thermal_cycle/experiment_13/experiment_13_dataset_long.csv
    13_thermal_cycle/metadata.json
    13_thermal_cycle/column_info.json

To load in Python:

    import pickle
    import pandas as pd

    with open("experiment_13_dataset_long.pkl", "rb") as fh:
        payload = pickle.load(fh)
    df = pd.DataFrame(payload["data"], columns=payload["columns"])

    # one ring-down trace (1000 rows):
    mask  = (df["cooldown_index"] == 1) & (df["frequency_MHz"] == 3657)
    trace = df[mask].sort_values("timestamp_ns")

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    python experiment_13_dataset_creation.py --data_dir /path/to/matrix_npy_save_folder

    Optional arguments:
        --output_dir  where to write experiment_13/ (default: next to this script)
        --no_csv      skip the CSV (pickle only)
"""

import os
import json
import pickle
import argparse
import numpy as np
from tqdm import tqdm

# ─────────────────────────────────────────────────────────────────────────────
# RECORDING ORDER — taken directly from generate_fig_13.py
# ─────────────────────────────────────────────────────────────────────────────

SAMPLES = [("Shipley", 0)]
SAMPLE_MATERIAL = {
    "Shipley": "Sapphire substrate with spin-coated Shipley 1813 photoresist"
}

# THE VARIABLE OF THIS EXPERIMENT: the same chip, measured twice, with a warm-up
# to room temperature and back in between. Everything else was left untouched —
# the fridge was never opened — so any difference between the two is the thermal
# cycle reshuffling the defects.
COOLDOWNS = [
    (1, "shipley", "before thermal cycling (cooldown 1)"),
    (2, "shipley_2nd", "after thermal cycling to room temperature (cooldown 2)"),
]

# THE SWEPT AXIS: which note the chip is struck at. 3000 settings, 1 MHz apart
# — a much finer comb than Experiment 11's 5 MHz steps, to resolve small shifts.
FREQ_START_MHZ = 2000
FREQ_STOP_MHZ = 5000
FREQ_STEP_MHZ = 1
FREQUENCY_LIST_MHZ = np.arange(FREQ_START_MHZ, FREQ_STOP_MHZ, FREQ_STEP_MHZ)  # 3000

ADC_CLOCK_MHZ = 552.96  # digitiser's clock -> 1 sample ~= 1.8084 ns
N_TIME_SAMPLES = 1000   # how many instants are recorded per ring-down
N_FREQUENCIES = len(FREQUENCY_LIST_MHZ)  # 3000

# The clock along each recorded trace. The digitiser samples every ~1.8 ns, so
# 1000 samples covers ~1.81 microseconds. Identical for every measurement, so
# it is built once and reused.
TIMESTAMPS_NS = (np.arange(N_TIME_SAMPLES) / ADC_CLOCK_MHZ) * 1000

# Approximate. Not recorded anywhere in the raw files.
TEMPERATURE_MK = 22

# Pulse envelope measured from the data (threshold at 30% of peak), identical in
# both cooldowns.
PULSE_ENVELOPE_SAMPLES = [36, 58]
PULSE_ENVELOPE_NS = [
    round(36 / ADC_CLOCK_MHZ * 1000, 1),
    round(58 / ADC_CLOCK_MHZ * 1000, 1),
]

# Only what actually varies gets a column. The chip and the fridge temperature
# were the same for both cooldowns, so they would be one repeated value on every
# row — they live in metadata.json instead.
COLUMN_NAMES = [
    "cooldown_index",
    "frequency_MHz",
    "timestamp_ns",
    "I",
    "Q",
]

# Column name -> position, so the code below never hard-codes an index.
COL = {name: i for i, name in enumerate(COLUMN_NAMES)}

SAMPLE_NAMES = [name for name, _ in SAMPLES]
PICKLE_PROTOCOL = 4


def npy_filename(prefix: str) -> str:
    return f"{prefix}_IQ_avg_matrix.npy"


# ─────────────────────────────────────────────────────────────────────────────
# METADATA
# ─────────────────────────────────────────────────────────────────────────────


def build_metadata() -> dict:
    return {
        "experiment_id": "experiment_13",
        "title": "Thermal Cycle (BCTDS Before and After)",
        "data_type": "raw",
        "description": (
            "Raw BCTDS homodyne I/Q measurements of single-pulse broadband "
            "spectroscopy on a sapphire sample coated with Shipley 1813 "
            "photoresist, taken across two separate cooldowns three days apart "
            "without breaking the dilution fridge vacuum or changing the "
            "measurement setup. The drive frequency is swept from 2000 to 4999 MHz "
            "in 1 MHz steps. Comparing the two cooldowns shows how thermal cycling "
            "to room temperature repopulates the TLS defects, changing both the "
            "transient amplitude spectra and the phase V features. Only the "
            "in-phase (I) and quadrature (Q) signals are measured; magnitude, "
            "phase, and FFT spectra are computable from them and are not stored."
        ),
        "samples": [
            {"sample_id": sid, "name": name, "material": SAMPLE_MATERIAL[name]}
            for name, sid in SAMPLES
        ],
        "cooldowns": [
            {"cooldown_index": idx, "file_prefix": prefix, "description": desc}
            for idx, prefix, desc in COOLDOWNS
        ],
        "apparatus": {
            "refrigerator": "Bluefors LD400 dilution refrigerator",
            "temperature": f"~{TEMPERATURE_MK} mK",
            "temperature_note": "Approximate (~22 mK), and identical for both "
            "cooldowns. Not recorded in the raw files.",
            "waveguide": "WR-229 rectangular waveguide, 3-6 GHz passband, TE10 mode",
            "detection": "homodyne (in-phase I, quadrature Q)",
            "electronics": "RFSoC",
        },
        "clocks": {"adc_readout_clock_MHz": ADC_CLOCK_MHZ},
        "timing": {
            "time_axis": {
                "hardware_unit": "ADC samples",
                "clock_MHz": ADC_CLOCK_MHZ,
                "one_sample_ns": 1000 / ADC_CLOCK_MHZ,
                "formula": "timestamp_ns = sample_index / 552.96 * 1000",
                "n_samples": N_TIME_SAMPLES,
                "resulting_range_ns": [0.0, float(TIMESTAMPS_NS[-1])],
            }
        },
        "pulse_geometry": {
            "frame": "raw-trace samples/ns, the same frame as timestamp_ns",
            "num_pulses": 1,
            "envelope_samples": PULSE_ENVELOPE_SAMPLES,
            "envelope_ns": PULSE_ENVELOPE_NS,
            "identical_across_cooldowns": True,
            "source": (
                "Measured from the data (threshold at 30% of peak magnitude), NOT "
                "declared in generate_fig_13.py. Threshold-based edges overestimate "
                "the extent slightly. This is a single-pulse experiment: there is "
                "no inter-pulse spacing or phase sweep."
            ),
        },
        "sweep": {
            "sample": {"n": 1, "values": SAMPLE_NAMES},
            "cooldown": {"n": 2, "values": [1, 2]},
            "drive_frequency": {
                "n": N_FREQUENCIES,
                "unit": "MHz",
                "range": [int(FREQUENCY_LIST_MHZ[0]), int(FREQUENCY_LIST_MHZ[-1])],
                "step": FREQ_STEP_MHZ,
                "source": "generate_fig_13.py: np.arange(2000, 5000, 1)",
            },
            "time_samples_per_trace": N_TIME_SAMPLES,
        },
        "constant_drive_parameters": {
            "num_pulses": 1,
            "pulse_shape": "square",
            "pulse_width_ns": None,
            "pulse_width_note": (
                "NOT RECORDED. Neither the filename nor generate_fig_13.py states "
                "the pulse duration, so this dataset has no pulse_width_ns column. "
                "The measured envelope (~65 -> ~105 ns) is wider than the 31.33 ns "
                "(308-tick) pulse used in experiments 3, 4, 5, 11 and 12, so that "
                "value is not assumed here."
            ),
        },
    }


def build_column_info() -> dict:
    return {
        "dataset": "experiment_13_thermal_cycle",
        "format": "long (one row per time sample)",
        "n_rows": len(COOLDOWNS) * N_FREQUENCIES * N_TIME_SAMPLES,
        "n_columns": len(COLUMN_NAMES),
        "schema_rule": (
            "The filename holds the sample and the cooldown; the array axes hold "
            "the drive frequency (axis 1) and time (axis 2) together with the "
            "measured I/Q. Unlike the other experiments, the frequency axis is not "
            "stored in the file — it comes from generate_fig_13.py."
        ),
        "columns": [
            {
                "name": "cooldown_index",
                "dtype": "float32",
                "unit": "categorical index",
                "role": "coordinate (primary categorical variable)",
                "measured": False,
                "varies_within_file": False,
                "computed_from": "filename prefix: 'shipley' -> 1, 'shipley_2nd' -> 2",
                "values": {"1": "before thermal cycling", "2": "after thermal cycling"},
                "n_unique": 2,
                "description": "Which cooldown the measurement belongs to — the "
                "variable this experiment compares. The two cooldowns are three "
                "days apart, with a thermal cycle to room temperature in between "
                "and no vacuum break or setup change.",
            },
            {
                "name": "frequency_MHz",
                "dtype": "float32",
                "unit": "MHz",
                "role": "coordinate (primary swept input)",
                "measured": False,
                "varies_within_file": True,
                "computed_from": "generate_fig_13.py: np.arange(2000, 5000, 1); axis 1",
                "range": [int(FREQUENCY_LIST_MHZ[0]), int(FREQUENCY_LIST_MHZ[-1])],
                "n_unique": N_FREQUENCIES,
                "description": "Drive frequency, the primary swept variable: 3000 "
                "values from 2000 to 4999 MHz in 1 MHz steps. Each frequency gets "
                "its own single-pulse ring-down trace.",
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
                "description": "Time within the recorded trace, measured from t = 0 "
                "(start of the recorded window). The axis the ring-down physics "
                "lives on.",
            },
            {
                "name": "I",
                "dtype": "float32",
                "unit": "ADC arbitrary units",
                "role": "measured observable (raw)",
                "measured": True,
                "varies_within_file": True,
                "computed_from": "IQ_avg_matrix[0], loaded directly from the .npy",
                "description": "Raw in-phase homodyne signal, averaged over shots.",
            },
            {
                "name": "Q",
                "dtype": "float32",
                "unit": "ADC arbitrary units",
                "role": "measured observable (raw)",
                "measured": True,
                "varies_within_file": True,
                "computed_from": "IQ_avg_matrix[1], loaded directly from the .npy",
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
    output_dir = os.path.join(output_dir, "experiment_13")
    os.makedirs(output_dir, exist_ok=True)
    pkl_path = os.path.join(output_dir, "experiment_13_dataset_long.pkl")
    csv_path = os.path.join(output_dir, "experiment_13_dataset_long.csv")

    n_cooldowns = len(COOLDOWNS)
    n_total_rows = n_cooldowns * N_FREQUENCIES * N_TIME_SAMPLES  # 6,000,000

    print(f"\nFormat          : long (one row per time sample)")
    print(f"Sample          : {SAMPLE_NAMES[0]} (sapphire + Shipley 1813)")
    print(f"Cooldowns       : {n_cooldowns}  (1 = before, 2 = after thermal cycle)")
    print(f"Temperature     : ~{TEMPERATURE_MK} mK (nominal; not in the raw files)")
    print(f"Frequencies     : {N_FREQUENCIES}  ({FREQUENCY_LIST_MHZ[0]}-"
          f"{FREQUENCY_LIST_MHZ[-1]} MHz, step {FREQ_STEP_MHZ})")
    print(f"Time samples    : {N_TIME_SAMPLES} per measurement")
    print(f"Total rows      : {n_cooldowns} x {N_FREQUENCIES} x {N_TIME_SAMPLES} "
          f"= {n_total_rows:,}")
    print(f"Columns         : {COLUMN_NAMES}")
    print(f"Note            : single-pulse experiment; pulse width is not recorded\n")

    data_all = np.empty((n_total_rows, len(COLUMN_NAMES)), dtype=np.float32)
    row_idx = 0
    sample_id = SAMPLES[0][1]

    for cooldown_index, prefix, _desc in tqdm(COOLDOWNS, desc="Cooldowns"):

        filename = npy_filename(prefix)
        filepath = os.path.join(data_dir, filename)

        if not os.path.exists(filepath):
            print(f"  WARNING: file not found -> {filename}  (skipping)")
            continue

        IQ_matrix = np.load(filepath)  # expect (2, 3000, 1000)

        if IQ_matrix.shape != (2, N_FREQUENCIES, N_TIME_SAMPLES):
            print(f"  WARNING: {filename} has shape {IQ_matrix.shape}, expected "
                  f"(2, {N_FREQUENCIES}, {N_TIME_SAMPLES}) — skipping")
            continue

        I_matrix = IQ_matrix[0]  # (3000, 1000)
        Q_matrix = IQ_matrix[1]

        for freq_idx, freq_mhz in enumerate(FREQUENCY_LIST_MHZ):

            end_idx = row_idx + N_TIME_SAMPLES

            data_all[row_idx:end_idx, COL["cooldown_index"]] = cooldown_index
            data_all[row_idx:end_idx, COL["frequency_MHz"]] = freq_mhz
            data_all[row_idx:end_idx, COL["timestamp_ns"]] = TIMESTAMPS_NS
            data_all[row_idx:end_idx, COL["I"]] = I_matrix[freq_idx]  # all 1000
            data_all[row_idx:end_idx, COL["Q"]] = Q_matrix[freq_idx]  # all 1000

            row_idx += N_TIME_SAMPLES

    data_final = data_all[:row_idx]

    # ── Save ─────────────────────────────────────────────────────────────────
    print(f"\nSaving to {pkl_path} ...")

    payload = {
        "data": data_final,
        "columns": COLUMN_NAMES,
        "attrs": build_metadata(),
        "column_doc": build_column_info(),
    }
    save_pickle(payload, pkl_path)

    meta_path = os.path.join(script_dir, "metadata.json")
    cols_path = os.path.join(script_dir, "column_info.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(build_metadata(), fh, indent=2)
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
        print(f"  [PASS] Row count: {row_idx:,} = {n_cooldowns} cooldowns x "
              f"{N_FREQUENCIES} frequencies x {N_TIME_SAMPLES} samples")

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
        (COL["cooldown_index"], "cooldowns", n_cooldowns),
        (COL["frequency_MHz"], "frequencies", N_FREQUENCIES),
        (COL["timestamp_ns"], "time samples", N_TIME_SAMPLES),
    ]:
        got = len(np.unique(data_final[:, col_idx]))
        if got != expected:
            errors.append(f"  [FAIL] Expected {expected} unique {name}, got {got}")
        else:
            print(f"  [PASS] Unique {name}: {got}")

    # frequency_MHz must survive a float64 upcast (integers up to 2^24 are exact)
    f64 = data_final[:, COL["frequency_MHz"]].astype(np.float64)
    n_at = int((f64 == 3657).sum())
    if n_at == 0:
        errors.append("  [FAIL] frequency_MHz == 3657 matches no rows after upcast")
    else:
        print(f"  [PASS] frequency_MHz exact under float64 upcast "
              f"({n_at:,} rows at 3657 MHz)")

    fr = data_final[:, COL["frequency_MHz"]]
    print(f"  [INFO] frequency range: [{fr.min():.0f}, {fr.max():.0f}] MHz")

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
        description="Build the Experiment 13 raw IQ dataset (long format) as a pickle "
        "and a CSV."
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="Folder containing shipley_IQ_avg_matrix.npy and "
        "shipley_2nd_IQ_avg_matrix.npy (matrix_npy_save_folder)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=_script_dir,
        help="Where to write experiment_13/ (default: next to this script)",
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
