"""
experiment_12_dataset_creation.py
=================================
Converts the 126 raw phase-sweep .npz files from Experiment 12
(coherent phase control at different temperatures) into a long-format dataset:
one row per time sample, saved as a pickle and a CSV.


WHAT THIS PARTICULAR EXPERIMENT DOES
    TWO pulses are fired a short gap apart. The second lands while the defects
    are still ringing from the first, so the two responses overlap and interfere
    — like two ripples meeting on a pond. The PHASE of the first pulse (where in
    its cycle it starts, like a clock hand's position, 0-360 degrees) is swept
    through a full turn, which changes whether the ripples add or cancel.

    The point of THIS experiment is TEMPERATURE. The whole phase sweep is
    repeated at seven fridge settings from 8 mK up to 750 mK. Quantum
    interference is fragile: heat blurs it. So as the temperature climbs, the
    ability to steer the defects by turning the phase knob weakens and finally
    disappears. Each temperature is its own run, left to settle for over an hour
    first, and the whole campaign took three days.

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

    col 0 — temperature_mK   fridge set point — the PRIMARY variable
    col 1 — frequency_MHz    drive frequency in MHz (3400 or 3560)
    col 2 — spacing_ns       gap between the two drive pulses, in nanoseconds
    col 3 — phase_deg        first-pulse phase in degrees
    col 4 — timestamp_ns     time of this sample within the trace (nanoseconds)
    col 5 — elapsed_s        wall-clock seconds since the campaign started
    col 6 — I                in-phase channel value (ADC units)
    col 7 — Q                quadrature channel value (ADC units)

Only what varies gets a column. A single chip was used and the pulse width never
changed, so those would be one value repeated on every row; they are recorded in
metadata.json instead.

Total rows: 7 temperatures x 2 frequencies x 9 spacings x 121 phases x 1000 samples
          = 15,246,000

Timestamp spacing: 1 / 552.96 MHz ~ 1.8084 ns per sample

RECORDING ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Files are loaded in ascending temperature, which is also the chronological
acquisition order (8 mK was measured first, 750 mK last, over three days):

    temperature_mK (8, 95, 200, 307, 400, 600, 750)
      -> frequency_MHz (3400, 3560)
           -> spacing_ns (10, 30, 50, 100, 200, 300, 400, 500, 600)
                -> phase_deg (0, 3, ..., 360  -- 121 values, axis 1 of the .npz)
                     -> timestamp_ns (0 ... ~1806.6 ns -- 1000 values, axis 2)

Each temperature is a SEPARATE acquisition run with its own ID and start time;
the system was thermalised for >1 hour at each set point before acquisition. Files live in per-temperature subfolders:

    npz_data_base/npz_data_base_{T}mK/308_freq_{MHz}_spacing_{us}_ID_{exp_ID}.npz

and each contains:
    IQ_avg_matrix      (2, 121, 1000)   axis 0 -> [I, Q]
    pulse_phase_array  (121,)  int64    the phase axis, IN THE FILE
    time_stamp_list    (121,)  datetime64[s]   wall clock per phase point

Note that filenames express spacing in MICROSECONDS (0.01) while this dataset
stores NANOSECONDS (10), so that the values are exactly representable in float32.

Pulse width is fixed at 308 AWG clock ticks for all files:
    pulse_width_ns = 308 / 9830.4 * 1000 ~= 31.33 ns

NOTE ON OVERLAP WITH EXPERIMENT 5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The 9 files at 8 mK / 3400 MHz are byte-identical to the whole of experiment 5
(verified by hash): Experiment 5 is the 8 mK / 3400 MHz slice of this campaign,
sharing the run ID 'Shipley_phase_8mK_20251012_132853'. Both are released
separately so that each dataset stands alone.

OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    12_phase_control_temperature/experiment_12/experiment_12_dataset_long.pkl
    12_phase_control_temperature/experiment_12/experiment_12_dataset_long.csv
    12_phase_control_temperature/metadata.json
    12_phase_control_temperature/column_info.json

To load in Python:

    import pickle
    import pandas as pd

    with open("experiment_12_dataset_long.pkl", "rb") as fh:
        payload = pickle.load(fh)
    df = pd.DataFrame(payload["data"], columns=payload["columns"])

    # one ring-down trace (1000 rows):
    mask  = ((df["temperature_mK"] == 8) & (df["frequency_MHz"] == 3400)
             & (df["spacing_ns"] == 100) & (df["phase_deg"] == 0))
    trace = df[mask].sort_values("timestamp_ns")

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    python experiment_12_dataset_creation.py --data_dir /path/to/npz_data_base

    Optional arguments:
        --output_dir  where to write experiment_12/ (default: next to this script)
        --no_csv      skip the CSV (pickle only)
"""

