# Experiment 8 — Amplitude & Multi-Pulse Control (N = 4 TLS simulation)

Numerical Broadband Cryogenic Transient Dielectric Spectroscopy (BCTDS) study of
**amplitude and multi-pulse coherent control** of an ensemble of **four coupled
two-level systems (TLS)**. A square microwave drive pulse excites the ensemble
and the collective excitation ⟨σ⁺σ⁻⟩ is followed as it rings down.

> **This dataset is simulation output, not measured data.** There is no
> instrument, no I/Q. The dynamics are obtained by solving the **Lindblad master
> equation** (QuTiP `mesolve`). The single observable, `population` = ⟨σ⁺σ⁻⟩, is
> computed by the solver.

---

## 1. What this experiment does

Three regimes are simulated (kept here as three "panels"), stored as one long
table and distinguished by `panel_id`:

- **panel 0 — ring-down map.** One 200 ns pulse at fixed amplitude; the **drive
  frequency** is swept 3.0–5.0 GHz (400 values). The drive frequency that
  maximizes the post-pulse ring-down, **`FREQ_STAR`**, is selected here and
  reused in panels 1 and 2. It is **recomputed** (argmax of the post-pulse tail
  population), never hard-coded.
- **panel 1 — amplitude sweep.** A single pulse at `FREQ_STAR` whose amplitude
  **A₁** is swept 0 → 0.10 (60 values). Reveals collapse-and-revival that
  intensifies with amplitude.
- **panel 2 — two-pulse sweep.** Two pulses at `FREQ_STAR`, gap 100 ns. The
  **second pulse's amplitude A₂** is swept 0 → 0.10 (60 values) while **A₁ is
  held fixed** at 0.10. The second pulse interferes with the first pulse's
  residual ring-down — the coherent-control / memory effect.

## 2. The released dataset

**Format:** long — **one row per time sample**. Nine columns:

| Column | Type | Unit | Description |
|---|---|---|---|
| `panel_id` | float32 | 0/1/2 | Regime: 0 ring-down map, 1 amplitude sweep, 2 two-pulse sweep |
| `drive_frequency_GHz` | float32 | GHz (≡ ns⁻¹) | Drive frequency — swept in panel 0; `FREQ_STAR` in panels 1, 2 |
| `amp1` | float32 | — | Pulse-1 amplitude — swept in panel 1; fixed 0.10 elsewhere |
| `amp2` | float32 | — | Pulse-2 amplitude — swept in panel 2 (A₁ fixed); 0 when no 2nd pulse |
| `pulse1_ns` | float32 | ns | Pulse-1 duration (200 ns, constant) |
| `gap_ns` | float32 | ns | Inter-pulse gap (100 ns in panel 2; 0 otherwise) |
| `pulse2_ns` | float32 | ns | Pulse-2 duration (200 ns in panel 2; 0 otherwise) |
| `timestamp_ns` | float32 | ns | Simulation time within the trace; 0–1600 ns, ≈1.6016 ns/step |
| `population` | float32 | — | ⟨σ⁺σ⁻⟩ collective excitation — **the output** |

- **Rows:** (400 freqs + 60 A₁ + 60 A₂) × 1000 samples = **520,000**
- **One trace** = 1000 consecutive rows sharing a panel + swept-knob value.
- **Row ordering:** panel 0 → 1 → 2; within a panel, ascending swept knob, then time.

## 3. Simulated system & conditions

Four coupled TLS evolved under a Lindblad master equation. Bare frequencies drawn
`uniform[3.0, 5.0] GHz` with **seed 2072025**, giving
ω₁…₄/2π = **3.49, 3.17, 4.10, 4.19 GHz**. Dipole–dipole **XX** couplings drawn
`uniform[−50, 50] MHz` (code `−0.05…0.05`). Collective decay **Γ/2π = 2.0 MHz**
(code `0.002`); pure dephasing `γφ = 0`. Drive-frequency-maximizing point
**ωd/2π = `FREQ_STAR` = 4.15 GHz**.

**Unit convention:** frequencies are used numerically as inverse nanoseconds
(GHz ≡ ns⁻¹) with **no factor of 2π** inside the solver; amplitudes are
dimensionless (A/2π = 100 MHz ↔ code `0.10`); times in ns.

## 4. Constant parameters (in metadata, not columns)

`N_TLS`, the four TLS frequencies, the coupling matrix, γ, the seed, and the time
grid are single-valued for the whole run and live in `metadata.json` rather than
as repeated columns. Pulse shape is square with a 1 ns raised-cosine turn-on.

## 5. Provenance & correctness

- **Panel c** sweeps the **second pulse amplitude A₂** with **A₁ fixed** — this
  dataset follows that convention exactly.
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
| `experiment_8/experiment_8_dataset_long.pkl` | `data` — array `(520_000, 9)` float32; `columns`; `attrs`; `column_doc` |
| `experiment_8/experiment_8_dataset_long.csv` | Same table as CSV |
| `experiment_8/experiment_8_run.log` | Per-run build + sanity-check log (git-ignored) |
| `metadata.json` | Data-feature schema header + resolved run values — regenerated every run |
| `column_info.json` | Data-feature schema (grouped rows, colour legend) + stored-column map — regenerated every run |

## 7. Loading

```python
import pickle, pandas as pd

with open("experiment_8/experiment_8_dataset_long.pkl", "rb") as fh:
    payload = pickle.load(fh)
df = pd.DataFrame(payload["data"], columns=payload["columns"])

# one two-pulse trace at the largest second-pulse amplitude (1000 rows):
m = (df["panel_id"] == 2) & (df["amp2"] == df["amp2"].max())
trace = df[m].sort_values("timestamp_ns")
```

## 8. Rebuilding

Requires `qutip >= 5` (plus `numpy`, `pandas`, `tqdm`). Heavy — 520 solves; run
on a workstation/cluster:

```
python experiment_8_dataset_creation.py --workers 16
```

Plumbing-only check without qutip (tiny synthetic grids; write elsewhere so the
real dataset is not overwritten):

```
python experiment_8_dataset_creation.py --smoke-test --output_dir /tmp/exp8_check
```

Simulated by the Fitzpatrick Lab, Dartmouth College.
