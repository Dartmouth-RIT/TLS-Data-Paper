# TLS-Data-Paper

Data and dataset creation scripts accompanying the manuscript:

> *Spectroscopy and Coherent Control of Two-Level System Defect Ensembles Using a Broadband 3D Waveguide*

---

## Repository structure

```
src/
  dataset_creation_scripts/
    pulse_width_sweep/
      experiment_2_dataset_creation.py   ← builds pulse width sweep dataset from raw .npy files
      README.md
      column_info.json
      metadata.json
      experiment_2/
        README.md                        ← dataset documentation
    amplitude_control/
      emperiment_3_dataset_creation.py   ← builds amplitude control dataset from raw .npy files
      README.md
      column_info.json
      metadata.json
      experiment_3/
        README.md                        ← dataset documentation
        figure3_dataset_long.npz         ← full dataset (1,800,000 rows × 8 columns)
        figure3_long_preview.csv         ← first + last 5 traces for quick inspection
```

---

## Experiments

| Experiment | Description | Dataset rows | Key swept variables |
|---|---|---|---|
| [Pulse Width Sweep](src/dataset_creation_scripts/pulse_width_sweep/experiment_2/README.md) | Single-pulse width sweep, silicon SiOx sample | 21,000,000 | pulse width (42 values), frequency (500 values) |
| [Amplitude Control](src/dataset_creation_scripts/amplitude_control/experiment_3/README.md) | Two-pulse coherent control amplitude sweep, 3 samples | 1,800,000 | amplitude (100 values), pulse spacing (6 values) |

---

## Generating datasets from raw data

Each script accepts the path to the raw `.npy` files and an output directory:

```bash
# Pulse Width Sweep
python src/dataset_creation_scripts/pulse_width_sweep/experiment_2_dataset_creation.py \
    --data_dir  /path/to/pulse_width_sweep/raw/npy \
    --output_dir /path/to/output

# Amplitude Control
python src/dataset_creation_scripts/amplitude_control/emperiment_3_dataset_creation.py \
    --data_dir  /path/to/amplitude_control/raw/npy \
    --output_dir /path/to/output
```

Both scripts run sanity checks automatically after building and print a pass/fail report.

---

## Dependencies

```
numpy
pandas
tqdm
```
