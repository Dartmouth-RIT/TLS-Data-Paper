# Experiment 12 — Coherent Phase Control at Different Temperatures

Raw Broadband Cryogenic Transient Dielectric Spectroscopy (BCTDS) measurements
of a **two-pulse phase coherent-control** protocol on a single sample, repeated
at **seven fridge temperatures** from 8 mK to 750 mK. Quantum interference is
fragile — heat blurs it — so the phase contrast collapses as temperature rises.

> **This dataset is raw measured data.** Every row holds the homodyne **I** and
> **Q** samples exactly as acquired — nothing is cropped, filtered, or
> post-processed. Magnitude, phase, and FFT spectra are computable from I and Q
> (see §5) and are not stored.

---

## 1. What this experiment does

Two square microwave pulses are fired a gap apart; the ring-down is recorded by
homodyne detection. The **phase of the first pulse** is swept 0 → 360° (121 steps
of 3°), across nine inter-pulse spacings (10–600 ns) and two drive frequencies
(3400 and 3560 MHz). The whole set is then repeated at **seven temperature set
points** (8, 95, 200, 307, 400, 600, 750 mK). Each temperature is a separate
acquisition run, thermalised for > 1 hour beforehand; the full campaign spans
about three days.

## 2. The released dataset

**Format:** long — **one row per time sample**. Eight columns:

| Column | Type | Unit | Description |
|---|---|---|---|
| `temperature_mK` | float32 | mK | Fridge **set point** — **primary variable** (8, 95, 200, 307, 400, 600, 750) |
| `frequency_MHz` | float32 | MHz | Drive frequency (3400 or 3560) |
| `spacing_ns` | float32 | ns | Inter-pulse gap in nanoseconds (10, 30, 50, 100, 200, 300, 400, 500, 600) |
| `phase_deg` | float32 | deg | Phase of the **first** pulse, 121 values 0–360 (step 3) |
| `timestamp_ns` | float32 | ns | Time within the trace (fast axis); spacing ≈ 1.8084 ns |
| `elapsed_s` | float32 | s | Wall-clock seconds since the campaign started (slow axis) |
| `I` | float32 | ADC a.u. | **Raw** in-phase homodyne signal |
| `Q` | float32 | ADC a.u. | **Raw** quadrature homodyne signal |

- **Rows:** 7 temps × 2 freqs × 9 spacings × 121 phases × 1000 samples =
  **15,246,000**
- **One ring-down measurement** = 1000 consecutive rows sharing a
  `(temperature_mK, frequency_MHz, spacing_ns, phase_deg)` combination.
- **Row ordering:** ascending temperature (chronological), then frequency, then
  spacing, then phase, then time.
- `temperature_mK` is a **set point**, not a measured value — these files carry
  no thermometry arrays (Experiment 11's do). `elapsed_s` (seconds since the 8 mK
  run started; campaign spans ~3 days) also encodes which run a row belongs to.

## 3. Sample & conditions

Single sample, `Shipley` — sapphire substrate with spin-coated Shipley 1813
photoresist. Temperature is set with the mixing-chamber heater and allowed to
thermalise > 1 hour before each run. Bluefors LD400 refrigerator, WR-229
waveguide (3–6 GHz, TE₁₀), RFSoC readout.

## 4. Constant parameters (in metadata, not columns)

Single-valued quantities live in `metadata.json`: the sample, the pulse width
(fixed 308 AWG ticks → 31.33 ns), `num_pulses = 2`, `pulse_shape = square`, and
the **pulse geometry** (second pulse anchored, first slides with spacing). Drive
amplitudes are **not** recorded in the raw files and are left unasserted
(`None`).

**How time is computed (ticks → ns).** Pulse duration: `ns = ticks / 9830.4 ×
1000` (AWG clock). Ring-down time axis:
`timestamp_ns = sample_index / 552.96 × 1000` (ADC clock), 0 → 1806.64 ns.

## 5. Computable from the raw data (not shipped)

```python
mag   = np.abs(I + 1j*Q)
phase = np.angle(I + 1j*Q)
```

## 6. Raw files (before packing)

126 raw `.npz` files in per-temperature subfolders:
`npz_data_base/npz_data_base_{T}mK/308_freq_{MHz}_spacing_{spacing_us}_ID_{run_id}.npz`
(spacing in **microseconds** in the filename; each temperature has its own run
ID). Each contains `IQ_avg_matrix (2, 121, 1000)`, `pulse_phase_array (121,)`
(read and validated), and `time_stamp_list (121,)` (wall clock per phase point).

> **Overlap with Experiment 5.** The 9 files at 8 mK / 3400 MHz are
> byte-identical to the whole of Experiment 5 (shared run ID
> `Shipley_phase_8mK_20251012_132853`). The two are released separately so each
> dataset stands alone.

## 7. Released files

| File | Contents |
|---|---|
| `experiment_12/experiment_12_dataset_long.pkl` | `data` — array `(15_246_000, 8)` float32; `columns`; `attrs`; `column_doc` |
| `experiment_12/experiment_12_dataset_long.csv` | Same table as CSV |
| `metadata.json` | Constant configuration, per-run IDs, pulse geometry — regenerated every run |
| `column_info.json` | Per-column semantics and units (§2) — regenerated every run |

## 8. Loading

```python
import pickle, numpy as np, pandas as pd

with open("experiment_12/experiment_12_dataset_long.pkl", "rb") as fh:
    payload = pickle.load(fh)
df = pd.DataFrame(payload["data"], columns=payload["columns"])

# one ring-down trace (1000 rows):
mask  = ((df["temperature_mK"] == 8) & (df["frequency_MHz"] == 3400)
         & (df["spacing_ns"] == 100) & (df["phase_deg"] == 0))
trace = df[mask].sort_values("timestamp_ns")
```

## 9. Rebuilding

```
python experiment_12_dataset_creation.py --data_dir /path/to/npz_data_base
```

Measured by the Fitzpatrick Lab, Dartmouth College.
