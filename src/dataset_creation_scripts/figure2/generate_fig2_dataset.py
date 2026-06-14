"""
generate_fig2_dataset.py
=====================
Converts all 42 raw .npy files from the Figure 2 pulse-width sweep into
a long-format dataset: one row per time sample.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5 columns, one row per time sample:

    col 0 — pulse_width_ns   duration of the drive pulse in nanoseconds
    col 1 — frequency_MHz    drive frequency in MHz
    col 2 — timestamp_ns     time of this sample after pulse end (nanoseconds)
    col 3 — I                in-phase channel value (ADC units)
    col 4 — Q                quadrature channel value (ADC units)

Total rows: 42 pulse widths × 500 frequencies × 1000 time samples = 21,000,000

Example rows for one ringdown measurement at pulse=5.09 ns, freq=4100 MHz:

    pulse_width_ns  frequency_MHz  timestamp_ns      I        Q
    5.09            4100           0.000          -1234.0   567.0
    5.09            4100           1.810          -1230.0   560.0
    5.09            4100           3.620          -1220.0   550.0
    ...
    5.09            4100           1808.100        -10.0     5.0

Timestamp spacing: 1 / 552.96 MHz ≈ 1.8096 ns per sample

OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Saved to:  Figure_2_phase_V_sweep_width/dataset/figure2_dataset_long.npz

    data["data"]     shape (21_000_000, 5)
    data["columns"]  shape (5,)

To load in Python:

    import numpy as np
    import pandas as pd

    raw = np.load("figure2_dataset_long.npz", allow_pickle=True)
    df  = pd.DataFrame(raw["data"], columns=raw["columns"])

    # Filter to one measurement:
    mask = (df["pulse_width_ns"] == 5.09) & (df["frequency_MHz"] == 4100)
    trace = df[mask]   # 1000 rows — the full ringdown waveform

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    python generate_fig2_dataset.py

    Optional arguments:
        --data_dir    path to the folder containing the .npy files
        --output_dir  folder where the .npz will be saved (created if needed)
"""

import os
import argparse
import numpy as np
from tqdm import tqdm


# ─────────────────────────────────────────────────────────────────────────────
# RECORDING ORDER — taken directly from generate_fig_2.py lines 84–85
# ─────────────────────────────────────────────────────────────────────────────

PULSE_WIDTH_LIST   = np.arange(50, 2101, 50)       # 42 values, in ticks
FREQUENCY_LIST_MHZ = np.arange(4100, 4600, 1)      # 500 values

AWG_CLOCK_MHZ  = 9830.4    # MHz  →  1 tick ≈ 0.1017 ns
ADC_CLOCK_MHZ  = 552.96    # MHz  →  1 sample ≈ 1.8096 ns
N_TIME_SAMPLES = 1000

# Pre-compute timestamp array once — same for every measurement
# t[k] = k / 552.96 MHz  (in nanoseconds)
TIMESTAMPS_NS = (np.arange(N_TIME_SAMPLES) / ADC_CLOCK_MHZ) * 1000
# → [0.000, 1.810, 3.619, ..., 1808.910]  ns

