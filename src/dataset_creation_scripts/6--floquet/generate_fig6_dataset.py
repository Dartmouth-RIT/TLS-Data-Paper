"""
generate_fig6_dataset.py
========================
Organizes Figure 6 simulation outputs into interpretable Pickle dataframes.

Outputs:
    dataset_fig6/
        figure6_population_ringdown.pkl
        figure6_population_ringdown_column_info.json

        figure6_phase_fft.pkl
        figure6_phase_fft_column_info.json

        figure6_floquet_quasienergies.pkl
        figure6_floquet_quasienergies_column_info.json

        figure6_metadata.json
"""

import os
import json
import argparse
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
from tqdm import tqdm
from scipy.fft import fft, fftfreq
from qutip import (
    tensor,
    sigmax,
    qeye,
    sigmaz,
    sigmap,
    sigmam,
    mesolve,
    propagator,
)

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 6 PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_ID = 6
FIGURE_ID = 6

OMEGA_1 = 3.0
OMEGA_2 = 4.4
J_COUP = 0.05
DRIVE_AMP = 0.10
T_PULSE_NS = 100.0
T_TOTAL_NS = 400.0
DT_NS = 0.05
GAMMA_COL = 2e-3

FREQ_GRID_GHZ = np.linspace(3.0, 5.0, 400).astype(np.float32)

T_NS = np.arange(0.0, T_TOTAL_NS, DT_NS).astype(np.float32)
FFT_F_GHZ = fftfreq(T_NS.size, DT_NS).astype(np.float32)
FFT_MASK = (FFT_F_GHZ >= 0) & (FFT_F_GHZ <= 0.15)
FFT_POS_GHZ = FFT_F_GHZ[FFT_MASK].astype(np.float32)
FFT_POS_MHZ = (FFT_POS_GHZ * 1000.0).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def schema_entry(
    column_name,
    data_type,
    can_have_nulls,
    maps_to_original,
    value_or_range,
    in_raw_npy,
    derivation_or_notes,
):
    return {
        "column_name": column_name,
        "data_type": data_type,
        "can_have_nulls": can_have_nulls,
        "maps_to_original": maps_to_original,
        "value_or_range": value_or_range,
        "num_columns": 1,
        "in_raw_npy": in_raw_npy,
        "derivation_or_notes": derivation_or_notes,
    }


POP_COLUMN_INFO = [
    schema_entry(
        "sample_id",
        "int32",
        False,
        "manual feature",
        "6",
        False,
        "Numeric sample/figure identifier.",
    ),
    schema_entry(
        "figure_id", "int32", False, "manual feature", "6", False, "Figure identifier."
    ),
    schema_entry(
        "omega_1_GHz", "float32", False, "OMEGA_1", "3.0", False, "First TLS frequency."
    ),
    schema_entry(
        "omega_2_GHz",
        "float32",
        False,
        "OMEGA_2",
        "4.4",
        False,
        "Second TLS frequency.",
    ),
    schema_entry(
        "j_coupling_GHz",
        "float32",
        False,
        "J_COUP",
        "0.05",
        False,
        "TLS-TLS coupling strength.",
    ),
    schema_entry(
        "drive_amp_GHz",
        "float32",
        False,
        "DRIVE_AMP",
        "0.10",
        False,
        "Drive amplitude.",
    ),
    schema_entry(
        "gamma_collective_GHz",
        "float32",
        False,
        "GAMMA_COL",
        "0.002",
        False,
        "Collective decay rate.",
    ),
    schema_entry(
        "drive_frequency_GHz",
        "float32",
        False,
        "FREQ_GRID",
        "3.0 to 5.0",
        False,
        "Swept drive frequency.",
    ),
    schema_entry(
        "time_ns", "float32", False, "T_NS", "0 to 400 ns", False, "Simulation time."
    ),
    schema_entry(
        "population",
        "float32",
        False,
        "POP",
        ">= 0",
        False,
        "Expectation value <sigma+ sigma->.",
    ),
]

FFT_COLUMN_INFO = [
    *POP_COLUMN_INFO[:8],
    schema_entry(
        "fft_frequency_GHz",
        "float32",
        False,
        "FFT_POS",
        "0 to 0.15 GHz",
        False,
        "Positive FFT frequency.",
    ),
    schema_entry(
        "fft_frequency_MHz",
        "float32",
        False,
        "FFT_POS * 1000",
        "0 to 150 MHz",
        False,
        "Positive FFT frequency in MHz.",
    ),
    schema_entry(
        "normalized_phase_fft",
        "float32",
        False,
        "FFT_H",
        "0 to 1",
        False,
        "Normalized FFT magnitude of wrapped phase difference.",
    ),
]

