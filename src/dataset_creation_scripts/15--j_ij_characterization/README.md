# 📕 Experiment 15 — Interaction Strength Characterization

## 📖 Overview

Experiment 15 investigates how the interaction strength between multiple TLS defects influences transient quantum dynamics.

Three interaction regimes (Low-J, Mid-J, and High-J) are simulated using a four-TLS system.

---

## 🎯 Scientific Objective

Understand the influence of coupling strength on transient spectroscopy and frequency-domain signatures.

---

## 📂 Files

| File | Description |
|------|-------------|
| figure15_time_domain.pkl | Population and phase dynamics |
| figure15_fft_domain.pkl | FFT spectra |
| figure15_tls_frequencies.pkl | Random TLS frequencies |
| figure15_metadata.json | Simulation metadata |
| *_column_info.json | Feature documentation |

---

## 📊 Dataset Summary

Simulation includes

- 4 interacting TLS defects
- Random frequency distribution
- Three coupling strengths

Observables

- Population
- Phase
- FFT spectra

---

## 📑 Dataset Schema

### Experimental Conditions

| Column | Description |
|---------|-------------|
| sample_id | Experiment identifier |
| figure_id | Figure identifier |
| j_label | Low, Mid or High interaction regime |
| j_coupling_GHz | Uniform interaction strength |
| n_tls | Number of TLS defects |

---

### Simulation Parameters

| Column | Description |
|---------|-------------|
| drive_amp_GHz | Microwave drive amplitude |
| pulse_duration_ns | Pulse duration |
| pulse_ramp_ns | Pulse ramp |
| gamma_collective_GHz | Collective decay |
| gamma_phi_GHz | Pure dephasing |

---

### Time-Domain Dataset

| Column | Description |
|---------|-------------|
| drive_frequency_GHz | Applied frequency |
| time_ns | Simulation time |
| population | Collective population |
| phase_rad | Homodyne phase |

---

### FFT Dataset

| Column | Description |
|---------|-------------|
| drive_frequency_GHz | Applied frequency |
| fft_frequency_MHz | FFT frequency |
| log10_fft_population | Population FFT |
| log10_fft_phase | Phase FFT |

---

### TLS Configuration Dataset

| Column | Description |
|---------|-------------|
| tls_index | TLS identifier |
| tls_frequency_GHz | Bare TLS resonance frequency |

---

## ⚙ Interaction Regimes

- Low J
- Medium J
- High J

---

## 🤖 Applications

- Interaction estimation
- Graph learning
- Spectral clustering
- Quantum system identification
- Representation learning

---

## 📚 Citation

See the accompanying publication.