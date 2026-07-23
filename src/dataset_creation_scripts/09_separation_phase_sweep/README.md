# Experiment 9 — Separation & Relative-Phase Control (N = 2 TLS simulation)

Numerical Broadband Cryogenic Transient Dielectric Spectroscopy (BCTDS) study of
how the **separation** and **relative phase** of two drive pulses steer the
ring-down of a **pair of coupled two-level systems (TLS)**. A square microwave
pulse excites the pair and the collective excitation ⟨σ⁺σ⁻⟩ is followed as it
rings down.

> **This dataset is simulation output, not measured data.** There is no
> instrument, no I/Q. The dynamics are obtained by solving the **Lindblad master
> equation** (QuTiP `mesolve`). The single observable, `population` = ⟨σ⁺σ⁻⟩, is
> computed by the solver.

---

## 1. What this experiment does

Three regimes are simulated (kept here as three "panels"), stored as one long
table and distinguished by `panel_id`:

- **panel 0 — ring-down map.** One 200 ns pulse; the **drive frequency** is swept
  2.0–5.0 GHz (400 values). The frequency that maximizes the post-pulse ring-down,
  **`FREQ_STAR`**, is selected here and reused in panels 1 and 2. It is
  **recomputed** (argmax of the post-pulse tail population), never hard-coded.
- **panel 1 — gap sweep.** Two pulses at `FREQ_STAR`, equal amplitude, the second
  **in phase** with the first (φ₂ = 0). The **gap** between them is swept 0 → 800 ns
  (120 values), showing how the response changes as the second pulse lands later
  into the ring-down.
- **panel 2 — phase sweep.** Two pulses at `FREQ_STAR`, gap fixed at 150 ns. The
  **relative phase φ₂** of the second pulse is swept 0 → 2π (120 values). Because
  the second pulse arrives while the pair is still ringing, its phase decides
  whether the two responses add or cancel — the coherent-control knob.

## 2. The released dataset

**Format:** long — **one row per time sample**. Ten columns:

| Column | Type | Unit | Description |
|---|---|---|---|
| `panel_id` | float32 | 0/1/2 | Regime: 0 ring-down map, 1 gap sweep, 2 phase sweep |
| `drive_frequency_GHz` | float32 | GHz (≡ ns⁻¹) | Drive frequency — swept in panel 0; `FREQ_STAR` in panels 1, 2 |
| `amp1` | float32 | — | Pulse-1 amplitude (0.12, constant) |
| `amp2` | float32 | — | Pulse-2 amplitude (0.12 in panels 1,2; 0 in panel 0) |
| `pulse1_ns` | float32 | ns | Pulse-1 duration (200 ns) |
| `gap_ns` | float32 | ns | Inter-pulse gap — swept in panel 1; 150 ns in panel 2; 0 in panel 0 |
| `pulse2_ns` | float32 | ns | Pulse-2 duration (200 ns in panels 1,2; 0 in panel 0) |
| `phase2_rad` | float32 | rad | Relative phase of pulse 2 — swept 0–2π in panel 2; 0 elsewhere |
| `timestamp_ns` | float32 | ns | Simulation time within the trace; 0–1600 ns, ≈1.6016 ns/step |
| `population` | float32 | — | ⟨σ⁺σ⁻⟩ collective excitation — **the output** |

- **Rows:** (400 freqs + 120 gaps + 120 phases) × 1000 samples = **640,000**
- **One trace** = 1000 consecutive rows sharing a panel + swept-knob value.
- **Row ordering:** panel 0 → 1 → 2; within a panel, ascending swept knob, then time.

## 3. Simulated system & conditions

Two coupled TLS evolved under a Lindblad master equation. TLS frequencies are
fixed at **3.0 and 4.0 GHz**; a dipole–dipole **XX** coupling is drawn with a
fixed seed (42) from `uniform[−0.05, 0.05]`. Collective decay `γ = 0.002`
(dimensionless); pure dephasing `γφ = 0`. Both pulses use amplitude **0.12**.
The ring-down-maximizing drive frequency is **`FREQ_STAR` = 3.06767 GHz**.

**Unit convention:** frequencies are used numerically as inverse nanoseconds
(GHz ≡ ns⁻¹) with **no factor of 2π** inside the solver; amplitudes are
dimensionless; phase is in radians; times in ns.

## 4. Constant parameters (in metadata, not columns)

`N_TLS`, the two TLS frequencies, the coupling matrix, γ, the seed, and the time
grid are single-valued for the whole run and live in `metadata.json` rather than
as repeated columns. Pulse shape is square with a 1 ns raised-cosine turn-on.

## 5. Provenance & correctness

- **Physics module:** the local `hamiltonian_generator.py`, used unchanged except
  a QuTiP-5 API-compatibility shim (the `mesolve` call was updated from the
  QuTiP-4 form; **no physics change** — same Hamiltonian, operators, master
  equation).
- **Verified:** stored traces were checked against an independent recomputation
  from the same physics functions at the exact grid frequency — **bit-for-bit
  match (diff = 0)** in all three panels.
- Uses code and simulation methods from the **Fitzpatrick Lab, Dartmouth College**.

## 6. Released files

| File | Contents |
|---|---|
| `experiment_9/experiment_9_dataset_long.pkl` | `data` — array `(640_000, 10)` float32; `columns`; `attrs`; `column_doc` |
| `experiment_9/experiment_9_dataset_long.csv` | Same table as CSV |
| `experiment_9/experiment_9_run.log` | Per-run build + sanity-check log (git-ignored) |
| `metadata.json` | Data-feature schema header + resolved run values — regenerated every run |
| `column_info.json` | Per-column semantics and units — regenerated every run |

## 7. Loading

```python
import pickle, numpy as np, pandas as pd

with open("experiment_9/experiment_9_dataset_long.pkl", "rb") as fh:
    payload = pickle.load(fh)
df = pd.DataFrame(payload["data"], columns=payload["columns"])

# one phase-sweep trace near phase = pi (1000 rows):
m = df["panel_id"] == 2
phases = df[m]["phase2_rad"].unique()
near_pi = phases[np.argmin(np.abs(phases - np.pi))]
trace = df[m & (df["phase2_rad"] == near_pi)].sort_values("timestamp_ns")
```

## 8. Rebuilding

Requires `qutip >= 5` (plus `numpy`, `pandas`, `tqdm`). ~640 solves:

```
python experiment_9_dataset_creation.py --workers 16
```

Plumbing-only check without qutip (tiny synthetic grids; write elsewhere so the
real dataset is not overwritten):

```
python experiment_9_dataset_creation.py --smoke-test --output_dir /tmp/exp9_check
```

Simulated by the Fitzpatrick Lab, Dartmouth College.
