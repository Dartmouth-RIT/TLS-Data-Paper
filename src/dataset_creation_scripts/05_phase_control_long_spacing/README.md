# Experiment 5 — Phase Control at Long Inter-Pulse Spacing

Raw Broadband Cryogenic Transient Dielectric Spectroscopy (BCTDS) measurements
of a **two-pulse phase coherent-control** protocol on a single sample, with the
inter-pulse delay stretched from 10 ns to 600 ns. Because the ring-down dies
away in ~100 ns, the long delays reach past the point where anything is left to
interfere with — so the dataset measures how long the defects "remember" the
first pulse.

> **This dataset is raw measured data.** Every row holds the homodyne **I** and
> **Q** samples exactly as acquired — nothing is cropped, filtered, or
> post-processed. Magnitude, phase, and FFT spectra are computable from I and Q
> (see §5) and are not stored.

---

## 1. What this experiment does

Two square microwave pulses are fired a gap apart; the ring-down is recorded by
homodyne detection. The **phase of the first pulse** is swept 0 → 360° (121
steps of 3°) while the **inter-pulse spacing** is stepped across nine values from
10 to 600 ns, bracketing the ~100 ns ring-down lifetime. As the delay grows past
the lifetime, phase control fades — there is progressively less first-pulse
ring-down for the second pulse to interfere with.

## 2. The released dataset

**Format:** long — **one row per time sample**. Six columns:

| Column | Type | Unit | Description |
|---|---|---|---|
| `spacing_ns` | float32 | ns | Inter-pulse gap in **nanoseconds** — 10, 30, 50, 100, 200, 300, 400, 500, 600 |
| `phase_deg` | float32 | deg | Phase of the **first** pulse — **primary swept variable**, 121 values 0–360 (step 3) |
| `timestamp_ns` | float32 | ns | Time within the trace (fast axis); spacing ≈ 1.8084 ns |
| `elapsed_s` | float32 | s | Wall-clock seconds since the run started (slow acquisition axis) |
| `I` | float32 | ADC a.u. | **Raw** in-phase homodyne signal |
| `Q` | float32 | ADC a.u. | **Raw** quadrature homodyne signal |

- **Rows:** 9 spacings × 121 phases × 1000 samples = **1,089,000**
- **One ring-down measurement** = 1000 consecutive rows sharing a
  `(spacing_ns, phase_deg)` combination.
- **Row ordering:** ascending spacing, then phase, then time.
- `elapsed_s` is seconds since the run start (not a Unix epoch), constant across
  the 1000 samples of a single trace; it gives acquisition order and lets drift
  over the run be checked. Distinct from `timestamp_ns` (the fast within-trace
  axis). `phase = 0°` and `360°` are the same physical point, acquired
  independently.

## 3. Sample & conditions

Single sample, `Shipley` — sapphire substrate with spin-coated Shipley 1813
photoresist. Driven at a single frequency, **3400 MHz**, at an **8 mK** set
point. Bluefors LD400 refrigerator, WR-229 waveguide (3–6 GHz, TE₁₀), RFSoC
readout.

## 4. Constant parameters (in metadata, not columns)

This experiment used one chip, one drive frequency (3400 MHz), one temperature
(8 mK) and one pulse width — each single-valued, so all live in `metadata.json`
rather than as repeated columns. Also in metadata: `num_pulses = 2`,
`pulse_shape = square`, and the **pulse geometry** (second pulse anchored, first
slides earlier as the delay grows). Drive amplitudes are **not** recorded in the
raw files and are left unasserted (`None`) — do not assume Experiment 4's values.

**How time is computed (ticks → ns).** Pulse duration: `ns = ticks / 9830.4 ×
1000` (AWG clock; fixed 308 ticks → 31.33 ns). Ring-down time axis:
`timestamp_ns = sample_index / 552.96 × 1000` (ADC clock), 0 → 1806.64 ns.

## 5. Computable from the raw data (not shipped)

```python
mag   = np.abs(I + 1j*Q)
phase = np.angle(I + 1j*Q)
```

## 6. Raw files (before packing)

9 raw `.npz` files (one per spacing), named
`308_freq_3400_spacing_{spacing_us}_ID_Shipley_phase_8mK_20251012_132853.npz`
(spacing in **microseconds** in the filename). Each contains
`IQ_avg_matrix (2, 121, 1000)`, `pulse_phase_array (121,)` (the phase axis, read
and validated rather than assumed), and `time_stamp_list (121,)` (wall clock per
phase point, used for `elapsed_s`).

> **Overlap with Experiment 12.** These 9 files are byte-identical to the
> 8 mK / 3400 MHz slice of Experiment 12's temperature campaign (shared run ID
> `Shipley_phase_8mK_20251012_132853`). The two are released separately so each
> dataset stands alone.

## 7. Released files

| File | Contents |
|---|---|
| `experiment_5/experiment_5_dataset_long.pkl` | `data` — array `(1_089_000, 6)` float32; `columns`; `attrs`; `column_doc` |
| `experiment_5/experiment_5_dataset_long.csv` | Same table as CSV |
| `metadata.json` | Constant configuration, pulse geometry, acquisition (§3, §4) — regenerated every run |
| `column_info.json` | Per-column semantics and units (§2) — regenerated every run |

## 8. Loading

```python
import pickle, numpy as np, pandas as pd

with open("experiment_5/experiment_5_dataset_long.pkl", "rb") as fh:
    payload = pickle.load(fh)
df = pd.DataFrame(payload["data"], columns=payload["columns"])

# one ring-down trace (1000 rows):
mask  = (df["spacing_ns"] == 600) & (df["phase_deg"] == 0)
trace = df[mask].sort_values("timestamp_ns")
```

## 9. Rebuilding

```
python experiment_5_dataset_creation.py --data_dir /path/to/npz_data_base
```

Measured by the Fitzpatrick Lab, Dartmouth College.
