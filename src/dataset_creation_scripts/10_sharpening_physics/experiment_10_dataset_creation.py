"""
experiment_10_dataset_creation.py
=================================
Runs the Experiment 10 simulation, catches the arrays it produces, and writes
them out as three long-format tables (a pickle and a CSV each), plus a shared
metadata.json and column_info.json.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT — THE MODEL IS UNCOUPLED (a faithfully reproduced quirk)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The physics module builds an XX coupling operator (J = 0.05) but, inside the
solver, replaces it with `sum(interactions[i, j] for i in range(N) for j in
range(i))`. For the N = 2 system that expression evaluates to EXACTLY 0 (the
[1,0] matrix element of the XX operator is zero), so the coupling is silently
discarded and the two TLS evolve INDEPENDENTLY. This is almost certainly an
unintended quirk of the original implementation, and this dataset reproduces it
deliberately and unchanged. If you need the coupled system, that is a different
(new-physics) dataset — do not assume this one is coupled. See metadata.json ->
model.coupling_note.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAIN-LANGUAGE PRIMER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT THIS IS — A SIMULATION, NOT A MEASUREMENT
    Like Experiments 8 and 9, this is produced entirely on a computer. There is
    no instrument, no I and no Q. Two TWO-LEVEL SYSTEMS (TLS, tiny quantum
    switches) at 4.0 and 4.1 GHz are driven by a microwave pulse and left to ring
    down under a Lindblad master equation (QuTiP mesolve). Because the coupling
    vanishes (see above), they ring down independently and their signals beat
    against each other at their frequency difference (~0.1 GHz).

WHAT THIS PARTICULAR EXPERIMENT STUDIES — "sharpening"
    How the ring-down and the phase relationship between the two TLS SHARPEN as
    the drive pulse gets longer. Three products come out of one frequency sweep,
    repeated over a grid of pulse durations:

    (1) POST-PULSE MAP.  For every pulse duration (20-200 ns, 50 values) and
        every drive frequency (3.0-5.0 GHz, 400 values), the collective
        excitation <sigma+ sigma-> sampled at the FIRST time sample after the
        pulse ends. One scalar per (pulse, frequency): a 50 x 400 map.

    (2) POPULATION TRACES.  For three representative pulses (shortest, middle,
        longest), the FULL <sigma+ sigma-> time trace at every drive frequency.

    (3) PHASE-V FFT.  For the same three pulses, the normalized magnitude FFT of
        the phase difference phi(t) = arg<sigma+_1> - arg<sigma+_2> over the
        0-400 ns window, per drive frequency. This is the "phase V" that reveals
        the beat structure. Frequencies shown up to 150 MHz.

THE OBSERVABLES
    population  = <sigma+ sigma->   (collective excitation, dimensionless, >= 0)
    phi(t)      = arg<sigma+_1> - arg<sigma+_2>, wrapped to (-pi, pi]
    Only these are stored (and, for product 3, the normalized FFT magnitude of
    phi). They are computed by the solver, not measured.

UNIT CONVENTION  (inherited from the model)
    Frequencies used numerically as inverse nanoseconds (GHz == ns^-1), NO 2*pi.
    Amplitude dimensionless; phase in radians; time in nanoseconds; FFT axis in
    MHz.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT  (three long-format tables)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    10_sharpening_physics/experiment_10/experiment_10_postpulse_map.pkl / .csv
        cols: pulse_duration_ns, drive_frequency_GHz, postpulse_population
        rows: 50 pulses x 400 freqs                        = 20,000

    10_sharpening_physics/experiment_10/experiment_10_population_traces.pkl / .csv
        cols: pulse_duration_ns, drive_frequency_GHz, timestamp_ns, population
        rows: 3 pulses x 400 freqs x 1000 time             = 1,200,000

    10_sharpening_physics/experiment_10/experiment_10_phaseV_fft.pkl / .csv
        cols: pulse_duration_ns, drive_frequency_GHz, fft_frequency_MHz,
              normalized_phase_fft
        rows: 3 pulses x 400 freqs x Nf   (Nf ~ 60; set by the 0-400 ns window)

    10_sharpening_physics/experiment_10/experiment_10_run.log   (reverification log)
    10_sharpening_physics/metadata.json
    10_sharpening_physics/column_info.json

Each pickle holds a self-contained payload:
    payload["data"]        the table array (float32)
    payload["columns"]     that table's column names
    payload["table"]       the table name
    payload["attrs"]       shared experiment metadata (mirrors metadata.json)
    payload["column_doc"]  that table's column semantics

To load one table in Python:

    import pickle, pandas as pd
    with open("experiment_10_postpulse_map.pkl", "rb") as fh:
        payload = pickle.load(fh)
    df = pd.DataFrame(payload["data"], columns=payload["columns"])

PROVENANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    physics module : hamiltonian_generator.py  (local; only a QuTiP-5 API
                     compatibility shim differs — see that file)
    All knobs below are fixed and deterministic, including the coupling that the
    solver silently drops (reproduced, not fixed).
    Uses code and simulation methods from the Fitzpatrick Lab, Dartmouth College.

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # full run (needs qutip; HEAVY -- 50 x 400 = 20,000 solves)
    python experiment_10_dataset_creation.py --workers 16

    # fast plumbing check (no qutip: synthetic arrays on tiny grids)
    python experiment_10_dataset_creation.py --smoke-test

    Optional arguments:
        --output_dir  where to write experiment_10/ (default: next to this script)
        --workers     parallel solver processes (default: 4; ignored in smoke test)
        --no_csv      skip the CSVs (pickles only)
        --smoke-test  shrink grids + use synthetic arrays (no qutip needed)
"""

