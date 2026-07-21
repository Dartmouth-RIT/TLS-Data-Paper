# Experiment 13 — Thermal Cycle (BCTDS Before and After)

Raw Broadband Cryogenic Transient Dielectric Spectroscopy (BCTDS) measurements
of **single-pulse broadband spectroscopy** on one sample, taken across **two
separate cooldowns** three days apart, with a warm-up to room temperature in
between and nothing else touched. Warming reshuffles the TLS defects, so the chip
rings at a noticeably different set of frequencies the second time — the two
cooldowns are what this dataset compares.

> **This dataset is raw measured data.** Every row holds the homodyne **I** and
> **Q** samples exactly as acquired — nothing is cropped, filtered, or
> post-processed. Magnitude, phase, and FFT spectra are computable from I and Q
> (see §5) and are not stored.

---

## 1. What this experiment does

A single square microwave pulse is fired, its **frequency** stepped across the
band in 1 MHz steps (3000 settings, 2000–4999 MHz — a much finer comb than
Experiment 11's 5 MHz steps), and the ring-down recorded by homodyne detection.
The full sweep is taken twice: once **before** and once **after** a thermal cycle
to room temperature, without breaking the fridge vacuum or changing the setup.
Comparing the two cooldowns shows how thermal cycling repopulates the defects.

## 2. The released dataset

**Format:** long — **one row per time sample**. Five columns:

| Column | Type | Unit | Description |
|---|---|---|---|
| `cooldown_index` | float32 | index | Which cooldown: 1 = before, 2 = after the thermal cycle |
| `frequency_MHz` | float32 | MHz | Drive frequency — **primary swept variable**, 3000 values 2000–4999 (step 1) |
| `timestamp_ns` | float32 | ns | Time of this sample from t = 0; spacing ≈ 1.8084 ns |
| `I` | float32 | ADC a.u. | **Raw** in-phase homodyne signal |
| `Q` | float32 | ADC a.u. | **Raw** quadrature homodyne signal |

- **Rows:** 2 cooldowns × 3000 frequencies × 1000 samples = **6,000,000**
- **One ring-down measurement** = 1000 consecutive rows sharing a
  `(cooldown_index, frequency_MHz)` combination.
- **Row ordering:** cooldown 1 first, then cooldown 2; within each, ordered by
  frequency, then time.

## 3. Sample & conditions

Single sample, `Shipley` — sapphire substrate with spin-coated Shipley 1813
photoresist. Both cooldowns sat at the same base temperature (~22 mK, approximate
— **not recorded in the raw files**). Bluefors LD400 refrigerator, WR-229
waveguide (3–6 GHz, TE₁₀), RFSoC readout.

## 4. Constant parameters (in metadata, not columns)

The sample and base temperature (~22 mK) were the same for both cooldowns, so
they live in `metadata.json` rather than as repeated columns.

> **No pulse-width column.** Unlike every other experiment in this series,
> neither the filename nor the generation code records the pulse duration, so
> this dataset has **no** `pulse_width_ns` column. The envelope measured from the
> data (~65 → ~105 ns) is wider than the 31.33 ns (308-tick) pulse used
> elsewhere, so that value is **not** assumed here.

**How time is computed.** Ring-down time axis:
`timestamp_ns = sample_index / 552.96 × 1000` (ADC clock, 1 sample ≈ 1.8084 ns),
0 → 1806.64 ns over 1000 samples.

## 5. Computable from the raw data (not shipped)

```python
mag   = np.abs(I + 1j*Q)
phase = np.angle(I + 1j*Q)
```

## 6. Raw files (before packing)

2 raw `.npy` files, one per cooldown:

| File | Cooldown |
|---|---|
| `shipley_IQ_avg_matrix.npy` | 1 — before thermal cycling |
| `shipley_2nd_IQ_avg_matrix.npy` | 2 — after thermal cycling |

Each of shape `(2, 3000, 1000)` = (I/Q, frequency, time). The frequency axis is
**not** stored in the files — it comes from the generation code
(`np.arange(2000, 5000, 1)`).

## 7. Released files

| File | Contents |
|---|---|
| `experiment_13/experiment_13_dataset_long.pkl` | `data` — array `(6_000_000, 5)` float32; `columns`; `attrs`; `column_doc` |
| `experiment_13/experiment_13_dataset_long.csv` | Same table as CSV |
| `metadata.json` | Constant configuration, cooldown descriptions (§3, §4) — regenerated every run |
| `column_info.json` | Per-column semantics and units (§2) — regenerated every run |

## 8. Loading

```python
import pickle, numpy as np, pandas as pd

with open("experiment_13/experiment_13_dataset_long.pkl", "rb") as fh:
    payload = pickle.load(fh)
df = pd.DataFrame(payload["data"], columns=payload["columns"])

# one ring-down trace (1000 rows):
mask  = (df["cooldown_index"] == 1) & (df["frequency_MHz"] == 3657)
trace = df[mask].sort_values("timestamp_ns")
```

## 9. Rebuilding

```
python experiment_13_dataset_creation.py --data_dir /path/to/matrix_npy_save_folder
```

Measured by the Fitzpatrick Lab, Dartmouth College.
