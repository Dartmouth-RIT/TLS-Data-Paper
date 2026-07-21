# Experiment 4 — Phase Control (Two-Pulse Coherent Control)


Raw Broadband Cryogenic Transient Dielectric Spectroscopy (BCTDS) measurements
of a **two-pulse coherent-control** protocol on two-level-system (TLS) defect
ensembles, taken on **three different samples**. The **phase** of the first
pulse is swept through a full turn while the inter-pulse spacing is varied,
probing phase-controlled memory effects between the two pulses. Companion to
Experiment 3, which sweeps the first pulse's *amplitude* instead of its *phase*.

> **This dataset is raw measured data.** Every row holds the homodyne **I** and
> **Q** samples exactly as acquired — nothing is simulated, cropped, filtered,
> or post-processed. Magnitude, phase, and FFT spectra are *not* stored; they
> are trivially computable from I and Q (see §5).

---

## 1. What this experiment does

Two square microwave pulses are fired a short gap apart; the transient ring-down
that follows is recorded by homodyne detection. The **phase of the first pulse**
is swept 0 → 360° (121 steps of 3°) while the second pulse's phase is held fixed,
and the **inter-pulse spacing** is varied (0 → 50 ns). Changing the first pulse's
phase changes whether its ring-down adds to or cancels the second pulse's
response — i.e. phase-controlled coherent memory in the TLS bath. At
`spacing = 0` the two pulses are contiguous, forming one double-length pulse with
a phase discontinuity in the middle. The protocol is repeated on three samples,
each driven at a frequency chosen to hit a strong ring-down resonance.

## 2. The released dataset

**Format:** long — **one row per time sample**. Seven columns:

| Column | Type | Unit | Description |
|---|---|---|---|
| `sample_id` | float32 | index | Which sample: 0 = AlOx, 1 = 111_oxide, 2 = silicon (see `sample_names` in the pickle) |
| `frequency_MHz` | float32 | MHz | Drive frequency, fixed per sample (3657 / 4254 / 4424) |
| `spacing_ns` | float32 | ns | Inter-pulse gap in **nanoseconds** (0, 10, 20, 30, 40, 50) |
| `phase_deg` | float32 | deg | Phase of the **first** pulse — **primary swept variable**, 121 values 0–360 (step 3) |
| `timestamp_ns` | float32 | ns | Time of this sample from t = 0; spacing ≈ 1.8084 ns |
| `I` | float32 | ADC a.u. | **Raw** in-phase homodyne signal |
| `Q` | float32 | ADC a.u. | **Raw** quadrature homodyne signal |

- **Rows:** 3 samples × 6 spacings × 121 phases × 1000 samples = **2,178,000**
- **One ring-down measurement** = 1000 consecutive rows sharing a
  `(sample_id, spacing_ns, phase_deg)` combination.
- **Row ordering:** all AlOx rows first, then 111_oxide, then silicon; within a
  sample, ordered by spacing, then phase, then time.
- `spacing_ns` is stored in **integer nanoseconds**, so `== 10` is exact in
  float32. `phase = 0°` and `phase = 360°` are the same physical point, acquired
  independently — their difference gives a free per-file noise-floor estimate.
- `I`, `Q` are the *measured* signal, distinct from the drive amplitude.

## 3. Samples

| id | name | material | drive freq. |
|---|---|---|---|
| 0 | AlOx | Sapphire substrate + 2 nm ALD AlOx layer | 3657 MHz |
| 1 | 111_oxide | Silicon (111), native SiOₓ surface layer | 4254 MHz |
| 2 | silicon | Silicon with silicon oxide | 4424 MHz |

Drive frequency is **fixed per sample**; both pulses fire at that frequency. All
measured at < 10 mK (Bluefors LD400) in a WR-229 waveguide (3–6 GHz, TE₁₀), read
out on an RFSoC.

## 4. Constant parameters (in metadata, not columns)

Single-valued quantities live in `metadata.json`: the **pulse width** (fixed 308
AWG ticks → 31.33 ns), `num_pulses = 2`, `pulse_shape = square`, and the drive
amplitudes (first pulse 3× stronger than the second; absolute values are not
recorded in the raw files). `metadata.json` also records the **pulse geometry**
measured from the envelope: the second pulse is anchored in time and the first
slides earlier as the spacing grows, so `timestamp_ns` is directly comparable
across spacings.

**How time is computed (ticks → ns).** Pulse duration:
`ns = ticks / 9830.4 × 1000` (AWG clock). Ring-down time axis:
`timestamp_ns = sample_index / 552.96 × 1000` (ADC clock), 0 → 1806.64 ns.

## 5. Computable from the raw data (not shipped)

```python
mag   = np.abs(I + 1j*Q)
phase = np.angle(I + 1j*Q)
```

## 6. Raw files (before packing)

18 raw `.npy` files (3 samples × 6 spacings), named
`{sample}_308_freq_{frequency_MHz}_spacing_{spacing_us}_IQ_avg_matrix.npy`
(spacing in **microseconds** in the filename, e.g.
`AlOx_308_freq_3657_spacing_0.01_IQ_avg_matrix.npy`), each of shape
`(2, 121, 1000)` = (I/Q, phase, time).

The three `*_HFSS_calibrated_3-5_GHz_*` files in the same folder are a separate
frequency sweep and are **not** part of this dataset.

## 7. Released files

| File | Contents |
|---|---|
| `experiment_4/experiment_4_dataset_long.pkl` | `data` — array `(2_178_000, 7)` float32; `columns`; `sample_names`; `attrs`; `column_doc` |
| `experiment_4/experiment_4_dataset_long.csv` | Same table as CSV |
| `metadata.json` | Constant configuration, pulse geometry (§3, §4) — regenerated every run |
| `column_info.json` | Per-column semantics and units (§2) — regenerated every run |

## 8. Loading

```python
import pickle, numpy as np, pandas as pd

with open("experiment_4/experiment_4_dataset_long.pkl", "rb") as fh:
    payload = pickle.load(fh)
df = pd.DataFrame(payload["data"], columns=payload["columns"])
sample_names = payload["sample_names"]     # ['AlOx', '111_oxide', 'silicon']

# one ring-down trace (1000 rows):
mask  = (df["sample_id"] == 0) & (df["spacing_ns"] == 10) & (df["phase_deg"] == 0)
trace = df[mask].sort_values("timestamp_ns")
```

## 9. Rebuilding

```
python experiment_4_dataset_creation.py --data_dir /path/to/matrix_npy_save_folder
```

Measured by the Fitzpatrick Lab, Dartmouth College.