import os
import sys
import json
import pickle
import argparse
import datetime
import numpy as np
from tqdm import tqdm

# ─────────────────────────────────────────────────────────────────────────────
# SIMULATION KNOBS — the fixed parameters that define this experiment.
# ─────────────────────────────────────────────────────────────────────────────

# Pulse-duration grid (nanoseconds) and the three "representative" pulses.
PULSE_MIN_NS, PULSE_MAX_NS = 20.0, 200.0
N_PULSES = 50

# Drive-frequency sweep. Treated numerically as GHz == ns^-1.
F_MIN, F_MAX = 3.0, 5.0
N_FREQ       = 400

# Time grid: 0 to 1000 ns, 1000 points.
T_MAX_NS, N_T = 1000, 1000

# The N = 2 TLS. Frequencies hard-coded; coupling is built (J=0.05 XX) but the
# source solver DROPS it -> the TLS are effectively uncoupled (see header).
N_TLS      = 2
INIT_FREQS = [4.0, 4.1]
J_COUP     = 0.05

# Dissipation and drive amplitude.
GAMMA, GAMMA_PHI = 0.002, 0.0
DRIVE_AMPL       = 0.1

# Phase-V FFT settings.
FFT_VIEW_MHZ       = 150.0
PHASEV_WIN_START_NS = 0.0
PHASEV_WIN_STOP_NS  = 400.0

# ── table schemas ────────────────────────────────────────────────────────────
POSTPULSE_COLUMNS  = ["pulse_duration_ns", "drive_frequency_GHz",
                      "postpulse_population"]
POPTRACE_COLUMNS   = ["pulse_duration_ns", "drive_frequency_GHz",
                      "timestamp_ns", "population"]
PHASEV_COLUMNS     = ["pulse_duration_ns", "drive_frequency_GHz",
                      "fft_frequency_MHz", "normalized_phase_fft"]

PICKLE_PROTOCOL = 4