QUASI_COLUMN_INFO = [
    *POP_COLUMN_INFO[:8],
    schema_entry(
        "quasi_branch",
        "int32",
        False,
        "QUASI column index",
        "0 to 3",
        False,
        "Floquet quasi-energy branch index.",
    ),
    schema_entry(
        "quasi_energy_GHz",
        "float32",
        True,
        "QUASI",
        "real or NaN",
        False,
        "Floquet quasi-energy in GHz.",
    ),
    schema_entry(
        "quasi_energy_MHz",
        "float32",
        True,
        "QUASI * 1000",
        "real or NaN",
        False,
        "Floquet quasi-energy in MHz.",
    ),
]


def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def save_pickle(df, path):
    df.to_pickle(path)
    print(f"Saved: {path} ({os.path.getsize(path) / 1024**2:.2f} MB)")


# ─────────────────────────────────────────────────────────────────────────────
# SIMULATION WORKER
# ─────────────────────────────────────────────────────────────────────────────


def worker(pair):
    idx, f_drive = pair

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

    h_static = 0.5 * OMEGA_1 * sz1 + 0.5 * OMEGA_2 * sz2 + J_COUP * sx1 * sx2

    psi0 = h_static.eigenstates()[1][0]
    cops = [np.sqrt(GAMMA_COL) * sm_tot]

    def drive_coeff(t, args):
        if t <= T_PULSE_NS:
            return DRIVE_AMP * np.cos(f_drive * t)
        return 0.0

    h_full = [h_static, [sx1 + sx2, drive_coeff]]

    res = mesolve(
        H=h_full,
        rho0=psi0,
        tlist=T_NS,
        c_ops=cops,
        e_ops=[pop_op, sp1, sp2],
        options={
            "progress_bar": None,
            "nsteps": 5000,
        },
    )

    pop_t, sp1_t, sp2_t = res.expect

    phase = np.angle(sp1_t) - np.angle(sp2_t)
    phase = ((phase + np.pi) % (2 * np.pi) - np.pi).astype(np.float32)

    fft_row = np.abs(fft(phase))[FFT_MASK].astype(np.float32)
    if fft_row.max() > 1e-14:
        fft_row /= fft_row.max()

    try:
        U = propagator(
            H=h_full,
            t=T_PULSE_NS,
            c_ops=[],
            options={
                "nsteps": 5000,
            },
        )
        phases = np.angle(np.linalg.eigvals(U.full()))
        quasi = np.sort(((phases + np.pi) % (2 * np.pi) - np.pi) / T_PULSE_NS).astype(
            np.float32
        )
    except Exception:
        quasi = np.full(4, np.nan, dtype=np.float32)

    return idx, pop_t.real.astype(np.float32), fft_row, quasi


# ─────────────────────────────────────────────────────────────────────────────
# DATAFRAME BUILDERS
# ─────────────────────────────────────────────────────────────────────────────


def build_population_df(pop):
    n_freq, n_time = pop.shape

    return pd.DataFrame(
        {
            "sample_id": np.full(n_freq * n_time, SAMPLE_ID, dtype=np.int32),
            "figure_id": np.full(n_freq * n_time, FIGURE_ID, dtype=np.int32),
            "omega_1_GHz": np.full(n_freq * n_time, OMEGA_1, dtype=np.float32),
            "omega_2_GHz": np.full(n_freq * n_time, OMEGA_2, dtype=np.float32),
            "j_coupling_GHz": np.full(n_freq * n_time, J_COUP, dtype=np.float32),
            "drive_amp_GHz": np.full(n_freq * n_time, DRIVE_AMP, dtype=np.float32),
            "gamma_collective_GHz": np.full(
                n_freq * n_time, GAMMA_COL, dtype=np.float32
            ),
            "drive_frequency_GHz": np.repeat(FREQ_GRID_GHZ, n_time),
            "time_ns": np.tile(T_NS, n_freq),
            "population": pop.reshape(-1).astype(np.float32),
        }
    )


def build_fft_df(fft_h):
    n_freq, n_fft = fft_h.shape

    return pd.DataFrame(
        {
            "sample_id": np.full(n_freq * n_fft, SAMPLE_ID, dtype=np.int32),
            "figure_id": np.full(n_freq * n_fft, FIGURE_ID, dtype=np.int32),
            "omega_1_GHz": np.full(n_freq * n_fft, OMEGA_1, dtype=np.float32),
            "omega_2_GHz": np.full(n_freq * n_fft, OMEGA_2, dtype=np.float32),
            "j_coupling_GHz": np.full(n_freq * n_fft, J_COUP, dtype=np.float32),
            "drive_amp_GHz": np.full(n_freq * n_fft, DRIVE_AMP, dtype=np.float32),
            "gamma_collective_GHz": np.full(
                n_freq * n_fft, GAMMA_COL, dtype=np.float32
            ),
            "drive_frequency_GHz": np.repeat(FREQ_GRID_GHZ, n_fft),
            "fft_frequency_GHz": np.tile(FFT_POS_GHZ, n_freq),
            "fft_frequency_MHz": np.tile(FFT_POS_MHZ, n_freq),
            "normalized_phase_fft": fft_h.reshape(-1).astype(np.float32),
        }
    )


