"""
generate_fig16_dataset.py
=========================
Create clean Pickle datasets for Figure 16.

Figure 16 compares two N=2 TLS configurations:
    1. non_degenerate: omega_1 = 4.0 GHz, omega_2 = 4.12 GHz
    2. degenerate:     omega_1 = 4.0 GHz, omega_2 = 4.0 GHz

Outputs:
    dataset_fig16/
        figure16_time_domain.pkl
        figure16_time_domain_column_info.json

        figure16_phase_fft.pkl
        figure16_phase_fft_column_info.json

        figure16_metadata.json
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from scipy.fft import fft, fftfreq
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

from qutip import (
    tensor,
    qeye,
    sigmax,
    sigmaz,
    sigmap,
    sigmam,
    mesolve,
    Options,
)


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 16 PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_ID = 16
FIGURE_ID = 16

CONFIGURATIONS = {
    "non_degenerate": {
        "omega_tls_1_GHz": 4.0,
        "omega_tls_2_GHz": 4.12,
    },
    "degenerate": {
        "omega_tls_1_GHz": 4.0,
        "omega_tls_2_GHz": 4.0,
    },
}

J_COUPLING_GHZ = 0.01
DRIVE_AMPLITUDE_GHZ = 0.10

PULSE_DURATION_NS = 100.0
TOTAL_TIME_NS = 800.0
DT_NS = 0.01

DRIVE_FREQ_GHZ = np.linspace(3.0, 5.0, 400).astype(np.float32)

GAMMA_COLLECTIVE_NS_INV = 0.002
GAMMA_LOCAL_1_NS_INV = 0.0001
GAMMA_LOCAL_2_NS_INV = 0.0005

FFT_WINDOW_START_NS = 0.0
FFT_WINDOW_STOP_NS = 300.0
FFT_VIEW_MHZ = 150.0

MAX_WORKERS = 80

TLIST_NS = np.arange(0.0, TOTAL_TIME_NS, DT_NS).astype(np.float32)
N_TIME = TLIST_NS.size
N_DRIVE = DRIVE_FREQ_GHZ.size

FFT_TIME_MASK = (TLIST_NS >= FFT_WINDOW_START_NS) & (TLIST_NS <= FFT_WINDOW_STOP_NS)

if FFT_TIME_MASK.sum() < 2:
    raise ValueError("FFT window is too small.")

FFT_FREQ_GHZ = fftfreq(FFT_TIME_MASK.sum(), DT_NS).astype(np.float32)
FFT_POS_MASK = (FFT_FREQ_GHZ >= 0.0) & (FFT_FREQ_GHZ <= FFT_VIEW_MHZ / 1000.0)
FFT_FREQ_MHZ = (FFT_FREQ_GHZ[FFT_POS_MASK] * 1000.0).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# COLUMN INFO
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


COMMON_COLUMN_INFO = [
    schema_entry("sample_id", "int32", False, "manual feature", "16", False, "Numeric sample identifier."),
    schema_entry("figure_id", "int32", False, "manual feature", "16", False, "Figure identifier."),
    schema_entry("configuration", "string", False, "CONFIGURATIONS key", "non_degenerate / degenerate", False, "TLS frequency configuration."),
    schema_entry("omega_tls_1_GHz", "float32", False, "omega_tls_1", "4.0 GHz", False, "TLS 1 transition frequency."),
    schema_entry("omega_tls_2_GHz", "float32", False, "omega_tls_2", "4.0 or 4.12 GHz", False, "TLS 2 transition frequency."),
    schema_entry("j_coupling_GHz", "float32", False, "J_COUPLING_GHZ", "0.01 GHz", False, "TLS-TLS coupling strength."),
    schema_entry("drive_amplitude_GHz", "float32", False, "DRIVE_AMPLITUDE_GHZ", "0.10 GHz", False, "Drive amplitude."),
    schema_entry("pulse_duration_ns", "float32", False, "PULSE_DURATION_NS", "100 ns", False, "Drive pulse duration."),
    schema_entry("total_time_ns", "float32", False, "TOTAL_TIME_NS", "800 ns", False, "Total simulation time."),
    schema_entry("time_step_ns", "float32", False, "DT_NS", "0.01 ns", False, "Simulation time step."),
    schema_entry("gamma_collective_ns_inv", "float32", False, "gamma_collective", "0.002 ns^-1", False, "Collective decay rate."),
    schema_entry("gamma_local_1_ns_inv", "float32", False, "gamma_local_1", "0.0001 ns^-1", False, "Local decay rate of TLS 1."),
    schema_entry("gamma_local_2_ns_inv", "float32", False, "gamma_local_2", "0.0005 ns^-1", False, "Local decay rate of TLS 2."),
    schema_entry("drive_frequency_GHz", "float32", False, "omega_d_vals", "3.0 to 5.0 GHz", False, "Swept drive frequency."),
]

TIME_COLUMN_INFO = COMMON_COLUMN_INFO + [
    schema_entry("time_ns", "float32", False, "tlist", "0 to 800 ns", False, "Simulation time."),
    schema_entry("collective_population", "float32", False, "pop_t", ">= 0", True, "Collective excitation expectation value."),
    schema_entry("phase_difference_rad", "float32", False, "phase", "-pi to pi", True, "Wrapped phase difference arg<sigma1+> - arg<sigma2+>."),
]

FFT_COLUMN_INFO = COMMON_COLUMN_INFO + [
    schema_entry("fft_window_start_ns", "float32", False, "FFT_WINDOW_START_NS", "0 ns", False, "FFT window start time."),
    schema_entry("fft_window_stop_ns", "float32", False, "FFT_WINDOW_STOP_NS", "300 ns", False, "FFT window stop time."),
    schema_entry("fft_frequency_MHz", "float32", False, "fft_freq_plot_MHz", "0 to 150 MHz", False, "Positive FFT frequency axis."),
    schema_entry("normalized_phase_fft", "float32", False, "fft_row", "0 to 1", False, "Normalized FFT magnitude of phase difference."),
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def save_pickle(df, path):
    df.to_pickle(path)
    size_mb = os.path.getsize(path) / (1024 ** 2)
    print(f"Saved: {path} ({size_mb:.2f} MB)")


def drive_coeff_factory(omega_d):
    def dcoeff(t, args=None):
        if t <= PULSE_DURATION_NS:
            return DRIVE_AMPLITUDE_GHZ * np.cos(omega_d * t)
        return 0.0

    return dcoeff


def simulate_two_tls(job):
    config_name, idx, omega_d, omega_1, omega_2 = job

    sx1 = tensor(sigmax(), qeye(2))
    sx2 = tensor(qeye(2), sigmax())
    sz1 = tensor(sigmaz(), qeye(2))
    sz2 = tensor(qeye(2), sigmaz())
    sp1 = tensor(sigmap(), qeye(2))
    sp2 = tensor(qeye(2), sigmap())
    sm1 = tensor(sigmam(), qeye(2))
    sm2 = tensor(qeye(2), sigmam())

    sp_tot = sp1 + sp2
    sm_tot = sm1 + sm2
    pop_op = sp_tot * sm_tot

    H0 = 0.5 * omega_1 * sz1 + 0.5 * omega_2 * sz2
    Hint = J_COUPLING_GHZ * sx1 * sx2
    Hstat = H0 + Hint
    Hfull = [Hstat, [sx1 + sx2, drive_coeff_factory(omega_d)]]

    c_ops = [
        np.sqrt(GAMMA_COLLECTIVE_NS_INV) * sm_tot,
        np.sqrt(GAMMA_LOCAL_1_NS_INV) * sm1,
        np.sqrt(GAMMA_LOCAL_2_NS_INV) * sm2,
    ]

    _, evecs = Hstat.eigenstates()
    psi0 = evecs[0]

    result = mesolve(
        Hfull,
        psi0,
        TLIST_NS,
        c_ops=c_ops,
        e_ops=[pop_op, sp1, sp2],
        options=Options(nsteps=5000, progress_bar=None),
    )

    pop_t = np.real(result.expect[0]).astype(np.float32)
    sp1_t = result.expect[1]
    sp2_t = result.expect[2]

    phase = (np.angle(sp1_t) - np.angle(sp2_t)).astype(np.float32)
    phase = ((phase + np.pi) % (2 * np.pi) - np.pi).astype(np.float32)

    phase_win = phase[FFT_TIME_MASK]
    fft_row = np.abs(fft(phase_win))[FFT_POS_MASK].astype(np.float32)

    if fft_row.max() > 1e-14:
        fft_row /= fft_row.max()

    return config_name, idx, pop_t, phase, fft_row


def build_time_df(config_name, omega_1, omega_2, pop_mat, phase_mat):
    n_drive, n_time = pop_mat.shape
    n_rows = n_drive * n_time

    return pd.DataFrame({
        "sample_id": np.full(n_rows, SAMPLE_ID, dtype=np.int32),
        "figure_id": np.full(n_rows, FIGURE_ID, dtype=np.int32),
        "configuration": np.full(n_rows, config_name, dtype=object),
        "omega_tls_1_GHz": np.full(n_rows, omega_1, dtype=np.float32),
        "omega_tls_2_GHz": np.full(n_rows, omega_2, dtype=np.float32),
        "j_coupling_GHz": np.full(n_rows, J_COUPLING_GHZ, dtype=np.float32),
        "drive_amplitude_GHz": np.full(n_rows, DRIVE_AMPLITUDE_GHZ, dtype=np.float32),
        "pulse_duration_ns": np.full(n_rows, PULSE_DURATION_NS, dtype=np.float32),
        "total_time_ns": np.full(n_rows, TOTAL_TIME_NS, dtype=np.float32),
        "time_step_ns": np.full(n_rows, DT_NS, dtype=np.float32),
        "gamma_collective_ns_inv": np.full(n_rows, GAMMA_COLLECTIVE_NS_INV, dtype=np.float32),
        "gamma_local_1_ns_inv": np.full(n_rows, GAMMA_LOCAL_1_NS_INV, dtype=np.float32),
        "gamma_local_2_ns_inv": np.full(n_rows, GAMMA_LOCAL_2_NS_INV, dtype=np.float32),
        "drive_frequency_GHz": np.repeat(DRIVE_FREQ_GHZ, n_time).astype(np.float32),
        "time_ns": np.tile(TLIST_NS, n_drive).astype(np.float32),
        "collective_population": pop_mat.reshape(-1).astype(np.float32),
        "phase_difference_rad": phase_mat.reshape(-1).astype(np.float32),
    })


def build_fft_df(config_name, omega_1, omega_2, fft_mat):
    n_drive, n_fft = fft_mat.shape
    n_rows = n_drive * n_fft

    return pd.DataFrame({
        "sample_id": np.full(n_rows, SAMPLE_ID, dtype=np.int32),
        "figure_id": np.full(n_rows, FIGURE_ID, dtype=np.int32),
        "configuration": np.full(n_rows, config_name, dtype=object),
        "omega_tls_1_GHz": np.full(n_rows, omega_1, dtype=np.float32),
        "omega_tls_2_GHz": np.full(n_rows, omega_2, dtype=np.float32),
        "j_coupling_GHz": np.full(n_rows, J_COUPLING_GHZ, dtype=np.float32),
        "drive_amplitude_GHz": np.full(n_rows, DRIVE_AMPLITUDE_GHZ, dtype=np.float32),
        "pulse_duration_ns": np.full(n_rows, PULSE_DURATION_NS, dtype=np.float32),
        "total_time_ns": np.full(n_rows, TOTAL_TIME_NS, dtype=np.float32),
        "time_step_ns": np.full(n_rows, DT_NS, dtype=np.float32),
        "gamma_collective_ns_inv": np.full(n_rows, GAMMA_COLLECTIVE_NS_INV, dtype=np.float32),
        "gamma_local_1_ns_inv": np.full(n_rows, GAMMA_LOCAL_1_NS_INV, dtype=np.float32),
        "gamma_local_2_ns_inv": np.full(n_rows, GAMMA_LOCAL_2_NS_INV, dtype=np.float32),
        "drive_frequency_GHz": np.repeat(DRIVE_FREQ_GHZ, n_fft).astype(np.float32),
        "fft_window_start_ns": np.full(n_rows, FFT_WINDOW_START_NS, dtype=np.float32),
        "fft_window_stop_ns": np.full(n_rows, FFT_WINDOW_STOP_NS, dtype=np.float32),
        "fft_frequency_MHz": np.tile(FFT_FREQ_MHZ, n_drive).astype(np.float32),
        "normalized_phase_fft": fft_mat.reshape(-1).astype(np.float32),
    })


def build_dataset(output_dir):
    os.makedirs(output_dir, exist_ok=True)

    time_blocks = []
    fft_blocks = []

    for config_name, cfg in CONFIGURATIONS.items():
        omega_1 = float(cfg["omega_tls_1_GHz"])
        omega_2 = float(cfg["omega_tls_2_GHz"])

        print(f"\nRunning configuration: {config_name} ({omega_1}, {omega_2}) GHz")

        pop_mat = np.empty((N_DRIVE, N_TIME), dtype=np.float32)
        phase_mat = np.empty((N_DRIVE, N_TIME), dtype=np.float32)
        fft_mat = np.empty((N_DRIVE, FFT_FREQ_MHZ.size), dtype=np.float32)

        jobs = [
            (config_name, i, float(omega_d), omega_1, omega_2)
            for i, omega_d in enumerate(DRIVE_FREQ_GHZ)
        ]

        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(simulate_two_tls, job): job[1] for job in jobs}

            for fut in tqdm(as_completed(futures), total=len(futures), desc=config_name):
                _, idx, pop_t, phase_t, fft_row = fut.result()
                pop_mat[idx, :] = pop_t
                phase_mat[idx, :] = phase_t
                fft_mat[idx, :] = fft_row

        time_blocks.append(build_time_df(config_name, omega_1, omega_2, pop_mat, phase_mat))
        fft_blocks.append(build_fft_df(config_name, omega_1, omega_2, fft_mat))

    time_df = pd.concat(time_blocks, ignore_index=True)
    fft_df = pd.concat(fft_blocks, ignore_index=True)

    save_pickle(time_df, os.path.join(output_dir, "figure16_time_domain.pkl"))
    save_pickle(fft_df, os.path.join(output_dir, "figure16_phase_fft.pkl"))

    save_json(TIME_COLUMN_INFO, os.path.join(output_dir, "figure16_time_domain_column_info.json"))
    save_json(FFT_COLUMN_INFO, os.path.join(output_dir, "figure16_phase_fft_column_info.json"))

    metadata = {
        "figure": 16,
        "sample_id": SAMPLE_ID,
        "description": "Numerical N=2 TLS degenerate vs non-degenerate comparison.",
        "configurations": CONFIGURATIONS,
        "j_coupling_GHz": J_COUPLING_GHZ,
        "drive_amplitude_GHz": DRIVE_AMPLITUDE_GHZ,
        "pulse_duration_ns": PULSE_DURATION_NS,
        "total_time_ns": TOTAL_TIME_NS,
        "time_step_ns": DT_NS,
        "n_time_samples": int(N_TIME),
        "drive_frequency_GHz_start": float(DRIVE_FREQ_GHZ[0]),
        "drive_frequency_GHz_stop": float(DRIVE_FREQ_GHZ[-1]),
        "n_drive_frequencies": int(N_DRIVE),
        "gamma_collective_ns_inv": GAMMA_COLLECTIVE_NS_INV,
        "gamma_local_1_ns_inv": GAMMA_LOCAL_1_NS_INV,
        "gamma_local_2_ns_inv": GAMMA_LOCAL_2_NS_INV,
        "fft_window_start_ns": FFT_WINDOW_START_NS,
        "fft_window_stop_ns": FFT_WINDOW_STOP_NS,
        "fft_view_MHz": FFT_VIEW_MHZ,
        "n_fft_frequencies": int(FFT_FREQ_MHZ.size),
        "outputs": {
            "time_domain": "figure16_time_domain.pkl",
            "phase_fft": "figure16_phase_fft.pkl",
            "time_domain_column_info": "figure16_time_domain_column_info.json",
            "phase_fft_column_info": "figure16_phase_fft_column_info.json",
        },
    }

    save_json(metadata, os.path.join(output_dir, "figure16_metadata.json"))

    print("\nDone.")
    print(f"Time-domain shape : {time_df.shape}")
    print(f"Phase FFT shape   : {fft_df.shape}")
    print(f"Output directory  : {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate clean Pickle datasets for Figure 16."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="dataset_fig16",
        help="Output directory.",
    )

    args = parser.parse_args()
    build_dataset(args.output_dir)