def top_pulse_indices(pulses):
    """The three representative pulses: first, middle, last."""
    return [0, len(pulses) // 2, len(pulses) - 1]


# ─────────────────────────────────────────────────────────────────────────────
# ENSEMBLE
# ─────────────────────────────────────────────────────────────────────────────

def build_H_int():
    """Build the (nominal) XX coupling operator.
    NOTE: the solver discards this operator (see the UNCOUPLED note in the module
    docstring); it is built here only so the real solver path receives the same
    arguments as the original implementation."""
    from hamiltonian_generator import build_spin_spin_interactions_random_distribution
    return build_spin_spin_interactions_random_distribution(
        N_TLS, J_COUP, J_COUP, alpha_x=1.0, alpha_y=0.0, alpha_z=0.0
    )


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC ARRAYS — smoke-test stand-in for the QuTiP solver (no physics).
# ─────────────────────────────────────────────────────────────────────────────

def _synthetic_full(freq, amp, tlist, init_freqs, pulse_ns):
    """Return (sp1, sp2, pop) surrogates. NOT physical; plumbing only."""
    detune = np.min(np.abs(np.asarray(init_freqs) - freq))
    lorentz = 1.0 / (1.0 + (detune / 0.15) ** 2)
    drive = amp * lorentz * np.sin(
        np.pi * np.clip(tlist / max(pulse_ns, 1e-9), 0, 1)) ** 2
    tail = np.where(tlist > pulse_ns,
                    amp * lorentz * np.exp(-GAMMA * (tlist - pulse_ns)), 0.0)
    pop = np.clip(np.where(tlist <= pulse_ns, drive, tail), 0.0, None)
    env = np.exp(-GAMMA * tlist)
    sp1 = amp * env * np.exp(1j * init_freqs[0] * tlist * 0.05)
    sp2 = amp * env * np.exp(1j * init_freqs[1] * tlist * 0.05)
    return sp1, sp2, pop.astype(np.float64)


# ─────────────────────────────────────────────────────────────────────────────
# PARALLEL WORKER (real run) — one solve per (pulse, frequency)
# ─────────────────────────────────────────────────────────────────────────────

_G = {}


def _init_worker(tlist, init_freqs, H_int, gamma, gamma_phi, amp):
    """Runs once per worker process: stash the constants + the physics function
    so each task only ships (freq, pulse_ns, j_post, want_full)."""
    global _G
    from hamiltonian_generator import run_simulation_for_frequency
    _G = dict(tlist=tlist, init_freqs=init_freqs, H_int=H_int, gamma=gamma,
              gamma_phi=gamma_phi, amp=amp, fn=run_simulation_for_frequency)


def _worker(task):
    """Return (postpulse_scalar, sp1, sp2, pop) — sp1/sp2/pop only when want_full,
    to keep inter-process traffic small for the non-representative pulses."""
    freq, pulse_ns, j_post, want_full = task
    sp1, sp2, pop = _G["fn"](freq, _G["tlist"], _G["init_freqs"], _G["H_int"],
                             _G["gamma"], _G["gamma_phi"], _G["amp"], pulse_ns)
    pop = np.asarray(pop, dtype=np.float64).real
    scalar = float(pop[j_post])
    if want_full:
        return scalar, np.asarray(sp1), np.asarray(sp2), pop.astype(np.float32)
    return scalar, None, None, None


def first_index_after(tlist, tau_ns):
    """First index j with tlist[j] > tau_ns."""
    j = int(np.searchsorted(tlist, tau_ns, side="right"))
    if j >= len(tlist):
        raise ValueError(f"Pulse {tau_ns} ns exceeds the {tlist[-1]} ns window.")
    return j


def compute_phaseV(phi_buffer, tlist, dt):
    """Compute the phase-V: FFT phi over the 0-400 ns window, keep positive freqs
    up to FFT_VIEW_MHZ, normalize row-wise (per drive freq).
    Returns (mag_norm (N_FREQ, Nf), fft_freq_MHz (Nf,))."""
    tmask = (tlist >= PHASEV_WIN_START_NS) & (tlist <= PHASEV_WIN_STOP_NS)
    if tmask.sum() < 2:
        raise ValueError(f"Phase-V window too small: {tmask.sum()} points.")
    freqs_GHz = np.fft.fftfreq(int(tmask.sum()), dt)
    pos = (freqs_GHz >= 0.0) & (freqs_GHz <= FFT_VIEW_MHZ / 1e3)
    fft_freq_MHz = (freqs_GHz[pos] * 1e3).astype(np.float32)

    phi_win = phi_buffer[:, tmask]
    PhiFFT = np.fft.fft(phi_win, axis=1)[:, pos]
    mag = np.abs(PhiFFT).astype(np.float32)
    den = mag.max(axis=1, keepdims=True)
    mag_norm = np.divide(mag, den, out=np.zeros_like(mag), where=den > 1e-14)
    return mag_norm, fft_freq_MHz


# ─────────────────────────────────────────────────────────────────────────────
# METADATA
# ─────────────────────────────────────────────────────────────────────────────

def build_metadata(pulses, top_idx, freq_axis, tlist, fft_freq_MHz,
                   smoke_test=False) -> dict:
    return {
        "experiment_id": "experiment_10",
        "title": "Ring-down & Phase Sharpening vs Pulse Duration (N=2 TLS simulation)",
        "data_type": "simulation",
        "description": (
            "Numerical BCTDS study of how the ring-down and the inter-TLS phase "
            "relationship sharpen with drive-pulse duration, for two TLS at 4.0 "
            "and 4.1 GHz under a Lindblad master equation (QuTiP mesolve). One "
            "drive-frequency sweep is repeated over a grid of pulse durations, "
            "yielding three products: a post-pulse population map, full population "
            "traces for three representative pulses, and the normalized FFT of the "
            "inter-TLS phase difference (the 'phase V'). Observables are computed "
            "by the solver, not measured. The model is imported from the local "
            "hamiltonian_generator.py (QuTiP-5 API shim only)."
        ),
        "model": {
            "system": f"{N_TLS} two-level systems (TLS) at {INIT_FREQS} GHz",
            "equation_of_motion": "Lindblad master equation",
            "solver": "QuTiP mesolve",
            "coupling_note": (
                "An XX coupling (J=0.05) is built but the solver replaces it with "
                "sum(interactions[i,j] for i in range(N) for j in range(i)), which "
                "for N=2 equals EXACTLY 0. The TLS therefore evolve INDEPENDENTLY "
                "(uncoupled). This is reproduced deliberately and unchanged; it is "
                "almost certainly an unintended quirk of the original "
                "implementation. Do NOT treat this dataset as a coupled system."
            ),
            "observables": {
                "population": "<sigma+ sigma-> collective excitation (dimensionless)",
                "phase_difference": "phi(t) = arg<sigma+_1> - arg<sigma+_2>, "
                                    "wrapped to (-pi, pi]",
            },
            "drive": "square pulse, amp*cos(freq*t) for t <= pulse_ns (no ramp), "
                     "per the active drive definition",
            "unit_convention": (
                "Frequencies used numerically as inverse nanoseconds (GHz == ns^-1) "
                "with NO factor of 2*pi. Amplitude dimensionless; phase in radians; "
                "time in ns; FFT axis in MHz."
            ),
        },
        "constants": {
            "n_tls": N_TLS,
            "tls_frequencies_GHz": list(INIT_FREQS),
            "nominal_coupling_J_GHz": J_COUP,
            "gamma_collective": GAMMA,
            "gamma_dephasing": GAMMA_PHI,
            "drive_amplitude": DRIVE_AMPL,
        },
        "grids": {
            "pulse_durations_ns": {
                "n": len(pulses), "min": float(pulses[0]), "max": float(pulses[-1]),
                "formula": "linspace(20, 200, 50)",
            },
            "representative_pulses_ns": [round(float(pulses[i]), 4) for i in top_idx],
            "drive_frequency_GHz": {
                "n": len(freq_axis), "range": [F_MIN, F_MAX],
                "formula": "linspace(3.0, 5.0, 400)",
            },
            "time_grid": {
                "t_min_ns": 0.0, "t_max_ns": T_MAX_NS, "n_samples": len(tlist),
                "one_sample_ns": float(tlist[1] - tlist[0]) if len(tlist) > 1 else 0.0,
            },
            "phaseV": {
                "window_ns": [PHASEV_WIN_START_NS, PHASEV_WIN_STOP_NS],
                "fft_view_MHz": FFT_VIEW_MHZ,
                "n_fft_bins": int(len(fft_freq_MHz)),
                "normalization": "row-wise (per drive frequency) to peak = 1",
            },
        },
        "tables": {
            "postpulse_map": {"columns": POSTPULSE_COLUMNS,
                              "n_rows": len(pulses) * len(freq_axis)},
            "population_traces": {"columns": POPTRACE_COLUMNS,
                                  "n_rows": len(top_idx) * len(freq_axis) * len(tlist)},
            "phaseV_fft": {"columns": PHASEV_COLUMNS,
                           "n_rows": len(top_idx) * len(freq_axis) * len(fft_freq_MHz)},
        },
        "provenance": {
            "physics_module": "hamiltonian_generator.py (QuTiP-5 API shim only)",
            "attribution": "Uses code and simulation methods from the "
                           "Fitzpatrick Lab, Dartmouth College.",
            "no_new_physics": True,
            "reproduces_uncoupled_quirk": True,
            "smoke_test": smoke_test,
        },
    }


def build_column_info(pulses, top_idx, freq_axis, tlist, fft_freq_MHz) -> dict:
    return {
        "dataset": "experiment_10_sharpening_physics",
        "format": "three long-format tables (see 'tables')",
        "note": "Uncoupled N=2 TLS (source quirk reproduced). See metadata.json.",
        "tables": {
            "postpulse_map": {
                "format": "long (one row per pulse x drive frequency)",
                "n_rows": len(pulses) * len(freq_axis),
                "columns": [
                    {"name": "pulse_duration_ns", "dtype": "float32", "unit": "ns",
                     "role": "coordinate", "description": "Drive pulse duration "
                     "(20-200 ns, 50 values)."},
                    {"name": "drive_frequency_GHz", "dtype": "float32",
                     "unit": "GHz (== ns^-1)", "role": "coordinate",
                     "description": "Drive frequency (3.0-5.0 GHz, 400 values)."},
                    {"name": "postpulse_population", "dtype": "float32",
                     "unit": "dimensionless", "role": "observable",
                     "description": "<sigma+ sigma-> sampled at the first time "
                     "sample after the pulse ends (first t > pulse_duration_ns)."},
                ],
            },
            "population_traces": {
                "format": "long (one row per representative pulse x freq x time)",
                "n_rows": len(top_idx) * len(freq_axis) * len(tlist),
                "columns": [
                    {"name": "pulse_duration_ns", "dtype": "float32", "unit": "ns",
                     "role": "coordinate", "description": "One of the three "
                     "representative pulses (shortest, middle, longest)."},
                    {"name": "drive_frequency_GHz", "dtype": "float32",
                     "unit": "GHz", "role": "coordinate",
                     "description": "Drive frequency (3.0-5.0 GHz, 400 values)."},
                    {"name": "timestamp_ns", "dtype": "float32", "unit": "ns",
                     "role": "coordinate (time axis)",
                     "description": "Simulation time (0-1000 ns, 1000 samples)."},
                    {"name": "population", "dtype": "float32", "unit": "dimensionless",
                     "role": "observable",
                     "description": "Full <sigma+ sigma-> time trace."},
                ],
            },
            "phaseV_fft": {
                "format": "long (one row per representative pulse x freq x fft bin)",
                "n_rows": len(top_idx) * len(freq_axis) * len(fft_freq_MHz),
                "columns": [
                    {"name": "pulse_duration_ns", "dtype": "float32", "unit": "ns",
                     "role": "coordinate", "description": "Representative pulse."},
                    {"name": "drive_frequency_GHz", "dtype": "float32",
                     "unit": "GHz", "role": "coordinate",
                     "description": "Drive frequency (3.0-5.0 GHz, 400 values)."},
                    {"name": "fft_frequency_MHz", "dtype": "float32", "unit": "MHz",
                     "role": "coordinate (FFT axis)",
                     "description": "Positive FFT frequency of phi(t), 0-150 MHz."},
                    {"name": "normalized_phase_fft", "dtype": "float32",
                     "unit": "dimensionless (0-1)", "role": "observable",
                     "description": "Row-wise normalized |FFT[phi(t)]| over the "
                     "0-400 ns window, where phi = arg<sigma+_1> - arg<sigma+_2>. "
                     "Normalized to peak 1 per drive frequency."},
                ],
            },
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# I/O
# ─────────────────────────────────────────────────────────────────────────────

class _Tee:
    """Duplicate stdout into a log file for reverification. tqdm uses stderr, so
    the log stays clean (summary + sanity-check PASS/FAIL lines)."""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, text):
        for s in self._streams:
            s.write(text)
        return len(text)

    def flush(self):
        for s in self._streams:
            s.flush()


def save_pickle(payload, path):
    with open(path, "wb") as fh:
        pickle.dump(payload, fh, protocol=PICKLE_PROTOCOL)


def load_pickle(path):
    with open(path, "rb") as fh:
        return pickle.load(fh)


def write_csv(data, columns, path, chunk_rows=500_000):
    import pandas as pd
    n = len(data)
    first = True
    with open(path, "w", newline="", encoding="utf-8") as fh:
        for start in tqdm(range(0, n, chunk_rows), desc=os.path.basename(path),
                          unit="chunk"):
            df = pd.DataFrame(data[start: start + chunk_rows], columns=columns)
            df.to_csv(fh, index=False, header=first)
            first = False


# ─────────────────────────────────────────────────────────────────────────────
# SOLVE
# ─────────────────────────────────────────────────────────────────────────────

def run_all(pulses, top_idx, freq_axis, tlist, workers, smoke_test):
    """Run the full pulse x frequency sweep, returning:
        postpulse_map     (n_pulses, n_freq)
        top_pop_maps      dict pulse_idx -> (n_freq, n_t)
        top_phi_maps      dict pulse_idx -> (n_freq, n_t)   wrapped phase
    """
    n_pulses, n_freq, n_t = len(pulses), len(freq_axis), len(tlist)
    postpulse_map = np.zeros((n_pulses, n_freq), dtype=np.float32)
    top_pop_maps, top_phi_maps = {}, {}
    top_set = set(top_idx)
    for pi in top_idx:
        top_pop_maps[pi] = np.zeros((n_freq, n_t), dtype=np.float32)
        top_phi_maps[pi] = np.zeros((n_freq, n_t), dtype=np.float32)

    def wrap(sp1, sp2):
        phi = np.angle(sp1) - np.angle(sp2)
        return ((phi + np.pi) % (2 * np.pi) - np.pi).astype(np.float32)

    # ── smoke test: synthetic, serial, no qutip ──────────────────────────────
    if smoke_test:
        for pi, pulse_ns in enumerate(tqdm(pulses, desc="pulses")):
            j_post = first_index_after(tlist, float(pulse_ns))
            want_full = pi in top_set
            for fi, f in enumerate(freq_axis):
                sp1, sp2, pop = _synthetic_full(f, DRIVE_AMPL, tlist, INIT_FREQS,
                                                float(pulse_ns))
                postpulse_map[pi, fi] = pop[j_post]
                if want_full:
                    top_pop_maps[pi][fi] = pop.astype(np.float32)
                    top_phi_maps[pi][fi] = wrap(sp1, sp2)
        return postpulse_map, top_pop_maps, top_phi_maps

    # ── real physics: one shared pool, all (pulse, freq) tasks ────────────────
    from concurrent.futures import ProcessPoolExecutor, as_completed
    H_int = build_H_int()

    tasks = []
    for pi, pulse_ns in enumerate(pulses):
        j_post = first_index_after(tlist, float(pulse_ns))
        want_full = pi in top_set
        for fi, f in enumerate(freq_axis):
            tasks.append((pi, fi, (float(f), float(pulse_ns), j_post, want_full)))

    n_workers = max(1, min(workers, len(tasks)))
    with ProcessPoolExecutor(
        n_workers, initializer=_init_worker,
        initargs=(tlist, INIT_FREQS, H_int, GAMMA, GAMMA_PHI, DRIVE_AMPL),
    ) as pool:
        futures = {pool.submit(_worker, t[2]): (t[0], t[1]) for t in tasks}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="solves"):
            pi, fi = futures[fut]
            scalar, sp1, sp2, pop = fut.result()
            postpulse_map[pi, fi] = scalar
            if sp1 is not None:
                top_pop_maps[pi][fi] = pop
                top_phi_maps[pi][fi] = wrap(sp1, sp2)
    return postpulse_map, top_pop_maps, top_phi_maps


# ─────────────────────────────────────────────────────────────────────────────
# TABLE ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────────

def assemble_postpulse(pulses, freq_axis, postpulse_map):
    n = len(pulses) * len(freq_axis)
    data = np.empty((n, 3), dtype=np.float32)
    r = 0
    for pi, pulse_ns in enumerate(pulses):
        e = r + len(freq_axis)
        data[r:e, 0] = pulse_ns
        data[r:e, 1] = freq_axis
        data[r:e, 2] = postpulse_map[pi]
        r = e
    return data


def assemble_poptraces(pulses, top_idx, freq_axis, tlist, top_pop_maps):
    n = len(top_idx) * len(freq_axis) * len(tlist)
    data = np.empty((n, 4), dtype=np.float32)
    r = 0
    for pi in top_idx:
        for fi, f in enumerate(freq_axis):
            e = r + len(tlist)
            data[r:e, 0] = pulses[pi]
            data[r:e, 1] = f
            data[r:e, 2] = tlist
            data[r:e, 3] = top_pop_maps[pi][fi]
            r = e
    return data


def assemble_phaseV(pulses, top_idx, freq_axis, top_phi_maps, tlist, dt):
    fft_freq_MHz = None
    blocks = []
    for pi in top_idx:
        mag_norm, fft_freq_MHz = compute_phaseV(top_phi_maps[pi], tlist, dt)
        n_freq, n_f = mag_norm.shape
        block = np.empty((n_freq * n_f, 4), dtype=np.float32)
        r = 0
        for fi, f in enumerate(freq_axis):
            e = r + n_f
            block[r:e, 0] = pulses[pi]
            block[r:e, 1] = f
            block[r:e, 2] = fft_freq_MHz
            block[r:e, 3] = mag_norm[fi]
            r = e
        blocks.append(block)
    return np.concatenate(blocks, axis=0), fft_freq_MHz


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def build_dataset(output_dir, workers=4, write_csv_file=True, smoke_test=False):
    """Public entry point. Tees stdout to a reverification log, then builds."""
    exp_dir = os.path.join(output_dir, "experiment_10")
    os.makedirs(exp_dir, exist_ok=True)
    log_path = os.path.join(exp_dir, "experiment_10_run.log")

    original_stdout = sys.stdout
    with open(log_path, "w", encoding="utf-8") as log_fh:
        sys.stdout = _Tee(original_stdout, log_fh)
        try:
            print(f"# Experiment 10 run log — "
                  f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} "
                  f"({'SMOKE TEST' if smoke_test else 'full run'}, "
                  f"workers={workers})")
            result = _build_dataset_impl(output_dir, workers, write_csv_file,
                                         smoke_test)
        finally:
            sys.stdout = original_stdout

    print(f"Run log written to {log_path}")
    return result