COLUMN_NAMES = ["pulse_width_ns", "frequency_MHz", "timestamp_ns", "I", "Q"]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def build_dataset(data_dir: str, output_dir: str):

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "figure2_dataset_long.npz")

    n_files      = len(PULSE_WIDTH_LIST)
    n_freqs      = len(FREQUENCY_LIST_MHZ)
    n_total_rows = n_files * n_freqs * N_TIME_SAMPLES   # 21,000,000

    print(f"\nFormat          : long (one row per time sample)")
    print(f"Pulse widths    : {n_files} values  ({PULSE_WIDTH_LIST[0]}–{PULSE_WIDTH_LIST[-1]} ticks)")
    print(f"Frequencies     : {n_freqs} values  ({FREQUENCY_LIST_MHZ[0]}–{FREQUENCY_LIST_MHZ[-1]} MHz)")
    print(f"Time samples    : {N_TIME_SAMPLES} per measurement")
    print(f"Total rows      : {n_files} × {n_freqs} × {N_TIME_SAMPLES} = {n_total_rows:,}")
    print(f"Columns         : {COLUMN_NAMES}\n")

    # Pre-allocate full array — float32 keeps size manageable
    # 21,000,000 rows × 5 cols × 4 bytes = ~400 MB in memory
    data_all = np.empty((n_total_rows, 5), dtype=np.float32)

    row_idx = 0

    for ticks in tqdm(PULSE_WIDTH_LIST, desc="Loading files"):

        pulse_ns = (ticks / AWG_CLOCK_MHZ) * 1000

        filename = f"{ticks}_IQ_avg_matrix_0.npy"
        filepath = os.path.join(data_dir, filename)

        if not os.path.exists(filepath):
            print(f"  WARNING: file not found → {filename}  (skipping)")
            continue

        IQ_matrix = np.load(filepath)   # shape (2, 500, 1000)

        if IQ_matrix.shape != (2, 500, 1000):
            print(f"  WARNING: {filename} has unexpected shape {IQ_matrix.shape} — skipping")
            continue

        I_matrix = IQ_matrix[0]   # shape (500, 1000)
        Q_matrix = IQ_matrix[1]   # shape (500, 1000)

        for freq_idx, freq_mhz in enumerate(FREQUENCY_LIST_MHZ):

            i_trace = I_matrix[freq_idx]   # shape (1000,)
            q_trace = Q_matrix[freq_idx]   # shape (1000,)

            end_idx = row_idx + N_TIME_SAMPLES

            # Fill all 1000 time-sample rows for this (pulse, freq) pair at once
            data_all[row_idx:end_idx, 0] = pulse_ns        # pulse_width_ns
            data_all[row_idx:end_idx, 1] = freq_mhz        # frequency_MHz
            data_all[row_idx:end_idx, 2] = TIMESTAMPS_NS   # timestamp_ns
            data_all[row_idx:end_idx, 3] = i_trace         # I
            data_all[row_idx:end_idx, 4] = q_trace         # Q

            row_idx += N_TIME_SAMPLES

    # ── Save ──────────────────────────────────────────────────────────────────
    print(f"\nSaving to {output_path} ...")

    np.savez_compressed(
        output_path,
        data    = data_all[:row_idx],
        columns = np.array(COLUMN_NAMES)
    )

    size_mb = os.path.getsize(output_path) / (1024 ** 2)

    print(f"\nDone!")
    print(f"  Shape     : ({row_idx:,}, 5)   — rows × columns")
    print(f"  File size : {size_mb:.1f} MB")
    print(f"  Saved to  : {output_path}")

    # ── Preview CSV — first and last 5 measurements (5000 rows total) ─────────
    # Each "measurement" = 1000 consecutive rows, so sample by measurement index
    import pandas as pd

    csv_path = os.path.join(output_dir, "figure2_long_preview.csv")

    # First 5 measurements = rows 0–4999, last 5 = rows -5000 to end
    n_measurements = row_idx // N_TIME_SAMPLES
    first_5 = np.arange(0, 5 * N_TIME_SAMPLES)
    last_5  = np.arange(
        max(5, n_measurements - 5) * N_TIME_SAMPLES,
        n_measurements * N_TIME_SAMPLES
    )
    preview_idx = np.concatenate([first_5, last_5])

    df_preview = pd.DataFrame(data_all[preview_idx], columns=COLUMN_NAMES)
    df_preview.to_csv(csv_path, index=False)

    print(f"\n  Preview CSV : {csv_path}")
    print(f"  Preview rows: first 5 + last 5 measurements = {len(preview_idx):,} rows")
    print(f"\nSample (first 3 rows of preview):")
    print(df_preview.head(3).to_string(index=False))


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND LINE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    _script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Build Figure 2 IQ dataset in long format (one row per time sample)."
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default=os.path.join(_script_dir, "matrix_npy"),
        help="Folder containing the *_IQ_avg_matrix_0.npy files"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.path.join(_script_dir, "dataset"),
        help="Output folder (created automatically if it does not exist)"
    )
    args = parser.parse_args()

    build_dataset(data_dir=args.data_dir, output_dir=args.output_dir)