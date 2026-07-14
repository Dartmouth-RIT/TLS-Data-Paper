# 📘 Experiment 6 — Floquet Spectroscopy of a Numerical Two-TLS System

## 📖 Overview

This experiment reproduces the numerical Floquet spectroscopy presented in Figure 6 of the accompanying publication.

A coherently driven system consisting of two interacting two-level systems (TLSs) is simulated while sweeping the microwave drive frequency. The resulting transient population dynamics, phase evolution, and Floquet quasienergies are organized into machine learning-ready datasets.

---

## 🎯 Scientific Objective

Investigate how periodic microwave driving modifies the coherent dynamics of coupled TLS defects through Floquet engineering.

The dataset contains:

- transient population ringdown
- phase-V FFT spectra
- Floquet quasienergy branches

---

## 📂 Files

| File | Description |
|------|-------------|
| figure6_population_ringdown.pkl | Time-domain population dynamics |
| figure6_phase_fft.pkl | FFT of phase difference |
| figure6_floquet_quasienergies.pkl | Floquet quasienergy spectrum |
| figure6_metadata.json | Simulation metadata |
| *_column_info.json | Feature documentation |

---

## 📊 Dataset Summary

**Simulation**

- 2 TLS defects
- Numerical Lindblad evolution
- Drive frequency sweep
- Constant interaction strength

**Observables**

- Population
- Phase difference
- FFT spectrum
- Floquet quasienergies

---

## 📑 Dataset Schema

The datasets follow a standardized long-format representation in which each row corresponds to a single observation.

### Common Metadata

| Column | Description |
|---------|-------------|
| sample_id | Experiment identifier |
| figure_id | Figure identifier |
| omega_1_GHz | First TLS resonance frequency |
| omega_2_GHz | Second TLS resonance frequency |
| j_coupling_GHz | TLS interaction strength |
| drive_amp_GHz | Microwave drive amplitude |
| gamma_collective_GHz | Collective decay rate |
| drive_frequency_GHz | Applied microwave frequency |

---

### Population Ringdown Dataset

Additional columns

| Column | Description |
|---------|-------------|
| time_ns | Simulation time |
| population | Collective excitation population |

---

### Phase FFT Dataset

Additional columns

| Column | Description |
|---------|-------------|
| fft_frequency_GHz | FFT frequency axis |
| fft_frequency_MHz | FFT frequency axis (MHz) |
| normalized_phase_fft | Normalized FFT magnitude of phase difference |

---

### Floquet Dataset

Additional columns

| Column | Description |
|---------|-------------|
| quasi_branch | Floquet branch index |
| quasi_energy_GHz | Floquet quasienergy |
| quasi_energy_MHz | Floquet quasienergy (MHz) |

---

## 🤖 Machine Learning Applications

- Time-series forecasting
- Spectral prediction
- Floquet phase classification
- Parameter estimation
- Representation learning

---

## 📚 Citation

See the accompanying research paper for complete simulation details.