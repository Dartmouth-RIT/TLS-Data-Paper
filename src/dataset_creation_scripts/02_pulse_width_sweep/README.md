# Experiment 2 — Pulse-Width Sweep

Raw Broadband Cryogenic Transient Dielectric Spectroscopy (BCTDS) measurements
of two-level-system (TLS) defect ensembles in a silicon native-oxide sample,
recorded while sweeping the **duration of a single square microwave drive pulse**
across 500 drive frequencies.

> **This dataset is raw measured data.** Every row holds the homodyne **I** and
> **Q** samples exactly as acquired — nothing is simulated, cropped, filtered,
> or post-processed. Magnitude, phase, and FFT spectra are *not* stored; they
> are trivially computable from I and Q (see §5).

---

## 1. What this experiment does

A single square microwave pulse drives the sample; the moment it switches off,
the excited TLS defects keep radiating and decaying — the **ring-down**. Two
knobs are turned. First, the **pulse duration**: 42 settings from ~5 ns to ~214
ns (a brief tap versus a long push excite the defects differently). Second, the
**drive frequency**: stepped across 4100–4599 MHz in 1 MHz steps (500 settings),
asking the chip which notes it rings at. Every combination is measured, giving a
42 × 500 grid, each cell holding one complete ring-down recording.

## 2. The released dataset

**Format:** long — **one row per time sample**. Five columns:

| Column | Type | Unit | Description |
|---|---|---|---|
| `pulse_width_ns` | float32 | ns | Duration of the square drive pulse — **swept variable**, 42 values ~5.09–213.62 ns (= AWG ticks / 9830.4 × 1000) |
| `frequency_MHz` | float32 | MHz | Drive frequency — 500 channels, 4100–4599 MHz (1 MHz steps) |
| `timestamp_ns` | float32 | ns | Time of this sample from t = 0; spacing ≈ 1.8084 ns (= sample index / 552.96 × 1000) |
| `I` | float32 | ADC a.u. | **Raw** in-phase homodyne signal |
| `Q` | float32 | ADC a.u. | **Raw** quadrature homodyne signal |

- **Rows:** 42 pulse widths × 500 frequencies × 1000 samples = **21,000,000**
  (the largest dataset in the series by row count).
- **One ring-down measurement** = 1000 consecutive rows sharing a
  `(pulse_width_ns, frequency_MHz)` pair.
- **Row ordering:** ascending pulse width, then frequency, then time.
- There is **no `sample_id` column** — a single chip was used (recorded in
  `metadata.json`).
- `I`, `Q` are the *measured* signal (roughly −2,700 to +2,400 a.u. here),
  distinct from the drive amplitude.

> ⚠️ **Filtering caveat.** `pulse_width_ns` is a converted value
> (`ticks / 9830.4 × 1000`) that lands on numbers a computer cannot store
> exactly, so `df.pulse_width_ns == 30.5176` may silently match **nothing**. Use
> `np.isclose()` instead. `frequency_MHz` is whole numbers, so `==` is safe
> there. The 42 exact widths are listed in `metadata.json` under
> `sweep.pulse_width.values_ns`.

## 3. Sample & conditions

Single sample, `Si_111_native_oxide` — Silicon (111) with a native SiOₓ surface
layer (WaferPro). Measured at < 10 mK (Bluefors LD400) in a WR-229 waveguide
(3–6 GHz, TE₁₀), read out on an RFSoC.

## 4. Constant parameters (in metadata, not columns)

Single-valued quantities live in `metadata.json`: the sample, `num_pulses = 1`,
`pulse_shape = square`, and the drive amplitude (fixed, but **recorded nowhere in
the raw files** — neither the filenames nor the arrays).

**How time is computed (ticks → ns).** The instrument counts integer clock
cycles on two independent clocks. Pulse duration: `ns = ticks / 9830.4 × 1000`
(AWG clock, 1 tick ≈ 0.1017 ns), 42 values from 50 to 2100 ticks. Ring-down time
axis: `timestamp_ns = sample_index / 552.96 × 1000` (ADC clock, 1 sample ≈
1.8084 ns), 0 → 1806.64 ns over 1000 samples.

## 5. Computable from the raw data (not shipped)

```python
mag   = np.abs(I + 1j*Q)      # = np.sqrt(I**2 + Q**2)
phase = np.angle(I + 1j*Q)    # = np.arctan2(Q, I)
# phase-V spectra: FFT the ring-down phase over the post-pulse window
```

## 6. Raw files (before packing)

42 raw `.npy` files (one per pulse width), named `{ticks}_IQ_avg_matrix_0.npy`
(e.g. `300_IQ_avg_matrix_0.npy`), each of shape `(2, 500, 1000)` = (I/Q,
frequency, time). Other files in the same folder (`full_record_*`, `slice_*`,
`peak_plot_data.npz`, `phase_fft_slice_and_avg.npz`) are **derived** results and
are **not** part of this dataset.

## 7. Released files

| File | Contents |
|---|---|
| `experiment_2/experiment_2_dataset_long.pkl` | `data` — array `(21_000_000, 5)` float32; `columns`; `attrs`; `column_doc` |
| `experiment_2/experiment_2_dataset_long.csv` | Same table as CSV (~1 GB; skip with `--no_csv`) |
| `metadata.json` | Constant configuration, swept-value lists (§3, §4) — regenerated every run |
| `column_info.json` | Per-column semantics and units (§2) — regenerated every run |

## 8. Loading

```python
import pickle, numpy as np, pandas as pd

with open("experiment_2/experiment_2_dataset_long.pkl", "rb") as fh:
    payload = pickle.load(fh)
df = pd.DataFrame(payload["data"], columns=payload["columns"])

# one ring-down trace (1000 rows) — note np.isclose for pulse_width_ns:
mask  = np.isclose(df["pulse_width_ns"], 30.5176) & (df["frequency_MHz"] == 4254)
trace = df[mask].sort_values("timestamp_ns")
```

## 9. Rebuilding

```
python experiment_2_dataset_creation.py --data_dir /path/to/matrix_npy
```

Measured by the Fitzpatrick Lab, Dartmouth College.
