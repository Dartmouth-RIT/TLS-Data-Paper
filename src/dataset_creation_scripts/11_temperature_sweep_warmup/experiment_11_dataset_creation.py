"""
experiment_11_dataset_creation.py
=================================
Converts the 106 raw broadband .npz sweeps from Experiment 11
(temperature dependence of BCTDS during a fridge warm-up) into a long-format
dataset: one row per time sample, saved as a pickle and a CSV.

WHAT THIS PARTICULAR EXPERIMENT DOES
    Only ONE pulse here — no interference, no phase sweep. Instead the pulse's
    FREQUENCY is stepped across the whole 3-5 GHz band (401 settings), which
    asks the chip "which notes do you ring at?".

    That full sweep is then repeated 106 times back-to-back while the fridge is
    deliberately allowed to warm up, from 0.14 K to about 250 K over 17 hours.
    Each sweep takes ~9 minutes. The point is to watch the quantum behaviour
    disappear as things get hotter: near absolute zero the ringing is sharp and
    structured, and warming smears it away.

    Because the fridge is warming throughout, the sweep number doubles as a
    temperature axis — which is why the temperature is MEASURED here and stored
    alongside every reading, rather than being a fixed setting.

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

8 columns, one row per time sample:

    col 0 — rep_index        which sweep (0-105) — the PRIMARY variable
    col 1 — frequency_MHz    drive frequency in MHz — the swept axis
    col 2 — T_mxc_K          mixing-chamber temperature in KELVIN (may be NaN)
    col 3 — T_still_K        still-stage temperature in KELVIN
    col 4 — timestamp_ns     time of this sample within the trace (nanoseconds)
    col 5 — elapsed_s        wall-clock seconds since the warm-up started
    col 6 — I                in-phase channel value (ADC units)
    col 7 — Q                quadrature channel value (ADC units)

Total rows: 106 reps x 401 frequencies x 1000 time samples
          = 42,506,000

Timestamp spacing: 1 / 552.96 MHz ~ 1.8084 ns per sample

RECORDING ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Files are loaded in ascending rep index, which is chronological:

    rep_index (0, 1, 2, ..., 105)
      -> frequency_MHz (3000, 3005, ..., 5000  -- 401 values, axis 1 of the .npz)
           -> timestamp_ns (0 ... ~1806.6 ns -- 1000 values, axis 2 of the .npz)

Each .npz file is named:
    308_rep_{N}_ID_FM_Shipley_cont_HFSS_calib_20251008_174837_with_T.npz
       |     |       |                        |               |
       |     |       |                        |               +-- has thermometry
       |     |       |                        +------------------ run datetime
       |     |       +------------------------------------------- sample + calibration
       |     +--------------------------------------------------- sweep index
       +--------------------------------------------------------- pulse width (AWG ticks)

and contains:
    IQ_avg_matrix     (2, 401, 1000)   axis 0 -> [I, Q]
                                       axis 1 -> 401 drive frequencies
                                       axis 2 -> 1000 time samples
    pulse_freq_array  (401,)  int64    the frequency axis, IN THE FILE
    time_stamp_list   (401,)  datetime64[s]   wall clock per frequency point
    T_still           (401,)  float64  still-stage temperature, KELVIN
    T_mxc             (401,)  float64  mixing-chamber temperature, KELVIN


THIS PACKAGES THE RAW SWEEPS, NOT THE DERIVED COMPANION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The source folder has two directories:

    npz_data_base_with_T/   raw IQ + thermometry   <-- THIS DATASET
    processed_result_npz/   derived fits and FFTs

This dataset packages the RAW directory. The processed one holds derived
quantities — tau, the fitted ring-down lifetime, is a scipy curve_fit output,
not a measured value — so none of it is included here. All of it is computable
from the raw I/Q. See attrs.processed_companion.

NaN IS EXPECTED IN THIS DATASET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T_mxc_K contains 9,221,000 NaN values. The mixing-chamber thermometer stops
reading as the fridge warms; the first all-NaN sweep is rep 84. Every NaN falls
in reps 83-105; reps 0-82 are completely clean. I and Q are never NaN, and
this script checks that invariant rather than rejecting NaN outright.

OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    11_temperature_sweep_warmup/experiment_11/experiment_11_dataset_long.pkl
    11_temperature_sweep_warmup/experiment_11/experiment_11_dataset_long.csv
    11_temperature_sweep_warmup/metadata.json
    11_temperature_sweep_warmup/column_info.json

WARNING: this is by far the largest dataset in the series — 42.5 M rows, about
1.6 GB as a pickle and about 3.5 GB as a CSV. Building it needs roughly 3.5 GB
of free RAM. Use --no_csv to skip the CSV.

To load in Python:

    import pickle
    import pandas as pd

    with open("experiment_11_dataset_long.pkl", "rb") as fh:
        payload = pickle.load(fh)
    df = pd.DataFrame(payload["data"], columns=payload["columns"])

    # one ring-down trace (1000 rows):
    mask  = (df["rep_index"] == 0) & (df["frequency_MHz"] == 3400)
    trace = df[mask].sort_values("timestamp_ns")

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    python experiment_11_dataset_creation.py --data_dir /path/to/npz_data_base_with_T

    Optional arguments:
        --output_dir       where to write experiment_11/ (default: next to this script)
        --no_csv           skip the CSV (pickle only)
"""

