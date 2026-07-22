"""
experiment_9_dataset_creation.py
================================
Runs the Experiment 9 simulation, catches the population traces it produces, and
writes them out as a long-format dataset: one row per time sample, saved as a
pickle and a CSV.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAIN-LANGUAGE PRIMER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT THIS IS — A SIMULATION, NOT A MEASUREMENT
    Like Experiment 8, Experiment 9 is produced entirely on a computer. There is
    no instrument, no I and no Q. A model of the physics is written down and
    solved numerically; the "data" is the solver's output. This script runs that
    same model and stores its result in a shareable table.

WHAT IS BEING MODELLED
    Two microscopic defects — TWO-LEVEL SYSTEMS (TLS), tiny quantum switches —
    that are COUPLED to one another and sit in an environment that slowly leaks
    their energy away (dissipation). The equation of motion is a LINDBLAD MASTER
    EQUATION, solved with QuTiP's `mesolve`. None of that physics is invented
    here: it is imported from the local `hamiltonian_generator.py`.

THE MEASUREMENT — like striking a bell
    A short microwave DRIVE PULSE excites the coupled defects; when it stops they
    keep re-radiating for a while — a fading echo, the RING-DOWN. Following that
    echo in time is the whole point.

THE ONE NUMBER RECORDED — "population"
    At every instant the solver reports one quantity:

        population = <sigma^+ sigma^->   (collective excitation)

    Zero when everything has relaxed, larger while the drive pumps energy in and
    during the ring-down. Dimensionless, never negative. This single column is
    the OUTPUT of the whole experiment.

WHAT THIS PARTICULAR EXPERIMENT DOES — three panels
    This experiment studies how the SEPARATION between two pulses — both the gap
    and the relative phase of the second pulse — steers the ring-down. Three
    parts (kept here as "panels"), each one block of rows:

    panel 0  RING-DOWN MAP.  One 200 ns pulse. The DRIVE FREQUENCY is swept
             across 2.0-5.0 GHz (400 values). This finds the frequency at which
             the pair rings the LONGEST after the pulse — FREQ_STAR — which the
             other two panels reuse. (Recomputed here, not hard-coded.)

    panel 1  GAP SWEEP.  Two pulses at FREQ_STAR, same amplitude, the second in
             phase with the first (phase2 = 0). The GAP between them is swept
             from 0 to 800 ns (120 values), showing how the response changes as
             the second pulse lands later and later into the ring-down.

    panel 2  PHASE SWEEP.  Two pulses at FREQ_STAR, gap fixed at 150 ns. The
             RELATIVE PHASE of the second pulse is swept through a full turn,
             0 to 2*pi (120 values). Because the second pulse arrives while the
             pair is still ringing, its phase decides whether the two responses
             add or cancel — the coherent-control knob.

UNIT CONVENTION  (inherited from the model, not chosen here)
    Frequencies are used numerically as inverse nanoseconds (GHz == ns^-1) with
    NO factor of 2*pi inside the solver. Amplitudes are dimensionless drive
    strengths; the relative phase is in radians; times are nanoseconds.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Long format": every row is ONE instant in time from ONE simulated trace, and
the columns repeat the settings in force at that instant. One complete ring-down
trace = 1000 consecutive rows.

10 columns, one row per time sample:

    col 0 — panel_id             0 = ring-down map, 1 = gap sweep, 2 = phase sweep
    col 1 — drive_frequency_GHz  drive frequency (swept in panel 0; FREQ_STAR in 1, 2)
    col 2 — amp1                 amplitude of pulse 1
    col 3 — amp2                 amplitude of pulse 2 (0 when there is no 2nd pulse)
    col 4 — pulse1_ns            duration of pulse 1 (ns)
    col 5 — gap_ns               inter-pulse gap (ns; swept in panel 1, 150 in panel 2, 0 in panel 0)
    col 6 — pulse2_ns            duration of pulse 2 (ns; 0 when there is no 2nd pulse)
    col 7 — phase2_rad           relative phase of pulse 2 (rad; swept in panel 2, else 0)
    col 8 — timestamp_ns         simulation time of this sample (ns)
    col 9 — population           <sigma+ sigma-> collective excitation (the OUTPUT)

Everything that is a single fixed number for the whole run — N_TLS, the two TLS
frequencies, the coupling, gamma, the seed, the time grid, and FREQ_STAR — is
NOT repeated on every row. It is recorded once in metadata.json.

Total rows (full run):
    panel 0 : 400 drive freqs x 1000 time samples = 400,000
    panel 1 : 120 gaps        x 1000 time samples = 120,000
    panel 2 : 120 phases      x 1000 time samples = 120,000
                                            total  = 640,000

Timestamp spacing: 1600 ns / (1000 - 1) ~= 1.6016 ns per sample

FREQ_STAR IS RECOMPUTED, NOT ASSUMED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The drive frequency for panels 1 and 2 is chosen as the argmax, over the
400-point sweep, of the population summed over the post-pulse tail
(timestamp_ns > pulse1_ns), computed on panel 0's output — so the frequency used
downstream matches the physics rather than a copied constant.

PROVENANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    physics module : hamiltonian_generator.py  (local; only a QuTiP-5 API
                     compatibility shim differs — see that file)
    The simulation knobs below are fixed and deterministic; the seed and draw
    ORDER are reproduced on every run so the coupling is always identical.
    Uses code and simulation methods from the Fitzpatrick Lab, Dartmouth College.

OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    09_separation_phase_sweep/experiment_9/experiment_9_dataset_long.pkl
    09_separation_phase_sweep/experiment_9/experiment_9_dataset_long.csv
    09_separation_phase_sweep/experiment_9/experiment_9_run.log   (reverification log)
    09_separation_phase_sweep/metadata.json
    09_separation_phase_sweep/column_info.json

    payload["data"]          shape (640_000, 10), float32
    payload["columns"]       the 10 column names
    payload["attrs"]         experiment metadata (mirrors metadata.json)
    payload["column_doc"]    per-column semantics (mirrors column_info.json)

The run log captures the full build summary and every sanity-check PASS/FAIL
line, so a re-run can be checked against a previous one. It is a *.log file and
is git-ignored (a build artifact, not source).

To load in Python:

    import pickle
    import pandas as pd

    with open("experiment_9_dataset_long.pkl", "rb") as fh:
        payload = pickle.load(fh)
    df = pd.DataFrame(payload["data"], columns=payload["columns"])

    # one phase-sweep trace at phase = pi (1000 rows):
    import numpy as np
    m = (df["panel_id"] == 2)
    p = df[m]["phase2_rad"].unique()
    near_pi = p[np.argmin(np.abs(p - np.pi))]
    trace = df[m & (df["phase2_rad"] == near_pi)].sort_values("timestamp_ns")

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # full run (needs qutip; heavy -- run on a workstation/cluster)
    python experiment_9_dataset_creation.py --workers 8

    # fast plumbing check (no qutip: synthetic population on tiny grids)
    python experiment_9_dataset_creation.py --smoke-test

    Optional arguments:
        --output_dir  where to write experiment_9/ (default: next to this script)
        --workers     parallel solver processes (default: 4; ignored in smoke test)
        --no_csv      skip the CSV (pickle only)
        --smoke-test  shrink grids + use a synthetic population (no qutip needed)
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
# Do not "improve" these: they are what makes the output reproducible.
# ─────────────────────────────────────────────────────────────────────────────

# Pulse timing (nanoseconds). Both pulses share one duration in this experiment.
PULSE_NS   = 200
FIXED_GAP_NS = 150           # gap held fixed while the phase is swept (panel 2)

# Drive-frequency sweep (panel 0). Treated numerically as GHz == ns^-1.
F_MIN, F_MAX = 2.0, 5.0
N_FREQ       = 400

# Gap sweep (panel 1) and phase sweep (panel 2).
GAP_LO, GAP_HI = 0.0, 800.0
N_GAP          = 120
PHASE_LO, PHASE_HI = 0.0, 2.0 * np.pi
N_PHASE            = 120

# Time grid: 0 to 1600 ns, 1000 points.
T_MAX_NS, N_T = 1600, 1000

# The N = 2 coupled-TLS ensemble. The TLS frequencies are HARD-CODED to
# [3.0, 4.0] after a throwaway random draw; the coupling is then drawn from the
# seeded RNG. The draw ORDER (one 2-value uniform consumed first) is fixed below
# so the coupling is deterministic on every run.
N_TLS        = 2
SEED         = 42
INIT_FREQS   = [3.0, 4.0]
J_MIN, J_MAX = -0.05, 0.05   # XX coupling range

# Dissipation and drive amplitude.
GAMMA, GAMMA_PHI = 0.002, 0.0
AMP_DRIVE        = 0.12       # both pulses use this amplitude

# Panel bookkeeping.
PANEL_NAMES = ["ring_down_map", "gap_sweep", "phase_sweep"]

# Only what varies across rows gets a column; scalar constants live in
# metadata.json. See the module docstring's FORMAT section.
COLUMN_NAMES = [
    "panel_id",
    "drive_frequency_GHz",
    "amp1",
    "amp2",
    "pulse1_ns",
    "gap_ns",
    "pulse2_ns",
    "phase2_rad",
    "timestamp_ns",
    "population",
]

COL = {name: i for i, name in enumerate(COLUMN_NAMES)}
PICKLE_PROTOCOL = 4


# ─────────────────────────────────────────────────────────────────────────────
# ENSEMBLE SETUP — the exact RNG stream that fixes the ensemble
# ─────────────────────────────────────────────────────────────────────────────

def build_ensemble(smoke_test=False):
    """Return (init_freqs, H_int).

    The RNG stream is fixed and deterministic:
        np.random.seed(SEED)
        _ = np.random.uniform(F_MIN, F_MAX, N_TLS)   # throwaway draw, then...
        init_freqs = [3.0, 4.0]                       # hard-coded override
        H_int      = build_spin_spin_...(N_TLS, J_MIN, J_MAX)   # draws the coupling

    In smoke-test mode qutip is not required, so H_int is returned as the raw
    symmetric coupling matrix (a plain ndarray) instead of a QuTiP operator.
    """
    np.random.seed(SEED)
    _ = np.random.uniform(F_MIN, F_MAX, N_TLS)   # consume the throwaway draw
    init_freqs = list(INIT_FREQS)

    if smoke_test:
        J = np.random.uniform(J_MIN, J_MAX, size=(N_TLS, N_TLS))
        J = np.tril(J, -1) + np.tril(J, -1).T
        return init_freqs, J

    from hamiltonian_generator import build_spin_spin_interactions_random_distribution
    H_int = build_spin_spin_interactions_random_distribution(N_TLS, J_MIN, J_MAX)
    return init_freqs, H_int


def coupling_matrix_from_seed():
    """Recompute the symmetric coupling matrix (for metadata.json only), without
    disturbing any live RNG state used elsewhere."""
    rng_state = np.random.get_state()
    try:
        np.random.seed(SEED)
        _ = np.random.uniform(F_MIN, F_MAX, N_TLS)   # consume throwaway draw
        J = np.random.uniform(J_MIN, J_MAX, size=(N_TLS, N_TLS))
        J = np.tril(J, -1) + np.tril(J, -1).T
    finally:
        np.random.set_state(rng_state)
    return J


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC POPULATION — smoke-test stand-in for the QuTiP solver.
# NOT physically meaningful; it only exercises the dataset plumbing without qutip.
# ─────────────────────────────────────────────────────────────────────────────

def _synthetic_single(freq, amp, tlist, init_freqs, pulse_ns):
    detune = np.min(np.abs(np.asarray(init_freqs) - freq))
    lorentz = 1.0 / (1.0 + (detune / 0.15) ** 2)
    drive = amp * lorentz * np.sin(
        np.pi * np.clip(tlist / max(pulse_ns, 1e-9), 0, 1)
    ) ** 2
    tail = np.where(tlist > pulse_ns,
                    amp * lorentz * np.exp(-GAMMA * (tlist - pulse_ns)), 0.0)
    pop = np.where(tlist <= pulse_ns, drive, tail)
    return np.clip(pop, 0.0, None).astype(np.float64)


def _synthetic_double_phase(freq, amp1, amp2, pulse1_ns, gap_ns, pulse2_ns,
                            phase2_rad, tlist, init_freqs):
    """Phase-aware surrogate: the second pulse interferes with the first with a
    (1 + cos(phase2))/2 weighting, so the phase axis actually varies the output."""
    p1 = _synthetic_single(freq, amp1, tlist, init_freqs, pulse1_ns)
    t2_start = pulse1_ns + gap_ns
    shifted = tlist - t2_start
    interf = 0.5 * (1.0 + np.cos(phase2_rad))
    p2 = np.where(shifted >= 0,
                  interf * _synthetic_single(freq, amp2, np.clip(shifted, 0, None),
                                             init_freqs, pulse2_ns),
                  0.0)
    return np.clip(p1 * np.exp(-GAMMA * tlist) + p2, 0.0, None).astype(np.float64)


# ─────────────────────────────────────────────────────────────────────────────
# SWEEP RUNNERS — thin wrappers around the ORIGINAL physics functions
# ─────────────────────────────────────────────────────────────────────────────

def _run_sweep(kind, param_list, freq_star, tlist, init_freqs, H_int,
               workers, smoke_test):
    """Run one panel's sweep, returning a (len(param_list), len(tlist)) array.

    kind = "freq"   -> single-pulse ring-down map, param_list = drive freqs
    kind = "gap"    -> two-pulse (phase2=0) at freq_star, param = gap_ns
    kind = "phase"  -> two-pulse at freq_star, fixed gap, param = phase2_rad

    The real branch calls run_simulation_single_pulse / run_simulation_double_
    pulse_phase straight out of the local hamiltonian_generator.py.
    """
    out = np.zeros((len(param_list), len(tlist)), dtype=np.float64)

    if smoke_test:
        for i, p in enumerate(param_list):
            if kind == "freq":
                out[i] = _synthetic_single(p, AMP_DRIVE, tlist, init_freqs, PULSE_NS)
            elif kind == "gap":
                out[i] = _synthetic_double_phase(freq_star, AMP_DRIVE, AMP_DRIVE,
                                                 PULSE_NS, p, PULSE_NS, 0.0,
                                                 tlist, init_freqs)
            else:  # phase
                out[i] = _synthetic_double_phase(freq_star, AMP_DRIVE, AMP_DRIVE,
                                                 PULSE_NS, FIXED_GAP_NS, PULSE_NS, p,
                                                 tlist, init_freqs)
        return out

    from concurrent.futures import ProcessPoolExecutor, as_completed
    from hamiltonian_generator import (
        run_simulation_single_pulse, run_simulation_double_pulse_phase,
    )

    def submit(pool, p):
        if kind == "freq":
            return pool.submit(run_simulation_single_pulse, p, AMP_DRIVE,
                               tlist, init_freqs, H_int, GAMMA, GAMMA_PHI, PULSE_NS)
        if kind == "gap":
            return pool.submit(run_simulation_double_pulse_phase,
                               freq_star, AMP_DRIVE, AMP_DRIVE,
                               PULSE_NS, p, PULSE_NS, 0.0,
                               tlist, init_freqs, H_int, GAMMA, GAMMA_PHI)
        return pool.submit(run_simulation_double_pulse_phase,
                           freq_star, AMP_DRIVE, AMP_DRIVE,
                           PULSE_NS, FIXED_GAP_NS, PULSE_NS, p,
                           tlist, init_freqs, H_int, GAMMA, GAMMA_PHI)

    n_workers = max(1, min(workers, len(param_list)))
    with ProcessPoolExecutor(n_workers) as pool:
        futures = {submit(pool, p): i for i, p in enumerate(param_list)}
        for fut in tqdm(as_completed(futures), total=len(futures), desc=kind):
            out[futures[fut]] = np.asarray(fut.result(), dtype=np.float64)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# METADATA
# ─────────────────────────────────────────────────────────────────────────────

def build_metadata(freq_star, init_freqs, n_freq, n_gap, n_phase, n_t,
                   smoke_test=False) -> dict:
    return {
        "experiment_id": "experiment_9",
        "title": "Separation & Relative-Phase Coherent Control (N=2 TLS simulation)",
        "data_type": "simulation",
        "description": (
            "Numerical BCTDS ring-down of N=2 coupled two-level systems evolved "
            "under a Lindblad master equation (QuTiP mesolve). A square microwave "
            "drive pulse excites the pair and its collective excitation "
            "<sigma+ sigma-> is followed as it rings down. Three panels: (0) a "
            "single-pulse ring-down map versus drive frequency, from which the "
            "longest-lived FREQ_STAR is selected; (1) a two-pulse gap sweep at "
            "FREQ_STAR with the second pulse in phase; (2) a two-pulse relative-"
            "phase sweep at FREQ_STAR with the gap held fixed. The population is "
            "the only observable; it is computed by the solver, not measured. The "
            "model is imported from the local hamiltonian_generator.py (QuTiP-5 "
            "API shim only)."
        ),
        "model": {
            "system": f"{N_TLS} coupled two-level systems (TLS)",
            "equation_of_motion": "Lindblad master equation",
            "solver": "QuTiP mesolve",
            "observable": "<sigma+ sigma-> (collective excitation), dimensionless",
            "unit_convention": (
                "Frequencies used numerically as inverse nanoseconds (GHz == ns^-1) "
                "with NO factor of 2*pi inside the solver. Amplitudes are "
                "dimensionless; phase in radians; times in nanoseconds."
            ),
        },
        "hamiltonian": {
            "n_tls": N_TLS,
            "seed": SEED,
            "tls_frequencies_GHz": [float(f) for f in init_freqs],
            "tls_frequencies_note": (
                "Hard-coded to [3.0, 4.0] after a throwaway random draw; that draw "
                "is reproduced so the coupling is deterministic."
            ),
            "coupling_type": "XX (alpha_x=1, alpha_y=0, alpha_z=0)",
            "coupling_J_range_GHz": [J_MIN, J_MAX],
            "coupling_J_matrix_GHz": coupling_matrix_from_seed().tolist(),
            "gamma_collective": GAMMA,
            "gamma_dephasing": GAMMA_PHI,
        },
        "timing": {
            "pulse1_ns": PULSE_NS,
            "pulse2_ns": PULSE_NS,
            "fixed_gap_ns_panel_2": FIXED_GAP_NS,
            "pulse_shape": "square with a 1 ns raised-cosine turn-on (T_ramp_ns=1)",
            "time_grid": {
                "t_min_ns": 0.0,
                "t_max_ns": T_MAX_NS,
                "n_samples": n_t,
                "one_sample_ns": T_MAX_NS / (n_t - 1) if n_t > 1 else 0.0,
                "formula": "timestamp_ns = linspace(0, 1600, 1000)",
            },
        },
        "sweep": {
            "panels": {"n": 3, "names": PANEL_NAMES,
                       "note": "panel_id 0=ring-down map, 1=gap sweep, "
                               "2=phase sweep."},
            "drive_frequency": {"panel": 0, "n": n_freq, "unit": "GHz",
                                "range": [F_MIN, F_MAX],
                                "note": "Swept in panel 0; FREQ_STAR in panels 1,2."},
            "gap": {"panel": 1, "n": n_gap, "unit": "ns", "range": [GAP_LO, GAP_HI],
                    "fixed_value_panel_2": FIXED_GAP_NS,
                    "note": "Inter-pulse gap; swept in panel 1, fixed in panel 2."},
            "phase2": {"panel": 2, "n": n_phase, "unit": "rad",
                       "range": [PHASE_LO, PHASE_HI],
                       "note": "Relative phase of pulse 2; swept in panel 2, else 0."},
            "amplitude": {"value": AMP_DRIVE, "note": "Both pulses; not swept."},
            "time_samples_per_trace": n_t,
        },
        "freq_star": {
            "value_GHz": round(float(freq_star), 6),
            "rule": (
                "argmax over the panel-0 drive-frequency sweep of the population "
                "summed over the post-pulse tail (timestamp_ns > pulse1_ns). "
                "Recomputed here, not hard-coded."
            ),
        },
        "provenance": {
            "physics_module": "hamiltonian_generator.py (QuTiP-5 API shim only)",
            "attribution": "Uses code and simulation methods from the "
                           "Fitzpatrick Lab, Dartmouth College.",
            "no_new_physics": True,
            "smoke_test": smoke_test,
        },
    }


def build_column_info(n_freq, n_gap, n_phase, n_t) -> dict:
    return {
        "dataset": "experiment_9_separation_phase_sweep",
        "format": "long (one row per time sample)",
        "n_rows": (n_freq + n_gap + n_phase) * n_t,
        "n_columns": len(COLUMN_NAMES),
        "schema_rule": (
            "panel_id selects one of three simulated regimes; the swept knob for "
            "that panel and the fast time axis vary row-to-row, together with the "
            "single simulated observable (population). All scalar constants of the "
            "run live once in metadata.json, not repeated per row."
        ),
        "columns": [
            {"name": "panel_id", "dtype": "float32", "unit": "categorical (0/1/2)",
             "role": "coordinate (regime selector)", "measured": False,
             "values": [0, 1, 2],
             "value_labels": {0: PANEL_NAMES[0], 1: PANEL_NAMES[1], 2: PANEL_NAMES[2]},
             "n_unique": 3,
             "description": "0 ring-down map (single pulse, drive freq swept), "
             "1 gap sweep (two pulses, phase2=0, gap swept, at FREQ_STAR), "
             "2 phase sweep (two pulses, fixed gap, phase2 swept, at FREQ_STAR)."},
            {"name": "drive_frequency_GHz", "dtype": "float32",
             "unit": "GHz (== ns^-1, no 2*pi)",
             "role": "coordinate (swept input in panel 0)", "measured": False,
             "range": [F_MIN, F_MAX], "n_unique_panel_0": n_freq,
             "description": "Microwave drive frequency. Swept across 2.0-5.0 GHz in "
             "panel 0; held at FREQ_STAR in panels 1 and 2."},
            {"name": "amp1", "dtype": "float32",
             "unit": "dimensionless drive amplitude",
             "role": "coordinate (fixed)", "measured": False, "value": AMP_DRIVE,
             "description": "Amplitude of the first (or only) drive pulse. Constant "
             "at 0.12 throughout."},
            {"name": "amp2", "dtype": "float32",
             "unit": "dimensionless drive amplitude",
             "role": "coordinate", "measured": False,
             "description": "Amplitude of the second drive pulse (0.12 in panels 1,2; "
             "0 in panel 0 where there is no second pulse)."},
            {"name": "pulse1_ns", "dtype": "float32", "unit": "ns",
             "role": "coordinate (pulse timing)", "measured": False,
             "description": "Duration of the first pulse. Constant (200 ns)."},
            {"name": "gap_ns", "dtype": "float32", "unit": "ns",
             "role": "coordinate (swept input in panel 1)", "measured": False,
             "range": [GAP_LO, GAP_HI],
             "description": "Idle gap after pulse 1 before pulse 2. Swept 0-800 ns in "
             "panel 1; fixed at 150 ns in panel 2; 0 in panel 0 (single pulse)."},
            {"name": "pulse2_ns", "dtype": "float32", "unit": "ns",
             "role": "coordinate (pulse timing)", "measured": False,
             "description": "Duration of the second pulse (200 ns in panels 1,2; "
             "0 in panel 0)."},
            {"name": "phase2_rad", "dtype": "float32", "unit": "rad",
             "role": "coordinate (swept input in panel 2)", "measured": False,
             "range": [PHASE_LO, PHASE_HI],
             "description": "Relative phase of the second pulse. Swept 0-2*pi in "
             "panel 2; 0 elsewhere. Decides whether the second pulse's response "
             "adds to or cancels the ring-down of the first."},
            {"name": "timestamp_ns", "dtype": "float32", "unit": "ns",
             "role": "coordinate (time axis)", "measured": False,
             "range": [0.0, float(T_MAX_NS)], "n_unique": n_t,
             "description": "Simulation time within the trace. Identical grid for "
             "every trace, so traces are directly comparable."},
            {"name": "population", "dtype": "float32", "unit": "dimensionless",
             "role": "simulated observable (output)", "measured": False,
             "computed_from": "QuTiP mesolve expectation of Sm.dag()*Sm",
             "description": "Collective excitation <sigma+ sigma-> of the N=2 TLS "
             "pair, computed by the Lindblad solver. Non-negative. The sole output."},
        ],
        "computable_not_stored": {
            "note": "population is the only observable stored here.",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# I/O
# ─────────────────────────────────────────────────────────────────────────────

class _Tee:
    """Duplicate everything written to stdout into a log file as well, so each
    run leaves a persistent, human-readable record for reverification (the run
    summary, FREQ_STAR, and every sanity-check PASS/FAIL line). tqdm progress
    bars write to stderr, so they stay on the console and out of the clean log."""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, text):
        for s in self._streams:
            s.write(text)
        return len(text)

    def flush(self):
        for s in self._streams:
            s.flush()


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
            df = pd.DataFrame(data[start: start + chunk_rows], columns=columns)
            df.to_csv(fh, index=False, header=first)
            first = False


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def build_dataset(output_dir, workers=4, write_csv_file=True, smoke_test=False):
    """Public entry point. Tees all console output to a run log for
    reverification, then delegates to _build_dataset_impl."""
    exp_dir = os.path.join(output_dir, "experiment_9")
    os.makedirs(exp_dir, exist_ok=True)
    log_path = os.path.join(exp_dir, "experiment_9_run.log")

    original_stdout = sys.stdout
    with open(log_path, "w", encoding="utf-8") as log_fh:
        sys.stdout = _Tee(original_stdout, log_fh)
        try:
            print(f"# Experiment 9 run log — "
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
    output_dir = os.path.join(output_dir, "experiment_9")
    os.makedirs(output_dir, exist_ok=True)
    pkl_path = os.path.join(output_dir, "experiment_9_dataset_long.pkl")
    csv_path = os.path.join(output_dir, "experiment_9_dataset_long.csv")

    if smoke_test:
        n_freq, n_gap, n_phase, n_t = 8, 5, 5, 20
    else:
        n_freq, n_gap, n_phase, n_t = N_FREQ, N_GAP, N_PHASE, N_T

    freq_axis  = np.linspace(F_MIN, F_MAX, n_freq)
    gap_sweep  = np.linspace(GAP_LO, GAP_HI, n_gap)
    phase_sweep = np.linspace(PHASE_LO, PHASE_HI, n_phase)
    tlist      = np.linspace(0.0, T_MAX_NS, n_t)

    n_total_rows = (n_freq + n_gap + n_phase) * n_t

    print(f"\nExperiment 9 dataset builder {'(SMOKE TEST)' if smoke_test else ''}")
    print(f"Format          : long (one row per time sample)")
    print(f"System          : N={N_TLS} coupled TLS, Lindblad master equation")
    print(f"Panels          : 0=ring-down map, 1=gap sweep, 2=phase sweep")
    print(f"Drive freqs     : {n_freq}  ({F_MIN}-{F_MAX} GHz, panel 0)")
    print(f"Gaps            : {n_gap}  ({GAP_LO}-{GAP_HI} ns, panel 1)")
    print(f"Phases          : {n_phase}  (0-2*pi rad, panel 2)")
    print(f"Time samples    : {n_t}  (0-{T_MAX_NS} ns)")
    print(f"Total rows      : ({n_freq}+{n_gap}+{n_phase}) x {n_t} = {n_total_rows:,}")
    print(f"Columns         : {COLUMN_NAMES}\n")

    init_freqs, H_int = build_ensemble(smoke_test=smoke_test)
    print(f"TLS freqs       : {init_freqs} GHz (seed {SEED}, hard-coded)\n")

    # ── panel 0: ring-down map + FREQ_STAR ───────────────────────────────────
    print("[panel 0] ring-down map ...")
    pop_ring = _run_sweep("freq", freq_axis, None, tlist, init_freqs, H_int,
                          workers, smoke_test)
    mask_tail = tlist > PULSE_NS
    if mask_tail.any():
        freq_star = float(freq_axis[np.argmax(pop_ring[:, mask_tail].sum(axis=1))])
    else:
        freq_star = float(freq_axis[np.argmax(pop_ring.sum(axis=1))])
    print(f"  FREQ_STAR     : {freq_star:.4f} GHz")

    # ── panel 1: gap sweep (phase2 = 0) ──────────────────────────────────────
    print("\n[panel 1] gap sweep ...")
    pop_gap = _run_sweep("gap", gap_sweep, freq_star, tlist, init_freqs, H_int,
                         workers, smoke_test)

    # ── panel 2: phase sweep (fixed gap) ─────────────────────────────────────
    print("\n[panel 2] phase sweep ...")
    pop_phase = _run_sweep("phase", phase_sweep, freq_star, tlist, init_freqs, H_int,
                           workers, smoke_test)

    # ── assemble the long table ──────────────────────────────────────────────
    data_all = np.empty((n_total_rows, len(COLUMN_NAMES)), dtype=np.float32)
    row_idx = 0

    def emit(panel_id, drive_freq, a1, a2, p1, gap, p2, phase2, pop_matrix, param_iter):
        nonlocal row_idx
        for row_i, _param in enumerate(param_iter):
            end = row_idx + n_t
            data_all[row_idx:end, COL["panel_id"]] = panel_id
            data_all[row_idx:end, COL["drive_frequency_GHz"]] = (
                drive_freq[row_i] if np.ndim(drive_freq) else drive_freq)
            data_all[row_idx:end, COL["amp1"]] = a1
            data_all[row_idx:end, COL["amp2"]] = a2
            data_all[row_idx:end, COL["pulse1_ns"]] = p1
            data_all[row_idx:end, COL["gap_ns"]] = (
                gap[row_i] if np.ndim(gap) else gap)
            data_all[row_idx:end, COL["pulse2_ns"]] = p2
            data_all[row_idx:end, COL["phase2_rad"]] = (
                phase2[row_i] if np.ndim(phase2) else phase2)
            data_all[row_idx:end, COL["timestamp_ns"]] = tlist
            data_all[row_idx:end, COL["population"]] = pop_matrix[row_i]
            row_idx = end

    # panel 0: single pulse -> amp2=0, gap=0, pulse2=0, phase2=0
    emit(0, freq_axis, AMP_DRIVE, 0.0, PULSE_NS, 0.0, 0.0, 0.0, pop_ring, freq_axis)
    # panel 1: two pulses, phase2=0, gap swept
    emit(1, freq_star, AMP_DRIVE, AMP_DRIVE, PULSE_NS, gap_sweep, PULSE_NS, 0.0,
         pop_gap, gap_sweep)
    # panel 2: two pulses, gap fixed, phase2 swept
    emit(2, freq_star, AMP_DRIVE, AMP_DRIVE, PULSE_NS, FIXED_GAP_NS, PULSE_NS,
         phase_sweep, pop_phase, phase_sweep)

    data_final = data_all[:row_idx]

    # ── save pickle + JSON sidecars ──────────────────────────────────────────
    print(f"\nSaving to {pkl_path} ...")
    metadata = build_metadata(freq_star, init_freqs, n_freq, n_gap, n_phase, n_t,
                              smoke_test)
    column_doc = build_column_info(n_freq, n_gap, n_phase, n_t)

    payload = {
        "data": data_final,
        "columns": COLUMN_NAMES,
        "attrs": metadata,
        "column_doc": column_doc,
    }
    save_pickle(payload, pkl_path)

    meta_path = os.path.join(script_dir, "metadata.json")
    cols_path = os.path.join(script_dir, "column_info.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
    with open(cols_path, "w", encoding="utf-8") as fh:
        json.dump(column_doc, fh, indent=2)

    print(f"\nDone!")
    print(f"  Shape       : ({row_idx:,}, {len(COLUMN_NAMES)})")
    print(f"  Pickle      : {pkl_path}  ({os.path.getsize(pkl_path)/1024**2:.1f} MB)")
    print(f"  metadata    : {meta_path}")
    print(f"  column_info : {cols_path}")

    # ── sanity checks ────────────────────────────────────────────────────────
    print(f"\nRunning sanity checks ...")
    errors = []

    if row_idx != n_total_rows:
        errors.append(f"  [FAIL] Row count: got {row_idx:,}, expected {n_total_rows:,}")
    else:
        print(f"  [PASS] Row count: {row_idx:,} = ({n_freq}+{n_gap}+{n_phase}) x {n_t}")

    n_nan = int(np.isnan(data_final).sum())
    n_inf = int(np.isinf(data_final).sum())
    if n_nan or n_inf:
        errors.append(f"  [FAIL] {n_nan} NaN and {n_inf} Inf values present")
    else:
        print(f"  [PASS] No NaN or Inf values")

    pop = data_final[:, COL["population"]]
    if pop.min() < -1e-3:
        errors.append(f"  [FAIL] Negative population: min={pop.min():.4f}")
    else:
        print(f"  [PASS] Population non-negative: [{pop.min():.4f}, {pop.max():.4f}]")

    panels = np.unique(data_final[:, COL["panel_id"]]).astype(int).tolist()
    if panels != [0, 1, 2]:
        errors.append(f"  [FAIL] Expected panels [0,1,2], got {panels}")
    else:
        print(f"  [PASS] Panels present: {panels} = {PANEL_NAMES}")

    ts = data_final[:, COL["timestamp_ns"]]
    if ts.min() < -1e-6 or abs(ts.max() - tlist[-1]) > 1e-3:
        errors.append(f"  [FAIL] Timestamp range: [{ts.min():.3f}, {ts.max():.3f}]")
    else:
        print(f"  [PASS] Timestamp range: [{ts.min():.3f}, {ts.max():.3f}] ns")

    p0 = data_final[:, COL["panel_id"]] == 0
    p1 = data_final[:, COL["panel_id"]] == 1
    p2 = data_final[:, COL["panel_id"]] == 2

    # Structural invariants that must hold across the three panels.
    ok_single = (np.all(data_final[p0, COL["amp2"]] == 0.0) and
                 np.all(data_final[p0, COL["pulse2_ns"]] == 0.0) and
                 np.all(data_final[p0, COL["phase2_rad"]] == 0.0))
    if not ok_single:
        errors.append("  [FAIL] panel 0 should be single-pulse (amp2/pulse2/phase2 = 0)")
    else:
        print("  [PASS] panel 0 is single-pulse (amp2=pulse2=phase2=0)")

    ok_two = (np.all(data_final[p1 | p2, COL["amp2"]] == AMP_DRIVE) and
              np.all(data_final[p1 | p2, COL["pulse2_ns"]] == PULSE_NS))
    if not ok_two:
        errors.append("  [FAIL] panels 1,2 should be two-pulse (amp2, pulse2_ns set)")
    else:
        print("  [PASS] panels 1,2 are two-pulse (amp2, pulse2_ns set)")

    ok_p1 = np.all(data_final[p1, COL["phase2_rad"]] == 0.0)
    ok_p2 = np.all(data_final[p2, COL["gap_ns"]] == FIXED_GAP_NS)
    if not (ok_p1 and ok_p2):
        errors.append("  [FAIL] panel 1 must hold phase2=0; panel 2 must hold gap=150")
    else:
        print("  [PASS] panel 1 phase2==0; panel 2 gap==150 ns")

    for mask, col, name, expected in [
        (p0, "drive_frequency_GHz", "drive freqs (panel 0)", n_freq),
        (p1, "gap_ns", "gaps (panel 1)", n_gap),
        (p2, "phase2_rad", "phases (panel 2)", n_phase),
    ]:
        got = len(np.unique(data_final[mask, COL[col]]))
        if got != expected:
            errors.append(f"  [FAIL] Expected {expected} unique {name}, got {got}")
        else:
            print(f"  [PASS] Unique {name}: {got}")

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

    return pkl_path


if __name__ == "__main__":

    _script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Build the Experiment 9 simulated dataset (long format) as a "
        "pickle and a CSV (N=2 TLS separation & relative-phase control)."
    )
    parser.add_argument("--output_dir", type=str, default=_script_dir,
                        help="Where to write experiment_9/ (default: next to this script).")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel solver processes (real run only).")
    parser.add_argument("--no_csv", action="store_true",
                        help="Skip the CSV, write only the pickle.")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Tiny grids + synthetic population; no qutip required.")
    args = parser.parse_args()

    build_dataset(
        output_dir=os.path.abspath(args.output_dir),
        workers=args.workers,
        write_csv_file=not args.no_csv,
        smoke_test=args.smoke_test,
    )