import os
import json
import pickle
import argparse
import numpy as np
from tqdm import tqdm

# ─────────────────────────────────────────────────────────────────────────────
# RECORDING ORDER — taken directly from generate_fig_12.py
# ─────────────────────────────────────────────────────────────────────────────

SAMPLES = [("Shipley", 0)]
SAMPLE_MATERIAL = {
    "Shipley": "Sapphire substrate with spin-coated Shipley 1813 photoresist"
}

# Here they are ascending, which is also chronological: each
# temperature is its own run, and 8 mK was acquired first.
# temperature_mK -> run ID (the 'exp_ID' in the filename)
TEMPERATURE_RUNS = [
    (8, "Shipley_phase_8mK_20251012_132853"),
    (95, "Shipley_phase_95mK_20251012_221708"),
    (200, "Shipley_phase_200mK_20251013_130527"),
    (307, "Shipley_phase_307mK_20251013_212945"),
    (400, "Shipley_phase_400mK_20251014_124917"),
    (600, "Shipley_phase_600mK_20251014_220010"),
    (750, "Shipley_phase_750mK_20251015_110827"),
]

# The two notes the chip was struck at. Both were measured at every
# temperature and every gap.
FREQUENCY_LIST_MHZ = [3400, 3560]

# The gap between the two pulses. Same nine values as Experiment 5.
# Filenames use MICROSECONDS; we store nanoseconds because 0.01 has no exact
# float32 representation and 10 does.
SPACING_LIST_NS = [10, 30, 50, 100, 200, 300, 400, 500, 600]

# Where in its cycle the first pulse starts — 121 settings covering one full
# turn of the "clock hand". Stored inside each .npz, so the script READS it
# and checks it against this rather than assuming it.
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

# Drive amplitudes are not stated for this figure and are absent from the files.
PULSE1_AMPLITUDE_AU = None
PULSE2_AMPLITUDE_AU = None

# Pulse positions in the raw trace, in the same frame as the timestamp_ns column.
# Measured from the pulse envelope (threshold at 30% of peak: samples 442 -> 461),
# identical at 8 mK and 750 mK and identical to experiment 5's — the same rig and
# the same campaign. The second pulse is ANCHORED and the first moves earlier as
# the spacing grows.
PULSE2_ENVELOPE_SAMPLES = [442, 461]
PULSE2_START_NS = round(442 / ADC_CLOCK_MHZ * 1000, 1)  # ~799.3
PULSE2_END_NS = round(461 / ADC_CLOCK_MHZ * 1000, 1)  # ~833.7