import os
import gc
import re
import json
import glob
import pickle
import argparse
import numpy as np
from tqdm import tqdm


SAMPLES = [("FM_Shipley", 0)]
SAMPLE_MATERIAL = {
    "FM_Shipley": "Sapphire substrate with spin-coated Shipley 1813 photoresist"
}

# generate_fig_11.py: exp_ID = "FM_Shipley_cont_HFSS_calib_20251008_174837"
EXP_ID = "FM_Shipley_cont_HFSS_calib_20251008_174837"

# Each "rep" is one complete 3-5 GHz sweep, taking ~9 minutes. 106 of them run
# back-to-back while the fridge warms from 0.14 K to ~250 K, so the rep number
# is effectively a clock AND a thermometer.
ALL_REPS = list(range(0, 106))

# THE SWEPT AXIS: which note the chip is struck at. 401 settings from 3 to 5
# GHz, 5 MHz apart. Each one gets its own ring-down recording, so a single
# sweep answers "which notes does this chip ring at?".
# The .npz files store this axis inside them, so the script READS it and checks
# it against this rather than assuming it.
FREQ_START_MHZ = 3000
FREQ_STOP_MHZ = 5000
FREQ_STEP_MHZ = 5
EXPECTED_FREQ_MHZ = np.arange(FREQ_START_MHZ, FREQ_STOP_MHZ + 1, FREQ_STEP_MHZ)  # 401

# How long each pulse lasts. The generator counts in its own clock steps
# ("ticks"), so 308 ticks must be converted to nanoseconds to mean anything.
PULSE_WIDTH_TICKS = 308
AWG_CLOCK_MHZ = 9830.4  # pulse generator's clock -> 1 tick   ~= 0.1017 ns
ADC_CLOCK_MHZ = 552.96  # digitiser's clock       -> 1 sample ~= 1.8084 ns
N_TIME_SAMPLES = 1000   # how many instants are recorded per ring-down
N_FREQUENCIES = len(EXPECTED_FREQ_MHZ)  # 401

PULSE_WIDTH_NS = (PULSE_WIDTH_TICKS / AWG_CLOCK_MHZ) * 1000  # ~= 31.33 ns
# The clock along each recorded trace. The digitiser samples every ~1.8 ns, so
# 1000 samples covers ~1.81 microseconds. Identical for every measurement, so
# it is built once and reused.
TIMESTAMPS_NS = (np.arange(N_TIME_SAMPLES) / ADC_CLOCK_MHZ) * 1000

# Pulse envelope measured from the data (threshold at 30% of peak), rep 0.
PULSE_ENVELOPE_SAMPLES = [103, 121]
PULSE_ENVELOPE_NS = [
    round(103 / ADC_CLOCK_MHZ * 1000, 1),
    round(121 / ADC_CLOCK_MHZ * 1000, 1),
]


# Only what actually varies gets a column. A single chip was used and the pulse
# width never changed, so those would be one value repeated on every row — they
# live in metadata.json instead.
COLUMN_NAMES = [
    "rep_index",
    "frequency_MHz",
    "T_mxc_K",
    "T_still_K",
    "timestamp_ns",
    "elapsed_s",
    "I",
    "Q",
]

# Column name -> position, so the code below never hard-codes an index.
COL = {name: i for i, name in enumerate(COLUMN_NAMES)}

SAMPLE_NAMES = [name for name, _ in SAMPLES]
PICKLE_PROTOCOL = 4


