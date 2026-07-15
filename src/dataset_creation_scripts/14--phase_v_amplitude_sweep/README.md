# 📗 Experiment 14 — Pulse-Amplitude Sweep Spectroscopy

## 📖 Overview

This dataset reproduces the pulse-amplitude sweep experiment shown in Figure 14.

The drive pulse amplitude is systematically varied while transient homodyne measurements are recorded.

---

## 🎯 Scientific Objective

Characterize how microwave drive amplitude influences transient spectroscopy measurements.

---

## 📂 Files

| File | Description |
|------|-------------|
| figure14_time_domain.pkl | Time-domain I/Q measurements |
| figure14_phase_fft.pkl | FFT spectra |
| figure14_metadata.json | Simulation metadata |
| *_column_info.json | Feature documentation |

---

## 📊 Dataset Summary

Recorded quantities include

- In-phase signal (I)
- Quadrature signal (Q)
- Phase
- FFT spectrum

---

## 📈 Swept Parameters

- Pulse amplitude
- Drive frequency
- Time

---

## 📑 Dataset Schema

### Experimental Parameters

| Column | Description |
|---------|-------------|
| sample_id | Experiment identifier |
| figure_id | Figure identifier |
| pulse_amplitude_GHz | Applied microwave amplitude |
| pulse_duration_ns | Pulse duration |
| drive_frequency_GHz | Applied drive frequency |
| timestamp_ns | Time after pulse |

---

### Time-Domain Dataset

| Column | Description |
|---------|-------------|
| I | In-phase homodyne signal |
| Q | Quadrature homodyne signal |
| phase_rad | Instantaneous phase |

---

### FFT Dataset

| Column | Description |
|---------|-------------|
| fft_frequency_MHz | FFT frequency |
| log10_phase_fft | Log-scaled phase FFT |

---

## 🤖 Applications

- Sequence modeling
- Signal denoising
- FFT prediction
- Spectroscopy regression
- Inverse pulse reconstruction

---

## 📚 Citation

See the accompanying publication.