# Only what actually varies gets a column. A single chip was used and the pulse
# width never changed, so those would be one value repeated on every row — they
# live in metadata.json instead.
COLUMN_NAMES = [
    "temperature_mK",
    "frequency_MHz",
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


def npz_filename(freq_mhz: int, spacing_ns: int, exp_id: str) -> str:
    """Filename on disk. Filenames express spacing in microseconds."""
    spacing_us = spacing_ns / 1000
    return (
        f"{PULSE_WIDTH_TICKS}_freq_{freq_mhz}"
        f"_spacing_{spacing_us:g}_ID_{exp_id}.npz"
    )


def temperature_subdir(temperature_mk: int) -> str:
    """generate_fig_12.py: f'npz_data_base_{temperature}mK'"""
    return f"npz_data_base_{temperature_mk}mK"


# ─────────────────────────────────────────────────────────────────────────────
# METADATA
# ─────────────────────────────────────────────────────────────────────────────


def build_metadata(campaign_start_iso: str = None, run_starts: dict = None) -> dict:
    return {
        "experiment_id": "experiment_12",
        "title": "Coherent Phase Control at Different Temperatures",
        "data_type": "raw",
        "description": (
            "Raw BCTDS homodyne I/Q measurements of a two-pulse phase coherent-"
            "control protocol on a sapphire sample with spin-coated Shipley 1813 "
            "photoresist, repeated at seven fridge temperatures from 8 to 750 mK. "
            "Raising the temperature weakens phase sensitivity and destroys "
            "coherent control, so the phase contrast collapses as T increases. "
            "Only the in-phase (I) and quadrature (Q) signals are measured; "
            "magnitude, phase, and FFT spectra are computable from them and are "
            "not stored."
        ),
        "samples": [
            {"sample_id": sid, "name": name, "material": SAMPLE_MATERIAL[name]}
            for name, sid in SAMPLES
        ],
        "apparatus": {
            "refrigerator": "Bluefors LD400 dilution refrigerator",
            "temperature_control": (
                "The MXC heater is adjusted to set the sample temperature to 8, 95, "
                "200, 307, 400, 600 and 750 mK. At each set point the system is "
                "allowed to thermalise for >1 hour before data acquisition."
            ),
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
            "frame": "raw-trace samples/ns, the same frame as timestamp_ns",
            "num_pulses": 2,
            "pulse2_envelope_samples": PULSE2_ENVELOPE_SAMPLES,
            "pulse2_start_ns": PULSE2_START_NS,
            "pulse2_end_ns": PULSE2_END_NS,
            "pulse2_is_anchored": True,
            "source": (
                "Measured from the pulse envelope in the raw data (threshold at "
                "30% of peak magnitude): samples 442 -> 461. Identical at 8 mK and "
                "750 mK, and identical to experiment 5's positions — the same rig "
                "and the same campaign."
            ),
            "note": (
                "The second pulse is fixed in time for every spacing; the first "
                "pulse moves earlier as the delay grows, so timestamp_ns is "
                "directly comparable across spacings and temperatures."
            ),
        },
        "sweep": {
            "sample": {"n": 1, "values": SAMPLE_NAMES},
            "temperature": {
                "n": len(TEMPERATURE_RUNS),
                "unit": "mK",
                "values": [t for t, _ in TEMPERATURE_RUNS],
                "note": "The primary variable of Experiment 12. Each temperature is a "
                "separate acquisition run with its own ID and start time.",
            },
            "drive_frequency": {
                "n": len(FREQUENCY_LIST_MHZ),
                "unit": "MHz",
                "values": FREQUENCY_LIST_MHZ,
                
            },
            "inter_pulse_spacing": {
                "n": len(SPACING_LIST_NS),
                "unit": "ns",
                "values": SPACING_LIST_NS,
                
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
                "The drive amplitudes are recorded nowhere: not in the filenames, "
                "not in the .npz contents. Experiment 4 used 30000 a.u. (first "
                "pulse) and 10000 a.u. (second); that is NOT asserted here."
            ),
        },
        "overlap_with_other_experiments": {
            "experiment_5": (
                "The 9 files at 8 mK / 3400 MHz are byte-identical to the whole of "
                "experiment 5 (verified by hash). Experiment 5 is the 8 mK / 3400 MHz "
                "slice of this campaign, sharing the run ID "
                "'Shipley_phase_8mK_20251012_132853'. Both are released separately "
                "so each dataset stands alone."
            )
        },
        "acquisition": {
            "campaign_start_utc": campaign_start_iso,
            "run_starts_utc": run_starts or {},
            "run_ids": {str(t): eid for t, eid in TEMPERATURE_RUNS},
            "elapsed_s_note": (
                "elapsed_s is wall-clock seconds since campaign_start_utc (the "
                "earliest timestamp across all files, i.e. the start of the 8 mK "
                "run), taken from the time_stamp_list array inside each .npz. The "
                "campaign spans about three days. To get seconds within a single "
                "temperature's run, subtract that run's start from "
                "acquisition.run_starts_utc. Stored as elapsed seconds rather than "
                "an absolute epoch because float32 cannot represent Unix "
                "timestamps to better than ~128 s; elapsed integer seconds up to "
                "16.7 M are exact."
            ),
        },
    }


def build_column_info() -> dict:
    n_rows = (
        len(TEMPERATURE_RUNS)
        * len(FREQUENCY_LIST_MHZ)
        * len(SPACING_LIST_NS)
        * len(EXPECTED_PHASE_DEG)
        * N_TIME_SAMPLES
    )
    return {
        "dataset": "experiment_12_phase_control_temperature",
        "format": "long (one row per time sample)",
        "n_rows": n_rows,
        "n_columns": len(COLUMN_NAMES),
        "schema_rule": (
            "The filename and its parent folder hold everything constant within a "
            "file (sample, pulse width, temperature, frequency, spacing); the array "
            "axes hold what varies (phase, time) together with the measured I/Q. "
            "The phase axis and the per-phase wall clock are stored inside the .npz."
        ),
        "columns": [
            {
                "name": "temperature_mK",
                "dtype": "float32",
                "unit": "mK",
                "role": "coordinate (primary swept input)",
                "measured": False,
                "varies_within_file": False,
                "computed_from": "parent folder 'npz_data_base_{T}mK' and the "
                "filename's exp_ID",
                "values": [t for t, _ in TEMPERATURE_RUNS],
                "n_unique": len(TEMPERATURE_RUNS),
                "description": "Fridge set point — the primary variable of Figure "
                "12. This is a SET POINT, not a measured temperature: these files "
                "carry no thermometry arrays (experiment 11's do). Each temperature "
                "is a separate run, thermalised >1 hour beforehand.",
            },
            {
                "name": "frequency_MHz",
                "dtype": "float32",
                "unit": "MHz",
                "role": "coordinate (swept input)",
                "measured": False,
                "varies_within_file": False,
                "computed_from": "filename field 'freq_XXXX'",
                "values": FREQUENCY_LIST_MHZ,
                "n_unique": len(FREQUENCY_LIST_MHZ),
                "description": "Drive and readout frequency. Both pulses fire at "
                "this frequency.",
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
                "description": "Gap between the end of the first pulse and the "
                "start of the second. Stored in nanoseconds rather than the "
                "filenames' microseconds so the values are exact in float32. The "
                "nine spacings span the ~100 ns ring-down lifetime.",
            },
            {
                "name": "phase_deg",
                "dtype": "float32",
                "unit": "deg",
                "role": "coordinate (swept input)",
                "measured": False,
                "varies_within_file": True,
                "computed_from": "pulse_phase_array, stored in each .npz; axis 1",
                "range": [0, 360],
                "n_unique": len(EXPECTED_PHASE_DEG),
                "description": "Phase of the FIRST pulse. The second pulse's phase "
                "is held fixed. 0 and 360 deg are the same physical point, acquired "
                "independently.",
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
                "across spacings and temperatures because the second pulse is "
                "anchored.",
            },
            {
                "name": "elapsed_s",
                "dtype": "float32",
                "unit": "s",
                "role": "acquisition metadata",
                "measured": False,
                "varies_within_file": True,
                "computed_from": "time_stamp_list in each .npz, minus the campaign "
                "start",
                "description": "Wall-clock seconds since the campaign started (the "
                "8 mK run), recorded once per phase point. The campaign spans about "
                "three days, so this also encodes which run a row belongs to and "
                "the thermalisation gaps between set points.",
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
    output_dir = os.path.join(output_dir, "experiment_12")
    os.makedirs(output_dir, exist_ok=True)
    pkl_path = os.path.join(output_dir, "experiment_12_dataset_long.pkl")
    csv_path = os.path.join(output_dir, "experiment_12_dataset_long.csv")

    n_temps = len(TEMPERATURE_RUNS)
    n_freqs = len(FREQUENCY_LIST_MHZ)
    n_spacings = len(SPACING_LIST_NS)
    n_phases = len(EXPECTED_PHASE_DEG)
    n_total_rows = n_temps * n_freqs * n_spacings * n_phases * N_TIME_SAMPLES

    print(f"\nFormat          : long (one row per time sample)")
    print(f"Sample          : {SAMPLE_NAMES[0]} (sapphire + Shipley 1813)")
    print(f"Temperatures    : {n_temps}  ({[t for t, _ in TEMPERATURE_RUNS]} mK)")
    print(f"Frequencies     : {n_freqs}  ({FREQUENCY_LIST_MHZ} MHz)")
    print(f"Spacings        : {n_spacings}  ({SPACING_LIST_NS} ns)")
    print(f"Phases          : {n_phases}  (0-360 deg, step 3)")
    print(f"Time samples    : {N_TIME_SAMPLES} per measurement")
    print(f"Total rows      : {n_temps} x {n_freqs} x {n_spacings} x {n_phases} x "
          f"{N_TIME_SAMPLES} = {n_total_rows:,}")
    print(f"Columns         : {COLUMN_NAMES}\n")

    # ── Pass 1: find the campaign start and each run's start ─────────────────
    campaign_start = None
    run_starts = {}
    for temperature_mk, exp_id in TEMPERATURE_RUNS:
        sub = os.path.join(data_dir, temperature_subdir(temperature_mk))
        run_start = None
        for freq_mhz in FREQUENCY_LIST_MHZ:
            for spacing_ns in SPACING_LIST_NS:
                path = os.path.join(sub, npz_filename(freq_mhz, spacing_ns, exp_id))
                if not os.path.exists(path):
                    continue
                with np.load(path, allow_pickle=True) as z:
                    t0 = z["time_stamp_list"][0]
                run_start = t0 if run_start is None else min(run_start, t0)
        if run_start is not None:
            run_starts[str(temperature_mk)] = str(run_start)
            campaign_start = (
                run_start if campaign_start is None else min(campaign_start, run_start)
            )
    if campaign_start is None:
        raise FileNotFoundError(
            f"No Experiment 12 .npz files found under {data_dir}\n"
            f"Expected subfolders like {temperature_subdir(8)}/ containing "
            f"{npz_filename(3400, 10, TEMPERATURE_RUNS[0][1])}"
        )
    print(f"Campaign start (from time_stamp_list): {campaign_start}\n")

    # ── Pass 2: build ────────────────────────────────────────────────────────
    data_all = np.empty((n_total_rows, len(COLUMN_NAMES)), dtype=np.float32)
    row_idx = 0
    sample_id = SAMPLES[0][1]
    n_files = 0

    for temperature_mk, exp_id in tqdm(TEMPERATURE_RUNS, desc="Temperatures"):

        subdir = os.path.join(data_dir, temperature_subdir(temperature_mk))

        for freq_mhz in FREQUENCY_LIST_MHZ:
            for spacing_ns in SPACING_LIST_NS:

                filename = npz_filename(freq_mhz, spacing_ns, exp_id)
                filepath = os.path.join(subdir, filename)

                if not os.path.exists(filepath):
                    print(f"  WARNING: file not found -> {filename}  (skipping)")
                    continue

                with np.load(filepath, allow_pickle=True) as z:
                    IQ_matrix = z["IQ_avg_matrix"]
                    phase_array = z["pulse_phase_array"]
                    time_stamps = z["time_stamp_list"]

                if IQ_matrix.shape != (2, n_phases, N_TIME_SAMPLES):
                    print(f"  WARNING: {filename} has shape {IQ_matrix.shape}, "
                          f"expected (2, {n_phases}, {N_TIME_SAMPLES}) — skipping")
                    continue

                if not np.array_equal(phase_array, EXPECTED_PHASE_DEG):
                    print(f"  WARNING: {filename} pulse_phase_array does not match "
                          f"np.arange(0, 361, 3) — using the file's own axis")

                # Wall-clock time, i.e. when this reading was actually taken in
                # the lab. Stored as SECONDS SINCE THE CAMPAIGN STARTED (the 8 mK
                # run) rather than a calendar date: float32 cannot hold a full
                # unix timestamp accurately, but elapsed seconds it stores
                # exactly. The campaign spans ~3 days, so this also tells you
                # which temperature run a row belongs to and how long the fridge
                # was left to settle between them.
                # Not to be confused with timestamp_ns — that is the fast axis
                # WITHIN one ring-down (nanoseconds); this is the slow axis
                # ACROSS the campaign (seconds).
                elapsed = (
                    (time_stamps - campaign_start)
                    .astype("timedelta64[s]")
                    .astype(np.float64)
                )

                I_matrix = IQ_matrix[0]
                Q_matrix = IQ_matrix[1]
                n_files += 1

                for phase_idx, phase_deg in enumerate(phase_array):

                    end_idx = row_idx + N_TIME_SAMPLES

                    data_all[row_idx:end_idx, COL["temperature_mK"]] = temperature_mk
                    data_all[row_idx:end_idx, COL["frequency_MHz"]] = freq_mhz
                    data_all[row_idx:end_idx, COL["spacing_ns"]] = spacing_ns
                    data_all[row_idx:end_idx, COL["phase_deg"]] = phase_deg
                    data_all[row_idx:end_idx, COL["timestamp_ns"]] = TIMESTAMPS_NS
                    data_all[row_idx:end_idx, COL["elapsed_s"]] = elapsed[phase_idx]
                    data_all[row_idx:end_idx, COL["I"]] = I_matrix[phase_idx]  # all 1000
                    data_all[row_idx:end_idx, COL["Q"]] = Q_matrix[phase_idx]  # all 1000

                    row_idx += N_TIME_SAMPLES

    data_final = data_all[:row_idx]

    # ── Save ─────────────────────────────────────────────────────────────────
    campaign_start_iso = str(campaign_start)
    print(f"\nFiles ingested  : {n_files} of 126")
    print(f"Saving to {pkl_path} ...")

    payload = {
        "data": data_final,
        "columns": COLUMN_NAMES,
        "attrs": build_metadata(campaign_start_iso, run_starts),
        "column_doc": build_column_info(),
    }
    save_pickle(payload, pkl_path)

    meta_path = os.path.join(script_dir, "metadata.json")
    cols_path = os.path.join(script_dir, "column_info.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(build_metadata(campaign_start_iso, run_starts), fh, indent=2)
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
        print(f"  [PASS] Row count: {row_idx:,} = {n_temps} temps x {n_freqs} freqs "
              f"x {n_spacings} spacings x {n_phases} phases x {N_TIME_SAMPLES}")

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
        (COL["temperature_mK"], "temperatures", n_temps),
        (COL["frequency_MHz"], "frequencies", n_freqs),
        (COL["spacing_ns"], "spacings", n_spacings),
        (COL["phase_deg"], "phases", n_phases),
    ]:
        got = len(np.unique(data_final[:, col_idx]))
        if got != expected:
            errors.append(f"  [FAIL] Expected {expected} unique {name}, got {got}")
        else:
            print(f"  [PASS] Unique {name}: {got}")

    spacing_64 = data_final[:, COL["spacing_ns"]].astype(np.float64)
    n_at_100 = int((spacing_64 == 100).sum())
    if n_at_100 == 0:
        errors.append("  [FAIL] spacing_ns == 100 matches no rows after upcast")
    else:
        print(f"  [PASS] spacing_ns exact under float64 upcast "
              f"({n_at_100:,} rows at 100 ns)")

    el = data_final[:, COL["elapsed_s"]]
    print(f"  [INFO] elapsed_s range: [{el.min():.0f}, {el.max():.0f}] s "
          f"({(el.max()-el.min())/3600:.1f} h campaign)")

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
        description="Build the Experiment 12 raw IQ dataset (long format) as a pickle "
        "and a CSV."
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="Folder containing the per-temperature subfolders "
        "(npz_data_base, which holds npz_data_base_8mK/ etc.)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=_script_dir,
        help="Where to write experiment_12/ (default: next to this script)",
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
