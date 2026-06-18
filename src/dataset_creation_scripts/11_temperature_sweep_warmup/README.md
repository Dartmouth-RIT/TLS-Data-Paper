# Experiment 11 — Temperature Dependence of BCTDS During Warm-Up

Raw Broadband Cryogenic Transient Dielectric Spectroscopy (BCTDS) measurements
of **single-pulse broadband spectroscopy**, swept across 3–5 GHz and repeated
back-to-back while the dilution refrigerator is deliberately allowed to warm up
from base temperature to ~250 K. The sweep index doubles as a temperature axis,
so the dataset captures how sharp, structured ring-downs wash out as the sample
heats.

> **This dataset is raw measured data.** Every row holds the homodyne **I** and
> **Q** samples exactly as acquired — nothing is cropped, filtered, or fitted.
> Magnitude, phase, FFT spectra and fitted lifetimes are computable from I and Q
> (see §5) and are not stored.

---

## 1. What this experiment does

A single square microwave pulse is fired, its **frequency** stepped across the
3–5 GHz band (401 settings, 5 MHz apart), and the ring-down recorded by homodyne
detection. That full sweep is then repeated **106 times** back-to-back while the
fridge warms from ~0.14 K to ~250 K over ~17 hours (each sweep ≈ 9 minutes).
Because the fridge is warming throughout, the sweep number (`rep_index`) is
monotonic in **both** wall-clock time and temperature — so temperature here is
**measured** and stored per reading, not a fixed setting.

## 2. The released dataset

**Format:** long — **one row per time sample**. Eight columns:

| Column | Type | Unit | Description |
|---|---|---|---|
| `rep_index` | float32 | index | Which back-to-back sweep (0–105) — **primary variable**; monotonic in time and temperature |
| `frequency_MHz` | float32 | MHz | Drive frequency — swept axis, 3000–5000 (step 5) |
| `T_mxc_K` | float32 | K | Mixing-chamber plate temperature, **in kelvin** — **may be NaN** (see §6) |
| `T_still_K` | float32 | K | Still-stage temperature, in kelvin |
| `timestamp_ns` | float32 | ns | Time within the trace (fast axis); spacing ≈ 1.8084 ns |
| `elapsed_s` | float32 | s | Wall-clock seconds since the warm-up started (slow axis) |
| `I` | float32 | ADC a.u. | **Raw** in-phase homodyne signal (never NaN) |
| `Q` | float32 | ADC a.u. | **Raw** quadrature homodyne signal (never NaN) |

- **Rows:** 106 reps × 401 frequencies × 1000 samples = **42,506,000** (the
  largest dataset in the series — ~1.6 GB pickle, ~3 GB CSV; needs ~3.5 GB RAM
  to build).
- **One ring-down measurement** = 1000 consecutive rows sharing a
  `(rep_index, frequency_MHz)` combination.
- **Row ordering:** ascending `rep_index` (chronological), then frequency, then
  time.
- `T_mxc_K` / `T_still_K` are in **kelvin, not millikelvin** — averaging
  `T_mxc_K` over a rep gives that sweep's temperature (rep 0 → 0.1416 K,
  rep 45 → 88.2431 K). The actual sample is expected to be *colder* than this
  plate reading.

## 3. Sample & conditions

Single sample, `FM_Shipley` — sapphire substrate with spin-coated Shipley 1813
photoresist. Bluefors LD400 refrigerator, WR-229 waveguide (3–6 GHz, TE₁₀),
RFSoC readout. Drive amplitude is HFSS-calibrated flat across the band; its
absolute value is not recorded in the raw files.

## 4. Constant parameters (in metadata, not columns)

Single-valued quantities live in `metadata.json`: the sample, `num_pulses = 1`,
`pulse_shape = square`, and the pulse width (fixed 308 AWG ticks → 31.33 ns).

**How time is computed (ticks → ns).** Pulse duration:
`ns = ticks / 9830.4 × 1000` (AWG clock). Ring-down time axis:
`timestamp_ns = sample_index / 552.96 × 1000` (ADC clock), 0 → 1806.64 ns over
1000 samples. `elapsed_s` is seconds since the first timestamp of rep 0 (stored
as elapsed seconds, not a Unix epoch, because float32 cannot hold an epoch to
better than ~128 s).

## 5. Computable from the raw data (not shipped)

```python
mag   = np.abs(I + 1j*Q)
phase = np.angle(I + 1j*Q)
log_amp = np.log10(np.abs(I + 1j*Q) + 0.01)
# tau (fitted ring-down lifetime) is a curve_fit output, not a measurement —
# deliberately not stored; it lives in the processed_result_npz companion folder.
```

## 6. NaN is expected in `T_mxc_K`

`T_mxc_K` contains **9,221,000 NaN rows (21.7%)**: the mixing-chamber thermometer
stops reading as the fridge warms, and the first all-NaN sweep is **rep 84**
(all NaN fall in reps 83–105; reps 0–82 are clean). **NaN means "not measured",
not "bad data".** `I` and `Q` are **never** NaN — the build script checks that
invariant rather than rejecting NaN outright. Filter with `np.isnan()` as needed.

## 7. Raw files (before packing)

106 raw `.npz` files, named
`308_rep_{N}_ID_FM_Shipley_cont_HFSS_calib_20251008_174837_with_T.npz`, each
containing `IQ_avg_matrix (2, 401, 1000)`, `pulse_freq_array (401,)`,
`time_stamp_list (401,)`, `T_still (401,)`, `T_mxc (401,)`. The source folder
also has a `processed_result_npz/` directory of **derived** results (fits, FFTs);
that is *not* packaged here — this dataset ships the raw sweeps only.

## 8. Released files

| File | Contents |
|---|---|
| `experiment_11/experiment_11_dataset_long.pkl` | `data` — array `(42_506_000, 8)` float32; `columns`; `attrs`; `column_doc` |
| `experiment_11/experiment_11_dataset_long.csv` | Same table as CSV |
| `metadata.json` | Constant configuration, thermometry notes, processed-companion note — regenerated every run |
| `column_info.json` | Per-column semantics and units — regenerated every run |

## 9. Loading

```python
import pickle, numpy as np, pandas as pd

with open("experiment_11/experiment_11_dataset_long.pkl", "rb") as fh:
    payload = pickle.load(fh)
df = pd.DataFrame(payload["data"], columns=payload["columns"])

# one ring-down trace (1000 rows):
mask  = (df["rep_index"] == 0) & (df["frequency_MHz"] == 3400)
trace = df[mask].sort_values("timestamp_ns")

# mean mixing-chamber temperature per sweep:
df.groupby("rep_index")["T_mxc_K"].mean()
```

## 10. Rebuilding

```
python experiment_11_dataset_creation.py --data_dir /path/to/npz_data_base_with_T
```

Measured by the Fitzpatrick Lab, Dartmouth College.