def npz_filename(rep: int) -> str:
    return f"{PULSE_WIDTH_TICKS}_rep_{rep}_ID_{EXP_ID}_with_T.npz"


def discover_reps(data_dir: str) -> list:
    """Find the rep indices actually present on disk, in ascending order."""
    found = []
    for path in glob.glob(os.path.join(data_dir, f"{PULSE_WIDTH_TICKS}_rep_*.npz")):
        m = re.search(r"_rep_(\d+)_", os.path.basename(path))
        if m:
            found.append(int(m.group(1)))
    return sorted(found)


# ─────────────────────────────────────────────────────────────────────────────
# METADATA
# ─────────────────────────────────────────────────────────────────────────────


def build_metadata(reps: list, run_start_iso: str = None) -> dict:
    return {
        "experiment_id": "experiment_11",
        "title": "Temperature Dependence of BCTDS During Warm-Up",
        "data_type": "raw",
        "description": (
            "Raw BCTDS homodyne I/Q measurements of single-pulse broadband "
            "spectroscopy on a sapphire sample coated with Shipley 1813 "
            "photoresist, swept 3000-5000 MHz and repeated back-to-back during a "
            "standard Bluefors warm-up. Each sweep takes about 9 minutes and the "
            "fridge climbs from ~0.14 K to ~250 K over the run, so the sweep index "
            "doubles as a temperature axis. Sharp ring-downs and collapse-and-"
            "revival patterns near base temperature wash out as the sample warms. "
            "Both stage temperatures are measured once per frequency point and are "
            "included as columns. Only the in-phase (I) and quadrature (Q) signals "
            "are measured; magnitude, phase, FFT spectra and fitted lifetimes are "
            "computable from them and are not stored."
        ),
        "samples": [
            {"sample_id": sid, "name": name, "material": SAMPLE_MATERIAL[name]}
            for name, sid in SAMPLES
        ],
        "apparatus": {
            "refrigerator": "Bluefors LD400 dilution refrigerator",
            "temperature": "swept by warming from base to ~250 K; measured, not set",
            "waveguide": "WR-229 rectangular waveguide, 3-6 GHz passband, TE10 mode",
            "detection": "homodyne (in-phase I, quadrature Q)",
            "electronics": "RFSoC",
            "calibration": "HFSS-calibrated drive amplitude, flat across the band "
            "('HFSS_calib' in the run ID).",
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
            "sweep_duration": "about 9 minutes per rep (401 frequency points)",
        },
        "pulse_geometry": {
            "frame": "raw-trace samples/ns, the same frame as timestamp_ns",
            "num_pulses": 1,
            "envelope_samples": PULSE_ENVELOPE_SAMPLES,
            "envelope_ns": PULSE_ENVELOPE_NS,
            "source": (
                "Measured from the data (threshold at 30% of peak magnitude), rep "
                "0. generate_fig_11.py declares no pulse position. Threshold-based "
                "edges overestimate the extent slightly; the implied width (~32 ns) "
                "is consistent with the 308-tick / 31.33 ns pulse in the filename. "
                "This is a single-pulse experiment: there is no inter-pulse spacing."
            ),
        },
        "sweep": {
            "sample": {"n": 1, "values": SAMPLE_NAMES},
            "rep": {
                "n": len(reps),
                "range": [min(reps), max(reps)] if reps else None,
                "note": "The primary variable. Sweeps are back-to-back during a "
                "warm-up, so rep index is monotonic in both time and temperature.",
            },
            "drive_frequency": {
                "n": N_FREQUENCIES,
                "unit": "MHz",
                "range": [FREQ_START_MHZ, FREQ_STOP_MHZ],
                "step": FREQ_STEP_MHZ,
                "source": "pulse_freq_array, stored in each .npz",
                "note": "The 3 GHz and 5 GHz sweep limits correspond to k_B T = h f "
                "temperatures of 144 mK and 240 mK.",
            },
            "time_samples_per_trace": N_TIME_SAMPLES,
        },
        "constant_drive_parameters": {
            "pulse_width_ns": PULSE_WIDTH_NS,
            "pulse_width_ticks": PULSE_WIDTH_TICKS,
            "num_pulses": 1,
            "pulse_shape": "square",
            "pulse_amplitude_au": None,
            "amplitude_note": "The drive amplitude is not stated for this figure "
            "and is absent from the filenames and the .npz contents. It is "
            "HFSS-calibrated to be flat across the band.",
        },
        "thermometry": {
            "T_mxc_K": "Mixing-chamber plate temperature, kelvin, one reading per "
            "frequency point.",
            "T_still_K": "Still-stage temperature, kelvin, one reading per "
            "frequency point.",
            "sample_vs_plate": (
                "The actual sample temperature is expected to be LOWER than the "
                "plate reading, because of the relatively low "
                "thermal conductivity between the baseplate and the insulating "
                "sapphire samples. T_mxc_K is the plate, not the sample."
            ),
            "nan_policy": (
                "T_mxc_K contains 9,221 NaN values: the mixing-chamber thermometer "
                "stops reading as the fridge warms, and the first all-NaN sweep is "
                "rep 84. I and Q are never NaN. NaN here means 'not measured', not "
                "'bad data'."
            ),
        },
        "processed_companion": {
            "directory": "processed_result_npz/",
            "note": (
                "The source folder contains a second directory of DERIVED results, "
                "and generate_fig_11.py reads that one rather than the raw sweeps "
                "packaged here. It holds, per rep: mag_log_matrix (401, 910), "
                "tau_us_array (401,), xc_array, average_transmission, "
                "phase_TP_fft_matrix (2001, 276), V_fit_avg_phase_TP_fft_matricies, "
                "and interpolated axes. Those are derived quantities — tau, for "
                "instance, is a scipy curve_fit output, not a measured value — so "
                "none of them are in this dataset, which packages the raw sweeps "
                "only. Everything there is computable from the raw I/Q here."
            ),
        },
        "acquisition": {
            "run_id": EXP_ID,
            "run_start_utc": run_start_iso,
            "elapsed_s_note": (
                "elapsed_s is wall-clock seconds since run_start_utc (the first "
                "timestamp of rep 0), taken from the time_stamp_list array inside "
                "each .npz, one entry per frequency point. The full run spans about "
                "17.1 hours; reps 0-50 span about 7.7 hours. Stored as elapsed "
                "seconds rather than an absolute epoch because float32 cannot "
                "represent Unix timestamps to better than ~128 s; elapsed integer "
                "seconds up to 16.7 M are exact."
            ),
        },
    }


