# Experiment 10 — Ring-down & Phase Sharpening vs Pulse Duration (N = 2 TLS simulation)

Numerical Broadband Cryogenic Transient Dielectric Spectroscopy (BCTDS) study of
how the ring-down and the inter-TLS phase relationship **sharpen** as the drive
pulse gets longer, for two two-level systems (TLS) at **4.0 and 4.1 GHz**.

> **This dataset is simulation output, not measured data.** The dynamics are
> obtained by solving the **Lindblad master equation** (QuTiP `mesolve`).

> ### ⚠ IMPORTANT — the model is *uncoupled*
> The physics module builds an XX coupling (J = 0.05) but the solver replaces it
> with `sum(interactions[i,j] for i in range(N) for j in range(i))`, which for
> N = 2 evaluates to **exactly 0**. The two TLS therefore evolve **independently**
> and their signals simply **beat** at their 0.1 GHz difference. This is a
> faithfully reproduced quirk of the original implementation — **do not treat this
> dataset as a coupled system.** See `metadata.json → model.coupling_note`.

---

## 1. What this experiment does

One drive-frequency sweep is repeated over a grid of pulse durations, producing
**three separate products** (each saved as its own table):

1. **Post-pulse map** — for every pulse duration (20–200 ns, 50 values) and drive
   frequency (3.0–5.0 GHz, 400 values), ⟨σ⁺σ⁻⟩ sampled at the **first time sample
   after the pulse ends**. One scalar per (pulse, frequency).
2. **Population traces** — for three representative pulses (shortest, middle,
   longest), the **full** ⟨σ⁺σ⁻⟩ time trace at every drive frequency.
3. **Phase-V FFT** — for the same three pulses, the normalized magnitude FFT of the
   inter-TLS phase difference φ(t) = arg⟨σ⁺₁⟩ − arg⟨σ⁺₂⟩ over the 0–400 ns window,
   per drive frequency, shown up to 150 MHz. This "phase V" reveals the beat
   structure.

## 2. The released dataset

This dataset comprises **three long-format tables**. Observables are computed by
the solver, not measured.

**`experiment_10_postpulse_map`** — 50 × 400 = **20,000 rows**

| Column | Type | Unit | Description |
|---|---|---|---|
| `pulse_duration_ns` | float32 | ns | Drive pulse duration (20–200 ns, 50 values) |
| `drive_frequency_GHz` | float32 | GHz | Drive frequency (3.0–5.0 GHz, 400 values) |
| `postpulse_population` | float32 | — | ⟨σ⁺σ⁻⟩ at the first sample after the pulse ends |

**`experiment_10_population_traces`** — 3 × 400 × 1000 = **1,200,000 rows**

| Column | Type | Unit | Description |
|---|---|---|---|
| `pulse_duration_ns` | float32 | ns | One of the three representative pulses |
| `drive_frequency_GHz` | float32 | GHz | Drive frequency (3.0–5.0 GHz, 400 values) |
| `timestamp_ns` | float32 | ns | Simulation time (0–1000 ns, 1000 samples) |
| `population` | float32 | — | Full ⟨σ⁺σ⁻⟩ time trace |

**`experiment_10_phaseV_fft`** — 3 × 400 × 61 ≈ **73,200 rows**

| Column | Type | Unit | Description |
|---|---|---|---|
| `pulse_duration_ns` | float32 | ns | One of the three representative pulses |
| `drive_frequency_GHz` | float32 | GHz | Drive frequency (3.0–5.0 GHz, 400 values) |
| `fft_frequency_MHz` | float32 | MHz | Positive FFT frequency of φ(t), 0–150 MHz |
| `normalized_phase_fft` | float32 | 0–1 | Row-wise normalized \|FFT[φ(t)]\| (per drive frequency) |

## 3. Simulated system & conditions

Two TLS at **4.0 and 4.1 GHz**, **uncoupled** (see the warning above). Collective
decay `γ = 0.002`; pure dephasing `γφ = 0`; drive amplitude **0.1**. Drive is a
square pulse, `amp·cos(freq·t)` for `t ≤ pulse_ns` (no ramp). Phase-V FFT uses the
0–400 ns window and keeps positive frequencies up to 150 MHz, normalized to peak 1
per drive frequency.

**Unit convention:** frequencies used numerically as inverse nanoseconds
(GHz ≡ ns⁻¹), no 2π; amplitude dimensionless; phase in radians; time in ns; FFT
axis in MHz.

## 4. Constant parameters (in metadata, not columns)

`N_TLS`, the two TLS frequencies, the (dropped) coupling, γ, the drive amplitude,
the pulse-duration and drive-frequency grids, and the phase-V FFT window are
single-valued for the whole run and live in `metadata.json` rather than as
repeated columns. Pulse shape is a square `amp·cos(freq·t)` with no ramp.

## 5. Provenance & correctness

- **Physics module:** the local `hamiltonian_generator.py`, used unchanged except
  a QuTiP-5 API-compatibility shim (**no physics change**). The uncoupled quirk is
  reproduced exactly, not "fixed".
- **Verified:** all three tables were checked against an independent recomputation
  from the same physics functions — **matches to float32 precision** (population
  traces exact at diff = 0; the map and FFT differ only at the ~1e-8 float32 floor).
- Uses code and simulation methods from the **Fitzpatrick Lab, Dartmouth College**.

## 6. Released files

| File | Contents |
|---|---|
| `experiment_10/experiment_10_postpulse_map.pkl` / `.csv` | 20,000 × 3 |
| `experiment_10/experiment_10_population_traces.pkl` / `.csv` | 1,200,000 × 4 |
| `experiment_10/experiment_10_phaseV_fft.pkl` / `.csv` | ~73,200 × 4 |
| `experiment_10/experiment_10_run.log` | Per-run build + sanity-check log (git-ignored) |
| `metadata.json` | Shared metadata (system, grids, tables, the coupling note) — regenerated every run |
| `column_info.json` | Per-table column semantics — regenerated every run |

Each pickle is self-contained: `payload["data"]`, `payload["columns"]`,
`payload["table"]`, `payload["attrs"]` (shared metadata), `payload["column_doc"]`.

## 7. Loading

```python
import pickle, pandas as pd

with open("experiment_10/experiment_10_postpulse_map.pkl", "rb") as fh:
    payload = pickle.load(fh)
df = pd.DataFrame(payload["data"], columns=payload["columns"])
```

## 8. Rebuilding

Requires `qutip >= 5` (plus `numpy`, `pandas`, `tqdm`). **Heavy — 50 × 400 =
20,000 solves (~15–25 min):**

```
python experiment_10_dataset_creation.py --workers 16
```

Plumbing-only check without qutip (tiny synthetic grids; write elsewhere so the
real dataset is not overwritten):

```
python experiment_10_dataset_creation.py --smoke-test --output_dir /tmp/exp10_check
```

Simulated by the Fitzpatrick Lab, Dartmouth College.
