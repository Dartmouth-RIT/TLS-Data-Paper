# Experiment 3 — Amplitude Control (Two-Pulse Coherent Control)


Raw Broadband Cryogenic Transient Dielectric Spectroscopy (BCTDS) measurements
of a **two-pulse coherent-control** protocol on two-level-system (TLS) defect
ensembles, taken on **three different samples**. The amplitude of the first
pulse is swept while the inter-pulse spacing is varied, probing
amplitude-controlled memory effects between the two pulses.

> **This dataset is raw measured data.** Every row holds the homodyne **I** and
> **Q** samples exactly as acquired — nothing is simulated, cropped, filtered,
> or post-processed. Magnitude, phase, and FFT spectra are *not* stored; they
> are trivially computable from I and Q (see §5).

---

## 1. What this experiment does

Two square microwave pulses are fired a short gap apart; the transient ring-down
that follows is recorded by homodyne detection. The **first pulse's amplitude**
is swept (100 steps, 0 → 29,700 a.u.) while the second pulse is held at a fixed
reference (~10,000 a.u.), and the **inter-pulse spacing** is varied (0 → 50 ns).
A harder first pulse leaves the defects ringing more strongly, changing what the
second pulse interferes with — i.e. amplitude-controlled coherent memory in the
TLS bath. At `spacing = 0` the two pulses are contiguous, forming one
double-length pulse. The protocol is repeated on three samples, each driven at a
frequency chosen to hit a strong ring-down resonance for that sample.

## 2. The released dataset

**Format:** long — **one row per time sample**. Seven columns:

| Column | Type | Unit | Description |
|---|---|---|---|
| `sample_id` | float32 | index | Which sample: 0 = AlOx, 1 = 111_oxide, 2 = silicon (see `sample_names` in the pickle) |
| `frequency_MHz` | float32 | MHz | Drive frequency, fixed per sample (3657 / 4254 / 4424) |
| `spacing_ns` | float32 | ns | Inter-pulse gap in **nanoseconds** (0, 10, 20, 30, 40, 50) |
| `amplitude_arb` | float32 | arb | Amplitude of the **first** pulse — **primary swept variable**, 100 values 0–29700 (step 300) |
| `timestamp_ns` | float32 | ns | Time of this sample from t = 0; spacing ≈ 1.8084 ns |
| `I` | float32 | ADC a.u. | **Raw** in-phase homodyne signal |
| `Q` | float32 | ADC a.u. | **Raw** quadrature homodyne signal |

- **Rows:** 3 samples × 6 spacings × 100 amplitudes × 1000 samples = **1,800,000**
- **One ring-down measurement** = 1000 consecutive rows sharing a
  `(sample_id, spacing_ns, amplitude_arb)` combination.
- **Row ordering:** all AlOx rows first, then 111_oxide, then silicon; within a
  sample, ordered by spacing, then amplitude, then time.
- `spacing_ns` is stored in **integer nanoseconds**, not the filenames'
  microseconds, so equality filtering (`== 10`) is exact in float32.
- `I`, `Q` are the *measured* signal (roughly −3,700 to +3,500 a.u. here),
  distinct from the swept *drive* amplitude in `amplitude_arb`.

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

Anything single-valued across the whole experiment lives in `metadata.json`
rather than as a repeated column: the **pulse width** (fixed 308 AWG ticks →
31.33 ns), `num_pulses = 2`, `pulse_shape = square`, and the fixed second-pulse
amplitude (~10,000 a.u.).

**How time is computed (ticks → ns).** The instrument counts integer clock
cycles on two independent clocks. Pulse duration: `ns = ticks / 9830.4 × 1000`
(AWG clock, 1 tick ≈ 0.1017 ns). Ring-down time axis:
`timestamp_ns = sample_index / 552.96 × 1000` (ADC clock, 1 sample ≈ 1.8084 ns),
giving 0 → 1806.64 ns over 1000 samples.

## 5. Computable from the raw data (not shipped)

```python
mag   = np.abs(I + 1j*Q)      # = np.sqrt(I**2 + Q**2)
phase = np.angle(I + 1j*Q)    # = np.arctan2(Q, I)
```

## 6. Raw files (before packing)

18 raw `.npy` files (3 samples × 6 spacings), named
`{sample}_308_freq_{frequency_MHz}_spacing_{spacing_us}_IQ_avg_matrix.npy`
(e.g. `AlOx_308_freq_3657_spacing_0.01_IQ_avg_matrix.npy`), each of shape
`(2, 100, 1000)` = (I/Q, amplitude, time). The three
`*_HFSS_calibrated_3-5_GHz_*` files in the same folder are a separate frequency
sweep and are **not** part of this dataset.

## 7. Released files

| File | Contents |
|---|---|
| `experiment_3/experiment_3_dataset_long.pkl` | `data` — array `(1_800_000, 7)` float32; `columns`; `sample_names`; `attrs`; `column_doc` |
| `experiment_3/experiment_3_dataset_long.csv` | Same table as CSV |
| `metadata.json` | Constant experiment configuration (§3, §4) — regenerated every run |
| `column_info.json` | Per-column semantics and units (§2) — regenerated every run |

## 8. Loading

```python
import pickle, numpy as np, pandas as pd

with open("experiment_3/experiment_3_dataset_long.pkl", "rb") as fh:
    payload = pickle.load(fh)
df = pd.DataFrame(payload["data"], columns=payload["columns"])
sample_names = payload["sample_names"]     # ['AlOx', '111_oxide', 'silicon']

# one ring-down trace (1000 rows):
mask  = (df["sample_id"] == 0) & (df["spacing_ns"] == 10) & (df["amplitude_arb"] == 1500)
trace = df[mask].sort_values("timestamp_ns")
```

## 9. Rebuilding

```
python experiment_3_dataset_creation.py --data_dir /path/to/matrix_npy_save_folder
```

Measured by the Fitzpatrick Lab, Dartmouth College.
