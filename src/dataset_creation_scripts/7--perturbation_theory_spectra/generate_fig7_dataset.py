"""
generate_fig7_dataset.py
========================
Organizes Figure 7 analytical phase-V data into clean Pickle dataframes
plus column-info JSON files.

Outputs:
    dataset_fig7/
        figure7_phase_fft.pkl
        figure7_phase_fft_column_info.json

        figure7_zero_freq_linecut.pkl
        figure7_zero_freq_linecut_column_info.json

        figure7_metadata.json
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm
from scipy.fft import fft, fftfreq


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 7 PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_ID = 7
FIGURE_ID = 7

F1_HZ = 3.0e9
F2_HZ = 4.0e9

OMEGA_1_RAD_S = 2 * np.pi * F1_HZ
OMEGA_2_RAD_S = 2 * np.pi * F2_HZ

J_RAD_S = 5.0e3 * np.pi
OMEGA_DRIVE_AMP_RAD_S = 2 * np.pi * 1e2

T_MAX_S = 1e-6
DT_S = 1.0e-9

NUM_DRIVE_FREQS = 900
DELTA_F_HZ = 0.9e9

GAMMA_CORRECTION = 0.4
EPS = 1e-15

PULSE_DURATION_NS = T_MAX_S * 1e9

T_S = np.arange(0, T_MAX_S, DT_S)
T_NS = (T_S * 1e9).astype(np.float32)
N_TIME = len(T_S)

DRIVE_FREQ_HZ = np.linspace(
    (F1_HZ + F2_HZ) / 2 - DELTA_F_HZ,
    (F1_HZ + F2_HZ) / 2 + DELTA_F_HZ,
    NUM_DRIVE_FREQS,
)

DRIVE_FREQ_GHZ = (DRIVE_FREQ_HZ / 1e9).astype(np.float32)
OMEGA_D_RAD_S = 2 * np.pi * DRIVE_FREQ_HZ

FFT_FREQ_HZ = fftfreq(N_TIME, DT_S)
FFT_MASK = FFT_FREQ_HZ >= 0

FFT_FREQ_HZ_POS = FFT_FREQ_HZ[FFT_MASK].astype(np.float32)
FFT_FREQ_MHZ_POS = (FFT_FREQ_HZ_POS / 1e6).astype(np.float32)

WINDOW = np.hanning(N_TIME)


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def schema_entry(
    column_name,
    data_type,
    can_have_nulls,
    maps_to_original,
    value_or_range,
    in_raw_simulation,
    derivation_or_notes,
):
    return {
        "column_name": column_name,
        "data_type": data_type,
        "can_have_nulls": can_have_nulls,
        "maps_to_original": maps_to_original,
        "value_or_range": value_or_range,
        "num_columns": 1,
        "in_raw_simulation": in_raw_simulation,
        "derivation_or_notes": derivation_or_notes,
    }


PHASE_FFT_COLUMN_INFO = [
    schema_entry("sample_id", "int32", False, "manual feature", "7", False, "Numeric sample/figure identifier."),
    schema_entry("figure_id", "int32", False, "manual feature", "7", False, "Figure identifier."),
    schema_entry("f1_GHz", "float32", False, "F1_HZ / 1e9", "3.0 GHz", False, "First bare transition frequency."),
    schema_entry("f2_GHz", "float32", False, "F2_HZ / 1e9", "4.0 GHz", False, "Second bare transition frequency."),
    schema_entry("j_rad_s", "float32", False, "J_RAD_S", "5000*pi rad/s", False, "Analytical coupling parameter."),
    schema_entry("pulse_duration_ns","float32",False,"T_MAX_S * 1e9","1000 ns",False,"Effective analytical pulse/evolution duration used to generate the phase trace."),
    schema_entry("omega_drive_amp_rad_s", "float32", False, "OMEGA_DRIVE_AMP_RAD_S", "2*pi*100 rad/s", False, "Analytical drive-amplitude parameter."),
    schema_entry("drive_frequency_GHz", "float32", False, "DRIVE_FREQ_HZ / 1e9", "2.6 to 4.4 GHz", False, "Swept drive frequency."),
    schema_entry("fft_frequency_Hz", "float32", False, "positive FFT frequency axis", ">= 0 Hz", False, "Positive FFT frequency."),
    schema_entry("fft_frequency_MHz", "float32", False, "fft_frequency_Hz / 1e6", ">= 0 MHz", False, "Positive FFT frequency in MHz."),
    schema_entry("normalized_phase_fft", "float32", False, "phase_eg_fft", "0 to 1", False, "Normalized FFT magnitude of analytical phase signal."),
    schema_entry("gamma_corrected_phase_fft", "float32", False, "(phase_eg_fft / vmax)^gamma * vmax", ">= 0", False, "Gamma-corrected FFT intensity used only for visualization."),
]

LINECUT_COLUMN_INFO = [
    schema_entry("sample_id", "int32", False, "manual feature", "7", False, "Numeric sample/figure identifier."),
    schema_entry("figure_id", "int32", False, "manual feature", "7", False, "Figure identifier."),
    schema_entry("f1_GHz", "float32", False, "F1_HZ / 1e9", "3.0 GHz", False, "First bare transition frequency."),
    schema_entry("f2_GHz", "float32", False, "F2_HZ / 1e9", "4.0 GHz", False, "Second bare transition frequency."),
    schema_entry("j_rad_s", "float32", False, "J_RAD_S", "5000*pi rad/s", False, "Analytical coupling parameter."),
    schema_entry("pulse_duration_ns","float32",False,"T_MAX_S * 1e9","1000 ns",False,"Effective analytical pulse/evolution duration used to generate the phase trace."),
    schema_entry("omega_drive_amp_rad_s", "float32", False, "OMEGA_DRIVE_AMP_RAD_S", "2*pi*100 rad/s", False, "Analytical drive-amplitude parameter."),
    schema_entry("drive_frequency_GHz", "float32", False, "DRIVE_FREQ_HZ / 1e9", "2.6 to 4.4 GHz", False, "Swept drive frequency."),
    schema_entry("fft_frequency_MHz", "float32", False, "zero FFT index", "0 MHz", False, "Zero-frequency FFT slice."),
    schema_entry("zero_freq_normalized_phase_fft", "float32", False, "phase_eg_fft[zero_idx, :]", "0 to 1", False, "Linecut at zero FFT frequency."),
]


def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def save_pickle(df, path):
    df.to_pickle(path)
    size_mb = os.path.getsize(path) / (1024 ** 2)
    print(f"Saved: {path} ({size_mb:.2f} MB)")


# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICAL COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────

def compute_phase_fft():
    phase_eg_fft = np.zeros((len(FFT_FREQ_HZ_POS), NUM_DRIVE_FREQS), dtype=np.float32)

    print("Starting Figure 7 analytical computation...")

    for i, wd in enumerate(tqdm(OMEGA_D_RAD_S, desc="drive frequency sweep")):
        delta_1 = OMEGA_1_RAD_S - wd
        delta_2 = OMEGA_2_RAD_S - wd
        delta = delta_1 - delta_2

        c_eg_0 = (
            (OMEGA_DRIVE_AMP_RAD_S / 2)
            * (1 - np.exp(-1j * delta_1 * T_S))
            / (delta_1 + EPS)
        )

        term1 = (1 / (delta_2 + EPS)) * (
            (1 - np.exp(-1j * delta_1 * T_S)) / (delta_1 + EPS)
            + (1 - np.exp(1j * delta * T_S)) / (delta + EPS)
        )

        c_eg_1 = (OMEGA_DRIVE_AMP_RAD_S / 2) * J_RAD_S * term1

        exp_w = np.exp(1j * (OMEGA_1_RAD_S - wd) * T_S)
        exp_delta_pos = np.exp(1j * delta * T_S)
        exp_delta_neg = np.exp(-1j * delta * T_S)

        cum_tau3 = np.cumsum(exp_w) * DT_S
        I_tau2 = np.copy(cum_tau3)
        I_tau1 = np.zeros_like(T_S, dtype=complex)

        for idx1 in range(N_TIME):
            integrand_tau2 = exp_delta_pos[:idx1 + 1] * I_tau2[:idx1 + 1]
            I_tau1[idx1] = np.sum(integrand_tau2) * DT_S

        integrand_tau1 = exp_delta_neg * I_tau1
        integral_I = np.cumsum(integrand_tau1) * DT_S

        c_eg_2 = 1j * (OMEGA_DRIVE_AMP_RAD_S / 2) * (J_RAD_S ** 2) * integral_I

        c_eg = c_eg_0 + c_eg_1 + c_eg_2
        phi_eg = np.angle(c_eg)

        fft_phi = np.abs(fft(phi_eg * WINDOW))[FFT_MASK].astype(np.float32)
        max_val = np.max(fft_phi)

        if max_val > EPS:
            phase_eg_fft[:, i] = fft_phi / max_val

    vmax = np.max(phase_eg_fft)
    if vmax > EPS:
        gamma_corrected = ((phase_eg_fft / vmax) ** GAMMA_CORRECTION * vmax).astype(np.float32)
    else:
        gamma_corrected = np.zeros_like(phase_eg_fft, dtype=np.float32)

    print("Computation finished.")
    return phase_eg_fft, gamma_corrected


# ─────────────────────────────────────────────────────────────────────────────
# DATAFRAME BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_phase_fft_df(phase_eg_fft, gamma_corrected):
    n_fft, n_drive = phase_eg_fft.shape
    n_rows = n_fft * n_drive

    return pd.DataFrame({
        "sample_id": np.full(n_rows, SAMPLE_ID, dtype=np.int32),
        "figure_id": np.full(n_rows, FIGURE_ID, dtype=np.int32),
        "f1_GHz": np.full(n_rows, F1_HZ / 1e9, dtype=np.float32),
        "f2_GHz": np.full(n_rows, F2_HZ / 1e9, dtype=np.float32),
        "j_rad_s": np.full(n_rows, J_RAD_S, dtype=np.float32),
        "pulse_duration_ns": np.full(n_rows, PULSE_DURATION_NS, dtype=np.float32),
        "omega_drive_amp_rad_s": np.full(n_rows, OMEGA_DRIVE_AMP_RAD_S, dtype=np.float32),
        "drive_frequency_GHz": np.tile(DRIVE_FREQ_GHZ, n_fft).astype(np.float32),
        "fft_frequency_Hz": np.repeat(FFT_FREQ_HZ_POS, n_drive).astype(np.float32),
        "fft_frequency_MHz": np.repeat(FFT_FREQ_MHZ_POS, n_drive).astype(np.float32),
        "normalized_phase_fft": phase_eg_fft.reshape(-1).astype(np.float32),
        "gamma_corrected_phase_fft": gamma_corrected.reshape(-1).astype(np.float32),
    })


def build_zero_linecut_df(phase_eg_fft):
    zero_idx = int(np.argmin(np.abs(FFT_FREQ_MHZ_POS - 0.0)))

    return pd.DataFrame({
        "sample_id": np.full(NUM_DRIVE_FREQS, SAMPLE_ID, dtype=np.int32),
        "figure_id": np.full(NUM_DRIVE_FREQS, FIGURE_ID, dtype=np.int32),
        "f1_GHz": np.full(NUM_DRIVE_FREQS, F1_HZ / 1e9, dtype=np.float32),
        "f2_GHz": np.full(NUM_DRIVE_FREQS, F2_HZ / 1e9, dtype=np.float32),
        "j_rad_s": np.full(NUM_DRIVE_FREQS, J_RAD_S, dtype=np.float32),
        "pulse_duration_ns": np.full(NUM_DRIVE_FREQS, PULSE_DURATION_NS, dtype=np.float32),
        "omega_drive_amp_rad_s": np.full(NUM_DRIVE_FREQS, OMEGA_DRIVE_AMP_RAD_S, dtype=np.float32),
        "drive_frequency_GHz": DRIVE_FREQ_GHZ.astype(np.float32),
        "fft_frequency_MHz": np.full(NUM_DRIVE_FREQS, FFT_FREQ_MHZ_POS[zero_idx], dtype=np.float32),
        "zero_freq_normalized_phase_fft": phase_eg_fft[zero_idx, :].astype(np.float32),
    })


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def build_dataset(output_dir):
    os.makedirs(output_dir, exist_ok=True)

    phase_eg_fft, gamma_corrected = compute_phase_fft()

    phase_fft_df = build_phase_fft_df(phase_eg_fft, gamma_corrected)
    linecut_df = build_zero_linecut_df(phase_eg_fft)

    phase_fft_pkl = os.path.join(output_dir, "figure7_phase_fft.pkl")
    linecut_pkl = os.path.join(output_dir, "figure7_zero_freq_linecut.pkl")

    save_pickle(phase_fft_df, phase_fft_pkl)
    save_pickle(linecut_df, linecut_pkl)

    save_json(
        PHASE_FFT_COLUMN_INFO,
        os.path.join(output_dir, "figure7_phase_fft_column_info.json"),
    )
    save_json(
        LINECUT_COLUMN_INFO,
        os.path.join(output_dir, "figure7_zero_freq_linecut_column_info.json"),
    )

    metadata = {
        "figure": 7,
        "sample_id": SAMPLE_ID,
        "description": "Analytical phase-V calculation organized into interpretable Pickle dataframes.",
        "f1_Hz": F1_HZ,
        "f2_Hz": F2_HZ,
        "f1_GHz": F1_HZ / 1e9,
        "f2_GHz": F2_HZ / 1e9,
        "omega_1_rad_s": OMEGA_1_RAD_S,
        "omega_2_rad_s": OMEGA_2_RAD_S,
        "j_rad_s": J_RAD_S,
        "omega_drive_amp_rad_s": OMEGA_DRIVE_AMP_RAD_S,
        "t_max_s": T_MAX_S,
        "dt_s": DT_S,
        "n_time_samples": int(N_TIME),
        "num_drive_freqs": int(NUM_DRIVE_FREQS),
        "drive_frequency_GHz_start": float(DRIVE_FREQ_GHZ[0]),
        "drive_frequency_GHz_stop": float(DRIVE_FREQ_GHZ[-1]),
        "n_fft_frequencies": int(len(FFT_FREQ_HZ_POS)),
        "gamma_correction": GAMMA_CORRECTION,
        "outputs": {
            "phase_fft_pickle": "figure7_phase_fft.pkl",
            "phase_fft_column_info": "figure7_phase_fft_column_info.json",
            "zero_freq_linecut_pickle": "figure7_zero_freq_linecut.pkl",
            "zero_freq_linecut_column_info": "figure7_zero_freq_linecut_column_info.json",
        },
    }

    save_json(metadata, os.path.join(output_dir, "figure7_metadata.json"))

    print("\nDone.")
    print(f"Phase FFT shape       : {phase_fft_df.shape}")
    print(f"Zero linecut shape    : {linecut_df.shape}")
    print(f"Saved output directory: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate clean Pickle datasets for Figure 7."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="dataset_fig7",
        help="Output directory.",
    )

    args = parser.parse_args()
    build_dataset(args.output_dir)