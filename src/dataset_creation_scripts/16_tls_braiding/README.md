# 📓 Experiment 16 — Degenerate and Non-Degenerate TLS Dynamics

## 📖 Overview

Experiment 16 compares two interacting TLS systems having identical coupling but different resonance-frequency configurations.

Two scenarios are considered:

- Non-degenerate TLS frequencies
- Degenerate TLS frequencies

---

## 🎯 Scientific Objective

Study how resonance-frequency degeneracy affects transient dynamics and frequency-domain signatures.

---

## 📂 Files

| File | Description |
|------|-------------|
| figure16_time_domain.pkl | Population and phase evolution |
| figure16_phase_fft.pkl | Phase FFT spectra |
| figure16_metadata.json | Simulation metadata |
| *_column_info.json | Feature documentation |

---

## 📊 Dataset Summary

Configurations

- Degenerate
- Non-degenerate

Measured quantities

- Population
- Phase difference
- FFT spectrum

---

## 📑 Dataset Schema

### Experimental Conditions

| Column | Description |
|---------|-------------|
| sample_id | Experiment identifier |
| figure_id | Figure identifier |
| configuration | Degenerate / Non-degenerate |
| omega_tls_1_GHz | First TLS frequency |
| omega_tls_2_GHz | Second TLS frequency |
| coupling_GHz | TLS coupling |

---

### Pulse Parameters

| Column | Description |
|---------|-------------|
| drive_amplitude_GHz | Microwave amplitude |
| pulse_duration_ns | Pulse duration |
| total_time_ns | Total simulation time |

---

### Time-Domain Dataset

| Column | Description |
|---------|-------------|
| drive_frequency_GHz | Applied frequency |
| time_ns | Simulation time |
| collective_population | Population observable |
| phase_difference_rad | Relative phase |

---

### FFT Dataset

| Column | Description |
|---------|-------------|
| drive_frequency_GHz | Applied frequency |
| fft_frequency_MHz | FFT frequency |
| normalized_phase_fft | Normalized phase FFT |

---

## ⚙ Variable Parameters

- TLS resonance frequencies
- Drive frequency

Fixed parameters

- Coupling
- Pulse duration
- Drive amplitude

---

## 🤖 Applications

- Binary classification
- System identification
- Degeneracy detection
- Quantum state characterization
- Spectral learning

---

## 📚 Citation

See the accompanying publication.