def build_column_info(reps: list) -> dict:
    return {
        "dataset": "experiment_11_temperature_sweep_warmup",
        "format": "long (one row per time sample)",
        "n_rows": len(reps) * N_FREQUENCIES * N_TIME_SAMPLES,
        "n_columns": len(COLUMN_NAMES),
        "schema_rule": (
            "The filename holds the sample, the pulse width and the sweep index; "
            "the array axes hold the drive frequency (axis 1) and time (axis 2) "
            "together with the measured I/Q. Unlike every other experiment in this "
            "series, the thermometry is also measured per frequency point and "
            "stored in the file, so T_mxc_K and T_still_K are per-row measurements "
            "rather than metadata."
        ),
        "columns": [
            {
                "name": "rep_index",
                "dtype": "float32",
                "unit": "index",
                "role": "coordinate (primary variable)",
                "measured": False,
                "varies_within_file": False,
                "computed_from": "filename field 'rep_N'",
                "range": [min(reps), max(reps)] if reps else None,
                "n_unique": len(reps),
                "description": "Which back-to-back sweep this row belongs to. The "
                "primary variable of Experiment 11: because the sweeps run continuously "
                "during a warm-up, rep index is monotonic in both wall-clock time "
                "and temperature.",
            },
            {
                "name": "frequency_MHz",
                "dtype": "float32",
                "unit": "MHz",
                "role": "coordinate (swept axis)",
                "measured": False,
                "varies_within_file": True,
                "computed_from": "pulse_freq_array, stored in each .npz; axis 1",
                "range": [FREQ_START_MHZ, FREQ_STOP_MHZ],
                "n_unique": N_FREQUENCIES,
                "description": "Drive frequency: 401 values from 3000 to 5000 MHz "
                "in 5 MHz steps. Each frequency gets its own single-pulse ring-down "
                "trace. Not in the filename, because frequency is the swept axis.",
            },
            {
                "name": "T_mxc_K",
                "dtype": "float32",
                "unit": "K",
                "role": "measured observable (thermometry)",
                "measured": True,
                "varies_within_file": True,
                "computed_from": "T_mxc, stored in each .npz; one value per "
                "frequency point",
                "may_be_nan": True,
                "description": "Mixing-chamber plate temperature in KELVIN "
                "(not millikelvin), measured once per frequency point. Averaging "
                "it over a rep gives that sweep's temperature (rep 0 -> 0.1416 K, "
                "rep 45 -> 88.2431 K). CONTAINS NaN: the thermometer stops reading "
                "as the fridge warms (9,221,000 rows, in reps 83-105). NaN means "
                "'not measured'. The actual sample is expected to be colder than "
                "this plate reading.",
            },
            {
                "name": "T_still_K",
                "dtype": "float32",
                "unit": "K",
                "role": "measured observable (thermometry)",
                "measured": True,
                "varies_within_file": True,
                "computed_from": "T_still, stored in each .npz; one value per "
                "frequency point",
                "may_be_nan": True,
                "description": "Still-stage temperature in KELVIN, measured once "
                "per frequency point. Continues to read at high temperature where "
                "T_mxc_K drops out.",
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
                "description": "Time within the recorded trace — the fast axis, on "
                "which the ring-down physics lives. Not to be confused with "
                "elapsed_s, which is the slow wall-clock axis of the warm-up.",
            },
            {
                "name": "elapsed_s",
                "dtype": "float32",
                "unit": "s",
                "role": "acquisition metadata",
                "measured": False,
                "varies_within_file": True,
                "computed_from": "time_stamp_list in each .npz, minus the run start",
                "description": "Wall-clock seconds since the warm-up started, "
                "recorded once per frequency point. The slow axis: the full run "
                "spans ~17.1 h and reps 0-50 span ~7.7 h. Pairs with T_mxc_K to "
                "track the fridge temperature against wall-clock time.",
            },
            {
                "name": "I",
                "dtype": "float32",
                "unit": "ADC arbitrary units",
                "role": "measured observable (raw)",
                "measured": True,
                "varies_within_file": True,
                "computed_from": "IQ_avg_matrix[0], loaded directly from the .npz",
                "description": "Raw in-phase homodyne signal, averaged over shots. "
                "Never NaN.",
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
                "shots. Never NaN. Combined with I to compute magnitude and phase.",
            },
        ],
        "computable_not_stored": {
            "magnitude": "sqrt(I^2 + Q^2)  ==  abs(I + 1j*Q)",
            "phase": "atan2(Q, I)  ==  angle(I + 1j*Q)",
            "log_amplitude_spectrum": "log10(abs(I + 1j*Q) + 0.01)",
            "tau_us": "fitted ring-down lifetime — an exponential curve_fit over "
            "the post-pulse window, per frequency. It "
            "lives in the processed_result_npz companion directory, not here.",
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


def build_dataset(
    data_dir: str,
    output_dir: str,
    write_csv_file: bool = True,
):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(output_dir, "experiment_11")
    os.makedirs(output_dir, exist_ok=True)
    pkl_path = os.path.join(output_dir, "experiment_11_dataset_long.pkl")
    csv_path = os.path.join(output_dir, "experiment_11_dataset_long.csv")

    reps = discover_reps(data_dir)
    if not reps:
        raise FileNotFoundError(
            f"No Experiment 11 .npz files found in {data_dir}\n"
            f"Expected e.g. {npz_filename(0)}"
        )

    n_reps = len(reps)
    n_total_rows = n_reps * N_FREQUENCIES * N_TIME_SAMPLES

    print(f"\nFormat          : long (one row per time sample)")
    print(f"Sample          : {SAMPLE_NAMES[0]} (sapphire + Shipley 1813)")
    print(f"Reps found      : {n_reps}  ({min(reps)}-{max(reps)})")
    print(f"Frequencies     : {N_FREQUENCIES}  ({FREQ_START_MHZ}-{FREQ_STOP_MHZ} MHz, "
          f"step {FREQ_STEP_MHZ})")
    print(f"Time samples    : {N_TIME_SAMPLES} per measurement")
    print(f"Total rows      : {n_reps} x {N_FREQUENCIES} x {N_TIME_SAMPLES} "
          f"= {n_total_rows:,}")
    print(f"Columns         : {COLUMN_NAMES}")
    print(f"Memory needed   : ~{n_total_rows*len(COLUMN_NAMES)*4/1024**3:.2f} GB "
          f"for the array alone")
    print(f"Note            : single-pulse experiment; T_mxc_K may legitimately "
          f"be NaN\n")

    # ── Pass 1: find the run start, so elapsed_s is relative to it ───────────
    run_start = None
    for rep in reps:
        path = os.path.join(data_dir, npz_filename(rep))
        if not os.path.exists(path):
            continue
        with np.load(path, allow_pickle=True) as z:
            t0 = z["time_stamp_list"][0]
        run_start = t0 if run_start is None else min(run_start, t0)
    print(f"Run start (from time_stamp_list): {run_start}\n")

    # ── Pass 2: build ────────────────────────────────────────────────────────
    data_all = np.empty((n_total_rows, len(COLUMN_NAMES)), dtype=np.float32)
    row_idx = 0
    sample_id = SAMPLES[0][1]
    n_files = 0

    for rep in tqdm(reps, desc="Reps"):

        filename = npz_filename(rep)
        filepath = os.path.join(data_dir, filename)

        if not os.path.exists(filepath):
            print(f"  WARNING: file not found -> {filename}  (skipping)")
            continue

        with np.load(filepath, allow_pickle=True) as z:
            IQ_matrix = z["IQ_avg_matrix"]
            freq_array = z["pulse_freq_array"]
            time_stamps = z["time_stamp_list"]
            # The fridge has several cooling stages, each with its own
            # thermometer. Two are recorded here, in KELVIN, once per
            # frequency point:
            #   T_mxc   the mixing chamber — the coldest stage, where the
            #           chip is mounted. This is the temperature that matters.
            #   T_still the "still" — a warmer stage higher up the fridge.
            # T_mxc can be NaN ("not measured"): its thermometer stops
            # reading once the fridge warms past its range. That is expected,
            # not corruption, so the NaNs are kept rather than patched.
            T_still = z["T_still"]
            T_mxc = z["T_mxc"]

        if IQ_matrix.shape != (2, N_FREQUENCIES, N_TIME_SAMPLES):
            print(f"  WARNING: {filename} has shape {IQ_matrix.shape}, expected "
                  f"(2, {N_FREQUENCIES}, {N_TIME_SAMPLES}) — skipping")
            continue

        # The frequency axis is in the file; verify rather than assume.
        if not np.array_equal(freq_array, EXPECTED_FREQ_MHZ):
            print(f"  WARNING: {filename} pulse_freq_array does not match "
                  f"np.arange(3000, 5001, 5) — using the file's own axis")

        elapsed = (time_stamps - run_start).astype("timedelta64[s]").astype(np.float64)

        I_matrix = IQ_matrix[0]  # (401, 1000)
        Q_matrix = IQ_matrix[1]
        n_files += 1

        for freq_idx, freq_mhz in enumerate(freq_array):

            end_idx = row_idx + N_TIME_SAMPLES

            data_all[row_idx:end_idx, COL["rep_index"]] = rep
            data_all[row_idx:end_idx, COL["frequency_MHz"]] = freq_mhz
            data_all[row_idx:end_idx, COL["T_mxc_K"]] = T_mxc[freq_idx]  # may be NaN
            data_all[row_idx:end_idx, COL["T_still_K"]] = T_still[freq_idx]
            data_all[row_idx:end_idx, COL["timestamp_ns"]] = TIMESTAMPS_NS
            data_all[row_idx:end_idx, COL["elapsed_s"]] = elapsed[freq_idx]
            data_all[row_idx:end_idx, COL["I"]] = I_matrix[freq_idx]  # all 1000
            data_all[row_idx:end_idx, COL["Q"]] = Q_matrix[freq_idx]  # all 1000

            row_idx += N_TIME_SAMPLES

        del IQ_matrix, I_matrix, Q_matrix

    data_final = data_all[:row_idx]

    # ── Save ─────────────────────────────────────────────────────────────────
    run_start_iso = str(run_start)
    print(f"\nFiles ingested  : {n_files} of {n_reps}")
    print(f"Saving to {pkl_path} ...")

    payload = {
        "data": data_final,
        "columns": COLUMN_NAMES,
        "attrs": build_metadata(reps, run_start_iso),
        "column_doc": build_column_info(reps),
    }
    save_pickle(payload, pkl_path)

    meta_path = os.path.join(script_dir, "metadata.json")
    cols_path = os.path.join(script_dir, "column_info.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(build_metadata(reps, run_start_iso), fh, indent=2)
    with open(cols_path, "w", encoding="utf-8") as fh:
        json.dump(build_column_info(reps), fh, indent=2)

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
        print(f"  [PASS] Row count: {row_idx:,} = {n_reps} reps x {N_FREQUENCIES} "
              f"frequencies x {N_TIME_SAMPLES} samples")

    # I and Q must NEVER be NaN, even though the thermometry may be.
    n_nan_iq = int(np.isnan(data_final[:, [COL["I"], COL["Q"]]]).sum())
    if n_nan_iq:
        errors.append(f"  [FAIL] I/Q contain {n_nan_iq} NaN values")
    else:
        print(f"  [PASS] No NaN in I/Q")

    # NaN in T_mxc_K is expected: the thermometer drops out as the fridge warms.
    # Report where, rather than treating it as an error.
    t_mxc = data_final[:, COL["T_mxc_K"]]
    rep_col = data_final[:, COL["rep_index"]]
    n_nan_t = int(np.isnan(t_mxc).sum())
    nan_reps = np.unique(rep_col[np.isnan(t_mxc)]).astype(int).tolist()
    print(f"  [INFO] T_mxc_K NaN: {n_nan_t:,} rows "
          f"({n_nan_t/len(data_final)*100:.1f}%), in reps "
          f"{min(nan_reps) if nan_reps else '-'}-"
          f"{max(nan_reps) if nan_reps else '-'}")

    I_min, I_max = float(data_final[:, COL["I"]].min()), float(data_final[:, COL["I"]].max())
    Q_min, Q_max = float(data_final[:, COL["Q"]].min()), float(data_final[:, COL["Q"]].max())
    print(f"  [INFO] I range: [{I_min:.1f}, {I_max:.1f}]   "
          f"Q range: [{Q_min:.1f}, {Q_max:.1f}]")

    for col_idx, name, expected in [
        (COL["rep_index"], "reps", n_reps),
        (COL["frequency_MHz"], "frequencies", N_FREQUENCIES),
        (COL["timestamp_ns"], "time samples", N_TIME_SAMPLES),
    ]:
        got = len(np.unique(data_final[:, col_idx]))
        if got != expected:
            errors.append(f"  [FAIL] Expected {expected} unique {name}, got {got}")
        else:
            print(f"  [PASS] Unique {name}: {got}")

    f64 = data_final[:, COL["frequency_MHz"]].astype(np.float64)
    n_at = int((f64 == 3400).sum())
    if n_at == 0:
        errors.append("  [FAIL] frequency_MHz == 3400 matches no rows after upcast")
    else:
        print(f"  [PASS] frequency_MHz exact under float64 upcast "
              f"({n_at:,} rows at 3400 MHz)")

    el = data_final[:, COL["elapsed_s"]]
    print(f"  [INFO] elapsed_s range: [{el.min():.0f}, {el.max():.0f}] s "
          f"({(el.max()-el.min())/3600:.1f} h warm-up)")
    tm = t_mxc[~np.isnan(t_mxc)]
    print(f"  [INFO] T_mxc_K range: [{tm.min():.4f}, {tm.max():.2f}] K")

    reloaded = load_pickle(pkl_path)
    same = np.array_equal(reloaded["data"], data_final, equal_nan=True)
    del reloaded
    gc.collect()
    if not same:
        errors.append("  [FAIL] Pickle round-trip: reloaded data differs")
    else:
        print(f"  [PASS] Pickle round-trip: reloaded array matches exactly "
              f"(NaN-aware)")

    if errors:
        print(f"\n  {len(errors)} sanity check(s) FAILED:")
        for e in errors:
            print(e)
    else:
        print(f"\n  All sanity checks passed.")

    # ── CSV ──────────────────────────────────────────────────────────────────
    if write_csv_file:
        print(f"\nWriting CSV to {csv_path} ...")
        print(f"  (expect roughly {n_total_rows*85/1024**3:.1f} GB and several "
              f"minutes)")
        write_csv(data_final, COLUMN_NAMES, csv_path)
        print(f"  CSV         : {csv_path}  "
              f"({os.path.getsize(csv_path)/1024**2:.1f} MB, {row_idx:,} rows)")


if __name__ == "__main__":

    _script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Build the Experiment 11 raw IQ dataset (long format) as a pickle "
        "and a CSV."
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="Folder containing the Experiment 11 *_with_T.npz files "
        "(npz_data_base_with_T)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=_script_dir,
        help="Where to write experiment_11/ (default: next to this script)",
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