def build_quasi_df(quasi):
    n_freq, n_branch = quasi.shape

    return pd.DataFrame(
        {
            "sample_id": np.full(n_freq * n_branch, SAMPLE_ID, dtype=np.int32),
            "figure_id": np.full(n_freq * n_branch, FIGURE_ID, dtype=np.int32),
            "omega_1_GHz": np.full(n_freq * n_branch, OMEGA_1, dtype=np.float32),
            "omega_2_GHz": np.full(n_freq * n_branch, OMEGA_2, dtype=np.float32),
            "j_coupling_GHz": np.full(n_freq * n_branch, J_COUP, dtype=np.float32),
            "drive_amp_GHz": np.full(n_freq * n_branch, DRIVE_AMP, dtype=np.float32),
            "gamma_collective_GHz": np.full(
                n_freq * n_branch, GAMMA_COL, dtype=np.float32
            ),
            "drive_frequency_GHz": np.repeat(FREQ_GRID_GHZ, n_branch),
            "quasi_branch": np.tile(np.arange(n_branch, dtype=np.int32), n_freq),
            "quasi_energy_GHz": quasi.reshape(-1).astype(np.float32),
            "quasi_energy_MHz": (quasi.reshape(-1) * 1000.0).astype(np.float32),
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────


def build_dataset(output_dir):
    os.makedirs(output_dir, exist_ok=True)

    pop = np.empty((FREQ_GRID_GHZ.size, T_NS.size), dtype=np.float32)
    fft_h = np.empty((FREQ_GRID_GHZ.size, FFT_POS_GHZ.size), dtype=np.float32)
    quasi = np.empty((FREQ_GRID_GHZ.size, 4), dtype=np.float32)

    with ProcessPoolExecutor(mp.cpu_count()) as pool:
        futures = [
            pool.submit(worker, (i, float(f))) for i, f in enumerate(FREQ_GRID_GHZ)
        ]

        for fut in tqdm(as_completed(futures), total=len(futures), desc="drive sweep"):
            i, p, f, q = fut.result()
            pop[i] = p
            fft_h[i] = f
            quasi[i] = q

    pop_df = build_population_df(pop)
    fft_df = build_fft_df(fft_h)
    quasi_df = build_quasi_df(quasi)

    save_pickle(pop_df, os.path.join(output_dir, "figure6_population_ringdown.pkl"))
    save_pickle(fft_df, os.path.join(output_dir, "figure6_phase_fft.pkl"))
    save_pickle(quasi_df, os.path.join(output_dir, "figure6_floquet_quasienergies.pkl"))

    save_json(
        POP_COLUMN_INFO,
        os.path.join(output_dir, "figure6_population_ringdown_column_info.json"),
    )
    save_json(
        FFT_COLUMN_INFO, os.path.join(output_dir, "figure6_phase_fft_column_info.json")
    )
    save_json(
        QUASI_COLUMN_INFO,
        os.path.join(output_dir, "figure6_floquet_quasienergies_column_info.json"),
    )

    metadata = {
        "figure": 6,
        "sample_id": SAMPLE_ID,
        "omega_1_GHz": OMEGA_1,
        "omega_2_GHz": OMEGA_2,
        "j_coupling_GHz": J_COUP,
        "drive_amp_GHz": DRIVE_AMP,
        "t_pulse_ns": T_PULSE_NS,
        "t_total_ns": T_TOTAL_NS,
        "dt_ns": DT_NS,
        "gamma_collective_GHz": GAMMA_COL,
        "drive_frequency_GHz_start": float(FREQ_GRID_GHZ[0]),
        "drive_frequency_GHz_stop": float(FREQ_GRID_GHZ[-1]),
        "n_drive_frequencies": int(FREQ_GRID_GHZ.size),
        "n_time_samples": int(T_NS.size),
        "n_fft_samples": int(FFT_POS_GHZ.size),
        "n_quasi_branches": 4,
        "outputs": [
            "figure6_population_ringdown.pkl",
            "figure6_phase_fft.pkl",
            "figure6_floquet_quasienergies.pkl",
        ],
    }

    save_json(metadata, os.path.join(output_dir, "figure6_metadata.json"))

    print("\nDone.")
    print(f"Population shape : {pop_df.shape}")
    print(f"Phase FFT shape  : {fft_df.shape}")
    print(f"Quasi shape      : {quasi_df.shape}")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    parser = argparse.ArgumentParser(
        description="Generate clean Pickle datasets for Figure 6."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="dataset_fig6",
        help="Output directory.",
    )

    args = parser.parse_args()
    build_dataset(args.output_dir)
