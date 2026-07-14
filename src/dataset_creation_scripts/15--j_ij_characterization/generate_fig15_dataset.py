"""
generate_fig15_dataset.py
=========================
Create clean Pickle datasets for Figure 15 interaction-strength scan.

Outputs:
    dataset_fig15/
        figure15_time_domain.pkl
        figure15_time_domain_column_info.json

        figure15_fft_domain.pkl
        figure15_fft_domain_column_info.json

        figure15_tls_frequencies.pkl
        figure15_tls_frequencies_column_info.json

        figure15_metadata.json
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

from src.dataset_creation_scripts.figure15.hamiltonian_generator import (
    run_simulation_single_pulse_full,
    build_spin_spin_interactions_random_distribution,
)


SAMPLE_ID = 15
FIGURE_ID = 15

PULSE_NS = 400.0
AFTER_PULSE_ONLY = False

T_MAX_NS = 1600.0
N_T = 1000
TLIST_NS = np.linspace(0, T_MAX_NS, N_T).astype(np.float32)

F_MIN_GHZ = 3.0
F_MAX_GHZ = 5.0
N_DRIVE_FREQS = 300
FREQ_AXIS_GHZ = np.linspace(F_MIN_GHZ, F_MAX_GHZ, N_DRIVE_FREQS).astype(np.float32)

N_TLS = 4
RANDOM_SEED = 42

GAMMA = 0.001
GAMMA_PHI = 0.0
AMP_DRIVE = 0.01
T_RAMP_NS = 1.0

J_LEVELS = {
    "Low J": 0.005,
    "Mid J": 0.05,
    "High J": 0.5,
}

FFT_VIEW_MHZ = 100.0
MAX_WORKERS = 70


def schema_entry(column_name, data_type, can_have_nulls, maps_to_original,
                 value_or_range, in_raw_simulation, derivation_or_notes):
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


TIME_COLUMN_INFO = [
    schema_entry("sample_id", "int32", False, "manual feature", "15", False, "Numeric sample identifier."),
    schema_entry("figure_id", "int32", False, "manual feature", "15", False, "Figure identifier."),
    schema_entry("j_label", "string", False, "J_LEVELS key", "Low J, Mid J, High J", False, "Interaction-strength category."),
    schema_entry("j_coupling_GHz", "float32", False, "J_LEVELS value", "0.005, 0.05, 0.5", False, "All-to-all coupling scale."),
    schema_entry("n_tls", "int32", False, "N_TLS", "4", False, "Number of TLS defects."),
    schema_entry("drive_amp_GHz", "float32", False, "AMP_DRIVE", "0.01", False, "Drive amplitude."),
    schema_entry("gamma_collective_GHz", "float32", False, "GAMMA", "0.001", False, "Collective decay rate."),
    schema_entry("gamma_phi_GHz", "float32", False, "GAMMA_PHI", "0.0", False, "Pure dephasing rate."),
    schema_entry("pulse_duration_ns", "float32", False, "PULSE_NS", "400 ns", False, "Single-pulse duration."),
    schema_entry("t_ramp_ns", "float32", False, "T_RAMP_NS", "1 ns", False, "Pulse ramp duration."),
    schema_entry("drive_frequency_GHz", "float32", False, "FREQ_AXIS", "3.0 to 5.0 GHz", False, "Swept drive frequency."),
    schema_entry("time_ns", "float32", False, "tlist", "0 to 1600 ns", False, "Simulation time."),
    schema_entry("time_us", "float32", False, "time_ns / 1000", "0 to 1.6 us", False, "Simulation time in microseconds."),
    schema_entry("population", "float32", False, "pop_mat", ">= 0", True, "Expectation value <S+S->."),
    schema_entry("phase_rad", "float32", False, "angle(Sp)", "[-pi, pi]", True, "Wrapped homodyne-like collective phase."),
]

FFT_COLUMN_INFO = [
    *TIME_COLUMN_INFO[:11],
    schema_entry("fft_frequency_MHz", "float32", False, "np.fft.rfftfreq", "0 to 100 MHz", False, "FFT frequency axis."),
    schema_entry("log10_fft_population", "float32", False, "log10(abs(rfft(population)) + 1e-12)", "real", False, "Log FFT magnitude of population."),
    schema_entry("log10_fft_phase", "float32", False, "log10(abs(rfft(phase)) + 1e-12)", "real", False, "Log FFT magnitude of phase."),
]

TLS_FREQ_COLUMN_INFO = [
    schema_entry("sample_id", "int32", False, "manual feature", "15", False, "Numeric sample identifier."),
    schema_entry("figure_id", "int32", False, "manual feature", "15", False, "Figure identifier."),
    schema_entry("tls_index", "int32", False, "base_freqs index", "0 to 3", False, "TLS index."),
    schema_entry("tls_frequency_GHz", "float32", False, "base_freqs", "3.0 to 5.0 GHz", False, "Randomly generated TLS bare frequency."),
]


def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def save_pickle(df, path):
    df.to_pickle(path)
    print(f"Saved: {path} ({os.path.getsize(path) / 1024**2:.2f} MB)")


def worker(args):
    freq, amp_drive, tlist, base_freqs, H_int, gamma, gamma_phi, pulse_ns, t_ramp_ns = args
    pop, Sp, Sm = run_simulation_single_pulse_full(
        freq,
        amp_drive,
        tlist,
        base_freqs,
        H_int,
        gamma,
        gamma_phi,
        pulse_ns,
        t_ramp_ns,
    )

    phase = np.angle(Sp).astype(np.float32)
    phase = ((phase + np.pi) % (2 * np.pi) - np.pi).astype(np.float32)

    return np.real_if_close(pop).astype(np.float32), phase


def build_time_df(j_label, j_val, pop_mat, phi_mat):
    n_t, n_f = pop_mat.shape
    n_rows = n_t * n_f

    time_ns = np.repeat(TLIST_NS, n_f).astype(np.float32)
    drive_freq = np.tile(FREQ_AXIS_GHZ, n_t).astype(np.float32)

    return pd.DataFrame({
        "sample_id": np.full(n_rows, SAMPLE_ID, dtype=np.int32),
        "figure_id": np.full(n_rows, FIGURE_ID, dtype=np.int32),
        "j_label": np.full(n_rows, j_label, dtype=object),
        "j_coupling_GHz": np.full(n_rows, j_val, dtype=np.float32),
        "n_tls": np.full(n_rows, N_TLS, dtype=np.int32),
        "drive_amp_GHz": np.full(n_rows, AMP_DRIVE, dtype=np.float32),
        "gamma_collective_GHz": np.full(n_rows, GAMMA, dtype=np.float32),
        "gamma_phi_GHz": np.full(n_rows, GAMMA_PHI, dtype=np.float32),
        "pulse_duration_ns": np.full(n_rows, PULSE_NS, dtype=np.float32),
        "t_ramp_ns": np.full(n_rows, T_RAMP_NS, dtype=np.float32),
        "drive_frequency_GHz": drive_freq,
        "time_ns": time_ns,
        "time_us": time_ns / np.float32(1000.0),
        "population": pop_mat.reshape(-1).astype(np.float32),
        "phase_rad": phi_mat.reshape(-1).astype(np.float32),
    })


def build_fft_df(j_label, j_val, pop_mat, phi_mat):
    mask_tail = (TLIST_NS > PULSE_NS) if AFTER_PULSE_ONLY else np.ones_like(TLIST_NS, dtype=bool)
    tail_t = TLIST_NS[mask_tail]

    fft_freq_mhz = (
        np.fft.rfftfreq(len(tail_t), d=float(TLIST_NS[1] - TLIST_NS[0])) * 1e3
    ).astype(np.float32)

    keep_idx = fft_freq_mhz <= FFT_VIEW_MHZ
    fft_freq = fft_freq_mhz[keep_idx].astype(np.float32)

    fft_pop = np.log10(
        np.abs(np.fft.rfft(pop_mat[mask_tail, :], axis=0)[keep_idx, :]) + 1e-12
    ).astype(np.float32)

    fft_phi = np.log10(
        np.abs(np.fft.rfft(phi_mat[mask_tail, :], axis=0)[keep_idx, :]) + 1e-12
    ).astype(np.float32)

    n_fft, n_f = fft_pop.shape
    n_rows = n_fft * n_f

    return pd.DataFrame({
        "sample_id": np.full(n_rows, SAMPLE_ID, dtype=np.int32),
        "figure_id": np.full(n_rows, FIGURE_ID, dtype=np.int32),
        "j_label": np.full(n_rows, j_label, dtype=object),
        "j_coupling_GHz": np.full(n_rows, j_val, dtype=np.float32),
        "n_tls": np.full(n_rows, N_TLS, dtype=np.int32),
        "drive_amp_GHz": np.full(n_rows, AMP_DRIVE, dtype=np.float32),
        "gamma_collective_GHz": np.full(n_rows, GAMMA, dtype=np.float32),
        "gamma_phi_GHz": np.full(n_rows, GAMMA_PHI, dtype=np.float32),
        "pulse_duration_ns": np.full(n_rows, PULSE_NS, dtype=np.float32),
        "t_ramp_ns": np.full(n_rows, T_RAMP_NS, dtype=np.float32),
        "drive_frequency_GHz": np.tile(FREQ_AXIS_GHZ, n_fft).astype(np.float32),
        "fft_frequency_MHz": np.repeat(fft_freq, n_f).astype(np.float32),
        "log10_fft_population": fft_pop.reshape(-1).astype(np.float32),
        "log10_fft_phase": fft_phi.reshape(-1).astype(np.float32),
    })


def build_tls_freq_df(base_freqs):
    return pd.DataFrame({
        "sample_id": np.full(N_TLS, SAMPLE_ID, dtype=np.int32),
        "figure_id": np.full(N_TLS, FIGURE_ID, dtype=np.int32),
        "tls_index": np.arange(N_TLS, dtype=np.int32),
        "tls_frequency_GHz": np.asarray(base_freqs, dtype=np.float32),
    })


def build_dataset(output_dir):
    os.makedirs(output_dir, exist_ok=True)

    np.random.seed(RANDOM_SEED)
    base_freqs = np.random.uniform(F_MIN_GHZ, F_MAX_GHZ, N_TLS).astype(np.float32)

    time_blocks = []
    fft_blocks = []

    for j_label, j_val in J_LEVELS.items():
        print(f"\nRunning {j_label}: J={j_val}")

        H_int = build_spin_spin_interactions_random_distribution(
            N_TLS,
            j_val,
            j_val,
            alpha_x=1.0,
            alpha_y=0.0,
            alpha_z=0.0,
        )

        pop_mat = np.empty((N_T, len(FREQ_AXIS_GHZ)), dtype=np.float32)
        phi_mat = np.empty_like(pop_mat)

        jobs = [
            (
                float(f_drv),
                AMP_DRIVE,
                TLIST_NS,
                base_freqs,
                H_int,
                GAMMA,
                GAMMA_PHI,
                PULSE_NS,
                T_RAMP_NS,
            )
            for f_drv in FREQ_AXIS_GHZ
        ]

        with ProcessPoolExecutor(min(MAX_WORKERS, len(FREQ_AXIS_GHZ))) as pool:
            futures = {pool.submit(worker, job): idx for idx, job in enumerate(jobs)}

            for fut in tqdm(as_completed(futures), total=len(futures), desc=j_label):
                idx = futures[fut]
                pop, phase = fut.result()
                pop_mat[:, idx] = pop
                phi_mat[:, idx] = phase

        phi_mat = np.nan_to_num(phi_mat).astype(np.float32)

        time_blocks.append(build_time_df(j_label, j_val, pop_mat, phi_mat))
        fft_blocks.append(build_fft_df(j_label, j_val, pop_mat, phi_mat))

    time_df = pd.concat(time_blocks, ignore_index=True)
    fft_df = pd.concat(fft_blocks, ignore_index=True)
    tls_df = build_tls_freq_df(base_freqs)

    save_pickle(time_df, os.path.join(output_dir, "figure15_time_domain.pkl"))
    save_pickle(fft_df, os.path.join(output_dir, "figure15_fft_domain.pkl"))
    save_pickle(tls_df, os.path.join(output_dir, "figure15_tls_frequencies.pkl"))

    save_json(TIME_COLUMN_INFO, os.path.join(output_dir, "figure15_time_domain_column_info.json"))
    save_json(FFT_COLUMN_INFO, os.path.join(output_dir, "figure15_fft_domain_column_info.json"))
    save_json(TLS_FREQ_COLUMN_INFO, os.path.join(output_dir, "figure15_tls_frequencies_column_info.json"))

    metadata = {
        "figure": 15,
        "sample_id": SAMPLE_ID,
        "description": "Interaction-strength scan organized into interpretable Pickle dataframes.",
        "pulse_duration_ns": PULSE_NS,
        "after_pulse_only_fft": AFTER_PULSE_ONLY,
        "t_max_ns": T_MAX_NS,
        "n_time_samples": N_T,
        "drive_frequency_GHz_start": F_MIN_GHZ,
        "drive_frequency_GHz_stop": F_MAX_GHZ,
        "n_drive_frequencies": N_DRIVE_FREQS,
        "n_tls": N_TLS,
        "random_seed": RANDOM_SEED,
        "base_freqs_GHz": base_freqs.astype(float).tolist(),
        "gamma_collective_GHz": GAMMA,
        "gamma_phi_GHz": GAMMA_PHI,
        "drive_amp_GHz": AMP_DRIVE,
        "t_ramp_ns": T_RAMP_NS,
        "j_levels": J_LEVELS,
        "fft_view_MHz": FFT_VIEW_MHZ,
        "outputs": {
            "time_domain": "figure15_time_domain.pkl",
            "fft_domain": "figure15_fft_domain.pkl",
            "tls_frequencies": "figure15_tls_frequencies.pkl",
        },
    }

    save_json(metadata, os.path.join(output_dir, "figure15_metadata.json"))

    print("\nDone.")
    print(f"Time-domain shape : {time_df.shape}")
    print(f"FFT-domain shape  : {fft_df.shape}")
    print(f"TLS freq shape    : {tls_df.shape}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate clean Pickle datasets for Figure 15."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="dataset_fig15",
        help="Output directory.",
    )

    args = parser.parse_args()
    build_dataset(args.output_dir)