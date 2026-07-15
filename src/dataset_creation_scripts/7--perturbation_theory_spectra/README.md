# 📙 Experiment 7 — Analytical Phase-V Spectroscopy

## 📖 Overview

This experiment provides analytical solutions for a driven two-TLS system.

Unlike Experiment 6, the observables are computed analytically rather than through numerical time evolution.

---

## 🎯 Scientific Objective

Study the analytical relationship between drive frequency and the Phase-V response of coupled TLS defects.

---

## 📂 Files

| File | Description |
|------|-------------|
| figure7_phase_fft.pkl | Analytical FFT spectra |
| figure7_zero_frequency_phase.pkl | Zero-frequency phase response |
| figure7_metadata.json | Simulation metadata |
| *_column_info.json | Feature documentation |

---

## 📊 Dataset Summary

Contains

- analytical Phase-V FFT
- zero-frequency phase response
- drive frequency sweep

---

## 📑 Dataset Schema

### Common Metadata

| Column | Description |
|---------|-------------|
| sample_id | Experiment identifier |
| figure_id | Figure identifier |
| omega_1_GHz | First TLS frequency |
| omega_2_GHz | Second TLS frequency |
| j_coupling_GHz | Coupling strength |
| drive_frequency_GHz | Applied drive frequency |

---

### Phase FFT Dataset

| Column | Description |
|---------|-------------|
| fft_frequency_GHz | FFT frequency |
| fft_frequency_MHz | FFT frequency (MHz) |
| normalized_phase_fft | Analytical phase FFT |

---

### Zero-Frequency Phase Dataset

| Column | Description |
|---------|-------------|
| drive_frequency_GHz | Applied frequency |
| zero_frequency_phase | Zero-frequency phase response |

---

## 🔬 Applications

- Physics-informed learning
- Analytical surrogate models
- Regression
- Frequency response prediction
- Benchmark validation

---

## 📚 Citation

See the accompanying publication.