def _build_dataset_impl(output_dir, workers=4, write_csv_file=True, smoke_test=False):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(output_dir, "experiment_10")
    os.makedirs(output_dir, exist_ok=True)

    if smoke_test:
        n_pulses, n_freq, n_t = 5, 8, 40
    else:
        n_pulses, n_freq, n_t = N_PULSES, N_FREQ, N_T

    pulses    = np.linspace(PULSE_MIN_NS, PULSE_MAX_NS, n_pulses)
    freq_axis = np.linspace(F_MIN, F_MAX, n_freq)
    tlist     = np.linspace(0.0, T_MAX_NS, n_t)
    dt        = float(tlist[1] - tlist[0]) if n_t > 1 else 1.0
    top_idx   = top_pulse_indices(pulses)

    print(f"\nExperiment 10 dataset builder {'(SMOKE TEST)' if smoke_test else ''}")
    print(f"UNCOUPLED N=2 TLS (source quirk reproduced) at {INIT_FREQS} GHz")
    print(f"Pulses          : {n_pulses}  ({PULSE_MIN_NS}-{PULSE_MAX_NS} ns)")
    print(f"  representative: {[round(float(pulses[i]),2) for i in top_idx]} ns")
    print(f"Drive freqs     : {n_freq}  ({F_MIN}-{F_MAX} GHz)")
    print(f"Time samples    : {n_t}  (0-{T_MAX_NS} ns)")
    print(f"Total solves    : {n_pulses} x {n_freq} = {n_pulses*n_freq:,}\n")

    # ── run the sweep ────────────────────────────────────────────────────────
    postpulse_map, top_pop_maps, top_phi_maps = run_all(
        pulses, top_idx, freq_axis, tlist, workers, smoke_test)

    # ── assemble the three tables ────────────────────────────────────────────
    print("\nAssembling tables ...")
    pp_data = assemble_postpulse(pulses, freq_axis, postpulse_map)
    pt_data = assemble_poptraces(pulses, top_idx, freq_axis, tlist, top_pop_maps)
    pv_data, fft_freq_MHz = assemble_phaseV(pulses, top_idx, freq_axis,
                                            top_phi_maps, tlist, dt)

    tables = {
        "postpulse_map":     (pp_data, POSTPULSE_COLUMNS),
        "population_traces": (pt_data, POPTRACE_COLUMNS),
        "phaseV_fft":        (pv_data, PHASEV_COLUMNS),
    }

    metadata = build_metadata(pulses, top_idx, freq_axis, tlist, fft_freq_MHz,
                              smoke_test)
    column_doc = build_column_info(pulses, top_idx, freq_axis, tlist, fft_freq_MHz)

    # ── save pickles + JSON sidecars ─────────────────────────────────────────
    print("\nSaving ...")
    pkl_paths = {}
    for name, (data, cols) in tables.items():
        pkl_path = os.path.join(output_dir, f"experiment_10_{name}.pkl")
        payload = {"data": data, "columns": cols, "table": name,
                   "attrs": metadata, "column_doc": column_doc["tables"][name]}
        save_pickle(payload, pkl_path)
        pkl_paths[name] = pkl_path
        print(f"  {name:18s}: {data.shape}  ->  {pkl_path}  "
              f"({os.path.getsize(pkl_path)/1024**2:.1f} MB)")

    meta_path = os.path.join(script_dir, "metadata.json")
    cols_path = os.path.join(script_dir, "column_info.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
    with open(cols_path, "w", encoding="utf-8") as fh:
        json.dump(column_doc, fh, indent=2)
    print(f"  metadata          : {meta_path}")
    print(f"  column_info       : {cols_path}")

    # ── sanity checks ────────────────────────────────────────────────────────
    print("\nRunning sanity checks ...")
    errors = []
    n_top = len(top_idx)
    n_f = len(fft_freq_MHz)
    expected = {
        "postpulse_map": n_pulses * n_freq,
        "population_traces": n_top * n_freq * n_t,
        "phaseV_fft": n_top * n_freq * n_f,
    }
    for name, (data, cols) in tables.items():
        if data.shape[0] != expected[name]:
            errors.append(f"  [FAIL] {name} rows: got {data.shape[0]:,}, "
                          f"expected {expected[name]:,}")
        elif int(np.isnan(data).sum()) or int(np.isinf(data).sum()):
            errors.append(f"  [FAIL] {name} contains NaN/Inf")
        else:
            print(f"  [PASS] {name}: {data.shape[0]:,} rows, no NaN/Inf")

    pop_col = pt_data[:, POPTRACE_COLUMNS.index("population")]
    if pop_col.min() < -1e-3:
        errors.append(f"  [FAIL] population negative: {pop_col.min():.4f}")
    else:
        print(f"  [PASS] population non-negative: "
              f"[{pop_col.min():.4f}, {pop_col.max():.4f}]")

    pp_col = pp_data[:, POSTPULSE_COLUMNS.index("postpulse_population")]
    if pp_col.min() < -1e-3:
        errors.append(f"  [FAIL] postpulse_population negative: {pp_col.min():.4f}")
    else:
        print(f"  [PASS] postpulse_population non-negative: "
              f"[{pp_col.min():.4f}, {pp_col.max():.4f}]")

    pv_col = pv_data[:, PHASEV_COLUMNS.index("normalized_phase_fft")]
    if pv_col.min() < -1e-6 or pv_col.max() > 1.0 + 1e-4:
        errors.append(f"  [FAIL] normalized_phase_fft outside [0,1]: "
                      f"[{pv_col.min():.4f}, {pv_col.max():.4f}]")
    else:
        print(f"  [PASS] normalized_phase_fft in [0,1]: "
              f"[{pv_col.min():.4f}, {pv_col.max():.4f}]")

    if len(np.unique(pp_data[:, 0])) != n_pulses:
        errors.append("  [FAIL] postpulse_map pulse count mismatch")
    else:
        print(f"  [PASS] postpulse_map spans {n_pulses} pulses x {n_freq} freqs")

    # pickle round-trip on the largest table
    reloaded = load_pickle(pkl_paths["population_traces"])
    if not np.array_equal(reloaded["data"], pt_data):
        errors.append("  [FAIL] Pickle round-trip: population_traces differs")
    else:
        print("  [PASS] Pickle round-trip: population_traces matches exactly")

    if errors:
        print(f"\n  {len(errors)} sanity check(s) FAILED:")
        for e in errors:
            print(e)
    else:
        print("\n  All sanity checks passed.")

    # ── CSVs ─────────────────────────────────────────────────────────────────
    if write_csv_file:
        print("\nWriting CSVs ...")
        for name, (data, cols) in tables.items():
            csv_path = os.path.join(output_dir, f"experiment_10_{name}.csv")
            write_csv(data, cols, csv_path)
            print(f"  {name:18s}: {os.path.getsize(csv_path)/1024**2:.1f} MB, "
                  f"{data.shape[0]:,} rows")

    return pkl_paths


if __name__ == "__main__":
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(
        description="Build the Experiment 10 simulated dataset (three long-format "
        "tables; N=2 TLS ring-down & phase sharpening, including the uncoupled "
        "quirk)."
    )
    parser.add_argument("--output_dir", type=str, default=_script_dir,
                        help="Where to write experiment_10/ (default: next to this script).")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel solver processes (real run only).")
    parser.add_argument("--no_csv", action="store_true",
                        help="Skip the CSVs, write only the pickles.")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Tiny grids + synthetic arrays; no qutip required.")
    args = parser.parse_args()

    build_dataset(
        output_dir=os.path.abspath(args.output_dir),
        workers=args.workers,
        write_csv_file=not args.no_csv,
        smoke_test=args.smoke_test,
    )
