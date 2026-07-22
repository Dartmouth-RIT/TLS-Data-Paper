"""
experiment_8_dataset_creation.py
================================

WHAT THIS IS — A SIMULATION, NOT A MEASUREMENT
    Experiment 8 is produced entirely on a computer. There is no
    instrument, no I and no Q here. A model of the physics is written down and
    solved numerically; the "data" is the solver's output. The whole point of
    this script is to run that same model and store its result
    in a shareable table.

WHAT IS BEING MODELLED
    Real materials contain microscopic defects called TWO-LEVEL SYSTEMS (TLS).
    Each behaves like a tiny quantum switch that can sit in one of two states.
    They are a leading source of noise in superconducting quantum computers, so
    the goal is to understand and control them. This experiment models N = 4
    such defects that are COUPLED to one another (they can swap energy), sitting
    in an environment that slowly leaks their energy away (dissipation).

    The equation of motion is a LINDBLAD MASTER EQUATION — the standard way to
    follow a small quantum system that is also losing energy to its
    surroundings. It is solved with QuTiP's `mesolve`. None of that physics is
    invented here: it is imported from the local `hamiltonian_generator.py`.

THE MEASUREMENT — like striking a bell
    A short microwave DRIVE PULSE is applied. It pumps energy into the coupled
    defects. When the pulse stops, the defects keep re-radiating for a while: a
    fading echo, exactly like a bell still ringing after it is struck. That
    fading echo is the RING-DOWN, and following it in time is the whole point.

THE ONE NUMBER RECORDED — "population"
    At every instant the solver reports one quantity:

        population = <sigma^+ sigma^->   (collective excitation)

    Read it as "how excited the ensemble is right now": zero when everything has
    relaxed to the ground state, larger while the drive is pumping energy in and
    during the ring-down that follows. It is dimensionless and never negative.
    This single column is the OUTPUT of the whole experiment.

WHAT THIS PARTICULAR EXPERIMENT DOES — three panels
    The experiment has three parts (kept here as "panels"), each one block of
    rows:

    panel 0  RING-DOWN MAP.  One 200 ns pulse at a fixed amplitude. The DRIVE
             FREQUENCY is swept across 3.0-5.0 GHz (400 values). This asks: at
             which drive frequency does the ensemble ring the LONGEST after the
             pulse? That best frequency is called FREQ_STAR and is reused by the
             other two panels. (It is not hard-coded; it is recomputed from this
             panel's own output, by the rule described below.)

    panel 1  AMPLITUDE SWEEP.  A single pulse, now parked at FREQ_STAR, whose
             AMPLITUDE A1 is swept from 0 to 0.10 (60 values). This shows how the
             ring-down grows as the drive is turned up.

    panel 2  TWO-PULSE SWEEP.  Two pulses at FREQ_STAR. The first is fixed
             (A1 = 0.10, 200 ns); after a 100 ns gap a SECOND pulse fires whose
             AMPLITUDE A2 is swept from 0 to 0.10 (60 values). The second pulse
             lands while the ensemble is still ringing from the first, so the two
             responses interfere — this is the coherent-control knob.

UNIT CONVENTION  (inherited from the model, not chosen here)
    Frequencies (drive, TLS, coupling) are used numerically as inverse
    nanoseconds, i.e. a value of 3.4 means 3.4 GHz with NO factor of 2*pi
    applied inside the solver. This is the convention stated in
    hamiltonian_generator.run_simulation_single_pulse and is preserved as-is.
    Amplitudes A1, A2 are dimensionless drive strengths. Times are nanoseconds.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Long format" means the table is tall and thin: every row is ONE instant in
time from ONE simulated trace, and the columns repeat the settings that were in
force at that instant. It is the shape pandas, SQL and most ML tooling expect.
One complete ring-down trace = 1000 consecutive rows.

9 columns, one row per time sample:

    col 0 — panel_id             0 = ring-down map, 1 = amplitude sweep,
                                 2 = two-pulse sweep (which block this row is in)
    col 1 — drive_frequency_GHz  drive frequency (swept in panel 0; FREQ_STAR in 1, 2)
    col 2 — amp1                 amplitude of pulse 1 (swept in panel 1)
    col 3 — amp2                 amplitude of pulse 2 (swept in panel 2; 0 when no 2nd pulse)
    col 4 — pulse1_ns            duration of pulse 1 (ns)
    col 5 — gap_ns               inter-pulse gap (ns; 0 when there is no 2nd pulse)
    col 6 — pulse2_ns            duration of pulse 2 (ns; 0 when there is no 2nd pulse)
    col 7 — timestamp_ns         simulation time of this sample (ns)
    col 8 — population           <sigma+ sigma-> collective excitation (the OUTPUT)

Everything that is a SINGLE fixed number for the whole run — N_TLS, the four TLS
frequencies, the coupling matrix, gamma, the random seed, the time grid, and
FREQ_STAR — is NOT repeated on every row. It is recorded once in metadata.json.
What remains as columns is the panel selector, the swept knobs, the per-panel
pulse timing, the clock, and the single simulated observable.

Total rows (full run):
    panel 0 : 400 drive freqs x 1000 time samples = 400,000
    panel 1 :  60 amplitudes  x 1000 time samples =  60,000
    panel 2 :  60 amplitudes  x 1000 time samples =  60,000
                                            total  = 520,000

Timestamp spacing: 1600 ns / (1000 - 1) ~= 1.6016 ns per sample

RECORDING ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    panel_id (0, 1, 2)
      -> swept knob   (400 drive freqs, then 60 A1, then 60 A2)
           -> timestamp_ns (0 ... 1600 ns -- 1000 values, the fast time axis)

OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    08_amplitude_control/experiment_8/experiment_8_dataset_long.pkl
    08_amplitude_control/experiment_8/experiment_8_dataset_long.csv
    08_amplitude_control/experiment_8/experiment_8_run.log   (reverification log)
    08_amplitude_control/metadata.json
    08_amplitude_control/column_info.json

The run log captures the full build summary and every sanity-check PASS/FAIL
line, so a re-run can be checked against a previous one. It is a *.log file and
is git-ignored (a build artifact, not source).

    payload["data"]          shape (520_000, 9), float32
    payload["columns"]       the 9 column names
    payload["attrs"]         experiment metadata (mirrors metadata.json)
    payload["column_doc"]    per-column semantics (mirrors column_info.json)

To load in Python:

    import pickle
    import pandas as pd

    with open("experiment_8_dataset_long.pkl", "rb") as fh:
        payload = pickle.load(fh)
    df = pd.DataFrame(payload["data"], columns=payload["columns"])

    # one two-pulse trace at the largest second-pulse amplitude (1000 rows):
    m = (df["panel_id"] == 2) & (df["amp2"] == df["amp2"].max())
    trace = df[m].sort_values("timestamp_ns")

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # full run (needs qutip; heavy -- run on a workstation/cluster)
    python experiment_8_dataset_creation.py --workers 8

    # fast plumbing check (no qutip: synthetic population on tiny grids)
    python experiment_8_dataset_creation.py --smoke-test

    Optional arguments:
        --output_dir  where to write experiment_8/ (default: next to this script)
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

# Pulse timing (nanoseconds).
PULSE_RING = 200              # single pulse used in the ring-down map (panel 0)
PULSE1_NS  = PULSE_RING       # pulse-1 duration (panels 1, 2)
GAP_NS     = 100              # idle gap AFTER pulse 1 ends (panel 2)
PULSE2_NS  = 200              # pulse-2 duration (panel 2)

# Drive-frequency sweep (panel 0). Treated numerically as GHz == ns^-1.
F_MIN, F_MAX = 3.0, 5.0
N_FREQ       = 400

# Time grid: 0 to 1600 ns, 1000 points.
T_MAX_NS, N_T = 1600, 1000

# The N = 4 coupled-TLS ensemble. The seed fixes both the TLS frequencies and
# the coupling matrix; the draw ORDER below fixes the ensemble deterministically.
N_TLS        = 4
SEED         = 2072025
J_MIN, J_MAX = -0.05, 0.05    # XX coupling range (J in [-0.05, 0.05] GHz)

# Dissipation: collective decay GAMMA, pure dephasing GAMMA_PHI (off here).
GAMMA, GAMMA_PHI = 0.002, 0.0

# Drive amplitudes (dimensionless).
AMP_BASE   = 0.10             # fixed amplitude for the ring-down map (panel 0)
AMP1_FIXED = 0.10             # fixed pulse-1 amplitude for the two-pulse sweep (panel 2)
N_AMP      = 60
AMP_LO, AMP_HI = 0.0, 0.10    # A1 sweep (panel 1) and A2 sweep (panel 2)

# Panel bookkeeping.
PANEL_NAMES = ["ring_down_map", "amp_sweep", "two_pulse_sweep"]

# Only what varies across rows gets a column; the scalar constants live in
# metadata.json. See the module docstring's FORMAT section.
COLUMN_NAMES = [
    "panel_id",
    "drive_frequency_GHz",
    "amp1",
    "amp2",
    "pulse1_ns",
    "gap_ns",
    "pulse2_ns",
    "timestamp_ns",
    "population",
]

# Column name -> position, so the code below never hard-codes an index.
COL = {name: i for i, name in enumerate(COLUMN_NAMES)}

PICKLE_PROTOCOL = 4


# ─────────────────────────────────────────────────────────────────────────────
# ENSEMBLE SETUP — the exact RNG stream that fixes the ensemble
# ─────────────────────────────────────────────────────────────────────────────

def build_ensemble(smoke_test=False):
    """Return (init_freqs, H_int).

    The seed and draw ORDER are fixed and deterministic:
        np.random.seed(SEED)
        init_freqs = uniform(F_MIN, F_MAX, N_TLS)           # first draw
        H_int      = build_spin_spin_interactions_...(...)   # second draw
    so the same coupling matrix is produced on every run.

    In smoke-test mode qutip is not required, so H_int is returned as the raw
    symmetric coupling matrix (a plain ndarray) instead of a QuTiP operator.
    """
    np.random.seed(SEED)
    init_freqs = np.random.uniform(F_MIN, F_MAX, N_TLS)

    if smoke_test:
        # Reproduce the same second draw so the coupling MATRIX is identical,
        # but do not build QuTiP operators (qutip may not be installed).
        J = np.random.uniform(J_MIN, J_MAX, size=(N_TLS, N_TLS))
        J = np.tril(J, -1) + np.tril(J, -1).T
        return init_freqs, J

    from hamiltonian_generator import build_spin_spin_interactions_random_distribution
    H_int = build_spin_spin_interactions_random_distribution(
        N_TLS, J_MIN, J_MAX, alpha_x=1.0, alpha_y=0.0, alpha_z=0.0
    )
    return init_freqs, H_int


def coupling_matrix_from_seed():
    """Recompute the symmetric XX coupling matrix (for metadata.json only),
    without disturbing any live RNG state used elsewhere."""
    rng_state = np.random.get_state()
    try:
        np.random.seed(SEED)
        _ = np.random.uniform(F_MIN, F_MAX, N_TLS)          # consume init_freqs draw
        J = np.random.uniform(J_MIN, J_MAX, size=(N_TLS, N_TLS))
        J = np.tril(J, -1) + np.tril(J, -1).T
    finally:
        np.random.set_state(rng_state)
    return J


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC POPULATION — smoke-test stand-in for the QuTiP solver.
# NOT physically meaningful; it exists only to exercise the dataset plumbing on
# a machine without qutip. The real run never touches these functions.
# ─────────────────────────────────────────────────────────────────────────────

def _synthetic_single(freq, amp, tlist, init_freqs, pulse_ns):
    """Cheap analytic surrogate for run_simulation_single_pulse (smoke test)."""
    detune = np.min(np.abs(np.asarray(init_freqs) - freq))
    lorentz = 1.0 / (1.0 + (detune / 0.15) ** 2)           # near-resonance envelope
    drive = amp * lorentz * np.sin(
        np.pi * np.clip(tlist / max(pulse_ns, 1e-9), 0, 1)
    ) ** 2
    tail = np.where(tlist > pulse_ns,
                    amp * lorentz * np.exp(-GAMMA * (tlist - pulse_ns)), 0.0)
    pop = np.where(tlist <= pulse_ns, drive, tail)
    return np.clip(pop, 0.0, None).astype(np.float64)


def _synthetic_double(freq, amp1, amp2, pulse1_ns, gap_ns, pulse2_ns,
                      tlist, init_freqs):
    """Cheap analytic surrogate for run_simulation_double_pulse (smoke test)."""
    p1 = _synthetic_single(freq, amp1, tlist, init_freqs, pulse1_ns)
    t2_start = pulse1_ns + gap_ns
    shifted = tlist - t2_start
    p2 = np.where(shifted >= 0,
                  _synthetic_single(freq, amp2, np.clip(shifted, 0, None),
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
    kind = "amp1"   -> single-pulse amplitude sweep at freq_star
    kind = "amp2"   -> two-pulse sweep at freq_star, A1 fixed, param = A2

    The real branch calls run_simulation_single_pulse / run_simulation_double_pulse
    straight out of the local hamiltonian_generator.py. Nothing about the physics
    is re-derived here.
    """
    out = np.zeros((len(param_list), len(tlist)), dtype=np.float64)

    # ── smoke test: synthetic, serial, no qutip ──────────────────────────────
    if smoke_test:
        for i, p in enumerate(param_list):
            if kind == "freq":
                out[i] = _synthetic_single(p, AMP_BASE, tlist, init_freqs, PULSE1_NS)
            elif kind == "amp1":
                out[i] = _synthetic_single(freq_star, p, tlist, init_freqs, PULSE1_NS)
            else:  # amp2
                out[i] = _synthetic_double(freq_star, AMP1_FIXED, p,
                                           PULSE1_NS, GAP_NS, PULSE2_NS,
                                           tlist, init_freqs)
        return out

    # ── real physics: parallel qutip solver ──────────────────────────────────
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from hamiltonian_generator import (
        run_simulation_single_pulse, run_simulation_double_pulse,
    )

    def submit(pool, p):
        if kind == "freq":
            return pool.submit(run_simulation_single_pulse, p, AMP_BASE,
                               tlist, init_freqs, H_int, GAMMA, GAMMA_PHI, PULSE1_NS)
        if kind == "amp1":
            return pool.submit(run_simulation_single_pulse, freq_star, p,
                               tlist, init_freqs, H_int, GAMMA, GAMMA_PHI, PULSE1_NS)
        return pool.submit(run_simulation_double_pulse, freq_star, AMP1_FIXED, p,
                           PULSE1_NS, GAP_NS, PULSE2_NS,
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

def build_metadata(freq_star, init_freqs, n_freq, n_amp, n_t,
                   smoke_test=False) -> dict:
    """Instance metadata: the schema header, the resolved runtime values (actual
    TLS frequencies, FREQ_STAR, coupling matrix), and provenance. The full
    data-feature schema (grouped rows + colour legend) lives in
    build_column_info()."""
    return {
        "schema_title": "Experiment 8 - Data Feature / Metadata Schema",
        "provenance_line": (
            "Fitzpatrick Lab, Dartmouth College | "
            "Numerical N=4 TLS: amplitude and multi-pulse (two-pulse) control"
        ),
        "experiment_id": "experiment_8",
        "data_type": "simulation",
        "what_it_shows": (
            "Amplitude and multi-pulse control of a 4-TLS ensemble. a: ring-down "
            "map (single pulse); b: amplitude sweep at the optimal drive frequency "
            "(collapse-and-revival); c: two-pulse protocol (A2 swept, A1 fixed, "
            "gap 100 ns)."
        ),
        "physical_system": {
            "system": "N = 4 coupled TLS, Lindblad master equation",
            "seed": SEED,
            "TLS_frequencies_GHz_resolved": [round(float(f), 4) for f in init_freqs],
            "TLS_frequencies_note": (
                "uniform[3.0, 5.0] GHz, seed 2072025; the resulting "
                "w_i/2pi = 3.49, 3.17, 4.10, 4.19 GHz."
            ),
            "coupling_type": "XX (alpha_x=1, alpha_y=0, alpha_z=0)",
            "coupling_J_range_GHz": [J_MIN, J_MAX],
            "coupling_J_matrix_GHz": coupling_matrix_from_seed().tolist(),
            "gamma_collective": GAMMA,
            "gamma_dephasing": GAMMA_PHI,
        },
        "drive_and_pulse": {
            "drive_frequency_sweep_GHz": [F_MIN, F_MAX],
            "n_drive_frequencies": n_freq,
            "freq_star_GHz": round(float(freq_star), 6),
            "freq_star_rule": (
                "argmax over the panel-a drive-frequency sweep of the population "
                "summed over the post-pulse tail (t > pulse1_ns)."
            ),
            "amp_base": AMP_BASE,
            "amp_sweep_range": [AMP_LO, AMP_HI],
            "n_amp": n_amp,
            "amp1_fixed_panel_c": AMP1_FIXED,
            "pulse1_ns": PULSE1_NS,
            "gap_ns": GAP_NS,
            "pulse2_ns": PULSE2_NS,
        },
        "time_grid": {
            "t_min_ns": 0.0,
            "t_max_ns": T_MAX_NS,
            "n_samples": n_t,
            "one_sample_ns": T_MAX_NS / (n_t - 1) if n_t > 1 else 0.0,
        },
        "output": {
            "observable": "<sigma+ sigma-> collective excitation (dimensionless)",
            "panels": PANEL_NAMES,
        },
        "provenance": {
            "physics_module": "hamiltonian_generator.py (QuTiP-5 API shim only)",
            "attribution": "Uses code and simulation methods from the "
                           "Fitzpatrick Lab, Dartmouth College.",
            "panel_c_note": "Panel c sweeps A2 (second pulse) with A1 fixed.",
            "no_new_physics": True,
            "smoke_test": smoke_test,
        },
    }


def build_column_info(n_freq, n_amp, n_t) -> dict:
    """The data-feature / metadata schema for this experiment: grouped feature
    rows, a colour legend, and the code-variable mapping for each knob.
    `actual_stored_columns` then records how this long-format dataset physically
    stores those features as columns."""

    def row(knob, dtype, nulls, code_var, value_range, in_file, notes, colour):
        return {
            "column_or_knob": knob,
            "data_type": dtype,
            "can_have_nulls": nulls,
            "maps_to_code_variable": code_var,
            "value_or_range": value_range,
            "in_a_stored_data_file": in_file,
            "derivation_or_notes": notes,
            "colour": colour,
        }

    return {
        "schema_title": "Experiment 8 - Data Feature / Metadata Schema",
        "provenance_line": (
            "Fitzpatrick Lab, Dartmouth College | "
            "Numerical N=4 TLS: amplitude and multi-pulse (two-pulse) control"
        ),
        "colour_legend": {
            "green": "Physical metadata / simulation INPUT feature (set in the script)",
            "blue": "Numerical / solver setting (grid, step, window)",
            "orange": "Computed OUTPUT array (population, phase, FFT)",
        },
        "sections": [
            {
                "section": "OVERVIEW",
                "rows": [
                    row("what_it_shows", "Text", "-", "experiment_8_dataset_creation.py",
                        "Amplitude and multi-pulse control of a 4-TLS ensemble", "No",
                        "a: ring-down map (single pulse); b: amplitude sweep at the "
                        "optimal drive frequency (collapse-and-revival); c: two-pulse "
                        "protocol (A2 swept, A1 fixed, gap 100 ns).", "green"),
                ],
            },
            {
                "section": "PHYSICAL SYSTEM METADATA - the simulated TLS ensemble",
                "rows": [
                    row("system", "String", "No", "N_TLS",
                        "N = 4 coupled TLS, Lindblad master equation", "No",
                        "Ensemble size.", "green"),
                    row("TLS_frequencies", "Float", "No", "init_freqs",
                        "uniform[3.0, 5.0] GHz, seed 2072025 -> "
                        "{3.49, 3.17, 4.10, 4.19} GHz", "No",
                        "Bare frequencies drawn with a fixed seed; the resulting "
                        "w_i/2pi = 3.49, 3.17, 4.10, 4.19 GHz.", "green"),
                    row("coupling_J", "Float", "No",
                        "build_spin_spin_interactions_random_distribution",
                        "J/2pi in [-50, 50] MHz (code uniform(-0.05, 0.05)), XX only",
                        "No", "Random symmetric dipole-dipole couplings between every "
                        "pair.", "green"),
                    row("dissipation_gamma", "Float", "No", "GAMMA, GAMMA_PHI",
                        "Gamma/2pi = 2.0 MHz (code 0.002); gamma_phi = 0", "No",
                        "Collective relaxation rate.", "green"),
                ],
            },
            {
                "section": "DRIVE & PULSE PARAMETERS",
                "rows": [
                    row("drive_frequency", "Float", "No", "FREQ_AXIS / FREQ_STAR",
                        "3.0-5.0 GHz, 400 pts (panel a); optimal wd/2pi = 4.15 GHz "
                        "(panels b,c)", "No",
                        "Swept in the ring-down map; fixed at the ring-down-"
                        "maximizing freq for b,c.", "green"),
                    row("drive_amplitude", "Float", "No",
                        "AMP_BASE / AMP_SWEEP / AMP2_SWEEP",
                        "A1/2pi = 100 MHz base (code 0.10); sweeps 0 -> 0.10 in 60 "
                        "steps", "No",
                        "Fixed for the ring-down map; swept 0->0.10 for the amplitude "
                        "panels (pulse-1 in b, pulse-2 in c).", "green"),
                    row("pulse_timing", "Float", "No",
                        "PULSE_RING / PULSE1_NS / GAP_NS / PULSE2_NS",
                        "single pulse: 200 ns; two-pulse: 200 ns / gap 100 ns / "
                        "200 ns", "No",
                        "tau = 200 ns; two-pulse protocol with inter-pulse gap "
                        "tau_g = 100 ns.", "green"),
                ],
            },
            {
                "section": "TIME GRID",
                "rows": [
                    row("time_grid", "Float", "No", "T_MAX_NS, N_T",
                        "0 to 1600 ns, 1000 points", "No",
                        "Simulation time axis.", "blue"),
                ],
            },
            {
                "section": "COMPUTED OUTPUT ARRAY",
                "rows": [
                    row("population", "Float", "No", "pop maps",
                        "<sigma+ sigma-> vs (freq,time), (amp,time), (amp2,time)",
                        "No", "Collective excitation; ring-down, amplitude sweep, "
                        "two-pulse sweep.", "orange"),
                ],
            },
        ],
        "actual_stored_columns": {
            "note": (
                "The schema above (in_a_stored_data_file = No) describes the "
                "original plotting workflow, which stored nothing. THIS dataset "
                "persists the features as a long-format table; below is how each "
                "pkl/csv row is laid out."
            ),
            "format": "long (one row per time sample)",
            "n_rows": (n_freq + n_amp + n_amp) * n_t,
            "n_columns": len(COLUMN_NAMES),
            "columns": list(COLUMN_NAMES),
            "column_notes": {
                "panel_id": "0 ring-down map, 1 amplitude sweep, 2 two-pulse sweep",
                "drive_frequency_GHz": "swept in panel 0; FREQ_STAR in 1,2 (green)",
                "amp1": "pulse-1 amplitude; swept in panel 1; fixed 0.10 else (green)",
                "amp2": "pulse-2 amplitude; swept in panel 2 (A1 fixed); 0 else (green)",
                "pulse1_ns": "200 ns constant (green)",
                "gap_ns": "100 ns in panel 2; 0 else (green)",
                "pulse2_ns": "200 ns in panel 2; 0 else (green)",
                "timestamp_ns": "0-1600 ns, 1000 samples (blue)",
                "population": "<sigma+ sigma-> output (orange)",
            },
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
    reverification, then delegates to _build_dataset_impl. The log is written to
    experiment_8/experiment_8_run.log (a *.log file, so it is git-ignored) and
    is overwritten on each run so it always reflects the latest build."""
    exp_dir = os.path.join(output_dir, "experiment_8")
    os.makedirs(exp_dir, exist_ok=True)
    log_path = os.path.join(exp_dir, "experiment_8_run.log")

    original_stdout = sys.stdout
    with open(log_path, "w", encoding="utf-8") as log_fh:
        sys.stdout = _Tee(original_stdout, log_fh)
        try:
            print(f"# Experiment 8 run log — "
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
    output_dir = os.path.join(output_dir, "experiment_8")
    os.makedirs(output_dir, exist_ok=True)
    pkl_path = os.path.join(output_dir, "experiment_8_dataset_long.pkl")
    csv_path = os.path.join(output_dir, "experiment_8_dataset_long.csv")

    # Grids (shrunk in smoke test so it finishes in seconds without qutip).
    if smoke_test:
        n_freq, n_amp, n_t = 8, 5, 20
    else:
        n_freq, n_amp, n_t = N_FREQ, N_AMP, N_T

    freq_axis = np.linspace(F_MIN, F_MAX, n_freq)
    amp_sweep = np.linspace(AMP_LO, AMP_HI, n_amp)
    tlist     = np.linspace(0.0, T_MAX_NS, n_t)

    n_total_rows = (n_freq + n_amp + n_amp) * n_t

    print(f"\nExperiment 8 dataset builder {'(SMOKE TEST)' if smoke_test else ''}")
    print(f"Format          : long (one row per time sample)")
    print(f"System          : N={N_TLS} coupled TLS, Lindblad master equation")
    print(f"Panels          : 0=ring-down map, 1=amp sweep, 2=two-pulse sweep")
    print(f"Drive freqs     : {n_freq}  ({F_MIN}-{F_MAX} GHz, panel 0)")
    print(f"Amplitudes      : {n_amp}  ({AMP_LO}-{AMP_HI}, panels 1 & 2)")
    print(f"Time samples    : {n_t}  (0-{T_MAX_NS} ns)")
    print(f"Total rows      : ({n_freq}+{n_amp}+{n_amp}) x {n_t} = {n_total_rows:,}")
    print(f"Columns         : {COLUMN_NAMES}\n")

    # ── ensemble ─────────────────────────────────────────────────────────────
    init_freqs, H_int = build_ensemble(smoke_test=smoke_test)
    print(f"TLS freqs       : {np.round(init_freqs, 3).tolist()} GHz (seed {SEED})\n")

    # ── panel 0: ring-down map + FREQ_STAR ───────────────────────────────────
    print("[panel 0] ring-down map ...")
    pop_ring = _run_sweep("freq", freq_axis, None, tlist, init_freqs, H_int,
                          workers, smoke_test)
    mask_tail = tlist > PULSE1_NS
    if mask_tail.any():
        freq_star = float(freq_axis[np.argmax(pop_ring[:, mask_tail].sum(axis=1))])
    else:                                     # tiny smoke grid may have no tail sample
        freq_star = float(freq_axis[np.argmax(pop_ring.sum(axis=1))])
    print(f"  FREQ_STAR     : {freq_star:.4f} GHz")

    # ── panel 1: single-pulse amplitude sweep ────────────────────────────────
    print("\n[panel 1] amplitude sweep ...")
    pop_amp = _run_sweep("amp1", amp_sweep, freq_star, tlist, init_freqs, H_int,
                         workers, smoke_test)

    # ── panel 2: two-pulse (A2) sweep ────────────────────────────────────────
    print("\n[panel 2] two-pulse sweep ...")
    pop_double = _run_sweep("amp2", amp_sweep, freq_star, tlist, init_freqs, H_int,
                            workers, smoke_test)

    # ── assemble the long table ──────────────────────────────────────────────
    data_all = np.empty((n_total_rows, len(COLUMN_NAMES)), dtype=np.float32)
    row_idx = 0

    def emit(panel_id, drive_freq, a1, a2, p1, gap, p2, pop_matrix, param_iter):
        nonlocal row_idx
        for row_i, _param in enumerate(param_iter):
            end = row_idx + n_t
            data_all[row_idx:end, COL["panel_id"]] = panel_id
            data_all[row_idx:end, COL["drive_frequency_GHz"]] = (
                drive_freq[row_i] if np.ndim(drive_freq) else drive_freq)
            data_all[row_idx:end, COL["amp1"]] = a1[row_i] if np.ndim(a1) else a1
            data_all[row_idx:end, COL["amp2"]] = a2[row_i] if np.ndim(a2) else a2
            data_all[row_idx:end, COL["pulse1_ns"]] = p1
            data_all[row_idx:end, COL["gap_ns"]] = gap
            data_all[row_idx:end, COL["pulse2_ns"]] = p2
            data_all[row_idx:end, COL["timestamp_ns"]] = tlist
            data_all[row_idx:end, COL["population"]] = pop_matrix[row_i]
            row_idx = end

    # panel 0: drive freq swept; single pulse -> amp1=AMP_BASE, no 2nd pulse
    emit(0, freq_axis, AMP_BASE, 0.0, PULSE1_NS, 0.0, 0.0, pop_ring, freq_axis)
    # panel 1: amp1 swept at freq_star; single pulse
    emit(1, freq_star, amp_sweep, 0.0, PULSE1_NS, 0.0, 0.0, pop_amp, amp_sweep)
    # panel 2: amp2 swept at freq_star; two pulses, amp1 fixed
    emit(2, freq_star, AMP1_FIXED, amp_sweep, PULSE1_NS, GAP_NS, PULSE2_NS,
         pop_double, amp_sweep)

    data_final = data_all[:row_idx]

    # ── save pickle + JSON sidecars ──────────────────────────────────────────
    print(f"\nSaving to {pkl_path} ...")
    metadata = build_metadata(freq_star, init_freqs, n_freq, n_amp, n_t, smoke_test)
    column_doc = build_column_info(n_freq, n_amp, n_t)

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
        print(f"  [PASS] Row count: {row_idx:,} = ({n_freq}+{n_amp}+{n_amp}) x {n_t}")

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
        errors.append(f"  [FAIL] Timestamp range: [{ts.min():.3f}, {ts.max():.3f}] "
                      f"(expected [0, {tlist[-1]:.3f}])")
    else:
        print(f"  [PASS] Timestamp range: [{ts.min():.3f}, {ts.max():.3f}] ns")

    # pulse2_ns and gap_ns must be non-zero only for panel 2.
    c_mask = data_final[:, COL["panel_id"]] == 2
    ok_p2 = (np.all(data_final[c_mask, COL["pulse2_ns"]] == PULSE2_NS) and
             np.all(data_final[~c_mask, COL["pulse2_ns"]] == 0.0))
    ok_gap = (np.all(data_final[c_mask, COL["gap_ns"]] == GAP_NS) and
              np.all(data_final[~c_mask, COL["gap_ns"]] == 0.0))
    if not (ok_p2 and ok_gap):
        errors.append("  [FAIL] gap_ns/pulse2_ns should be non-zero only for panel 2")
    else:
        print("  [PASS] gap_ns/pulse2_ns non-zero only for panel 2 (two-pulse)")

    # amp2 must be zero everywhere except panel 2.
    if np.any(data_final[~c_mask, COL["amp2"]] != 0.0):
        errors.append("  [FAIL] amp2 non-zero outside panel 2")
    else:
        print("  [PASS] amp2 is zero outside panel 2")

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
        description="Build the Experiment 8 simulated dataset (long format) as a "
        "pickle and a CSV (N=4 TLS amplitude and multi-pulse control)."
    )
    parser.add_argument(
        "--output_dir", type=str, default=_script_dir,
        help="Where to write experiment_8/ (default: next to this script).",
    )
    parser.add_argument(
        "--workers", type=int, default=4,
        help="Parallel solver processes (real run only; ignored in smoke test).",
    )
    parser.add_argument(
        "--no_csv", action="store_true", help="Skip the CSV, write only the pickle.",
    )
    parser.add_argument(
        "--smoke-test", action="store_true",
        help="Tiny grids + synthetic population; no qutip required.",
    )
    args = parser.parse_args()

    build_dataset(
        output_dir=os.path.abspath(args.output_dir),
        workers=args.workers,
        write_csv_file=not args.no_csv,
        smoke_test=args.smoke_test,
    )
