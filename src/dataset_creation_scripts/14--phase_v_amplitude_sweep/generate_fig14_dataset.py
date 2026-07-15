"""
generate_fig14_dataset.py
=========================
Create clean interpretable Pickle dataframes from Figure 14 raw IQ .npy files.

Raw .npy contents:
    IQ_matrix[0] -> I
    IQ_matrix[1] -> Q

Outputs:
    dataset/
        figure14_dataset_long.pkl
        figure14_dataset_long_column_info.json

        figure14_time_domain_derived_preview.pkl
        figure14_time_domain_derived_preview_column_info.json

        figure14_zero_time_slices.pkl
        figure14_zero_time_slices_column_info.json

        figure14_saturation_slice_4487MHz.pkl
        figure14_saturation_slice_4487MHz_column_info.json

        figure14_metadata.json
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm

SAMPLE_ID = "1950"

ADC_CLOCK_MHZ = 552.96
DT_NS = 1000.0 / ADC_CLOCK_MHZ

DISPLAY_OFFSET = 25
TRANSIENT_PROCESSING_OFFSET = 110
TP_START_SAMPLE = DISPLAY_OFFSET + TRANSIENT_PROCESSING_OFFSET

FREQUENCY_LIST_MHZ = np.arange(4100, 4600, 1).astype(np.int32)
FREQUENCY_LIST_GHZ = FREQUENCY_LIST_MHZ.astype(np.float32) / 1000.0

PULSE_AMP_AVAILABLE_LIST = np.concatenate(
    [
        np.arange(0, 1000, 50),
        np.arange(1000, 5000, 200),
        np.arange(5000, 30001, 1000),
    ]
).astype(np.int32)

PULSE_AMP_PLOT_LIST = np.arange(0, 30001, 1000).astype(np.int32)

SATURATION_FREQ_MHZ = 4487
SATURATION_FREQ_IDX = SATURATION_FREQ_MHZ - 4100


MAIN_COLUMNS = [
    "sample_id",
    "requested_pulse_amp_au",
    "available_pulse_amp_au",
    "frequency_MHz",
    "frequency_GHz",
    "raw_time_index",
    "timestamp_ns_raw",
    "I",
    "Q",
]

DERIVED_PREVIEW_COLUMNS = [
    "sample_id",
    "requested_pulse_amp_au",
    "available_pulse_amp_au",
    "frequency_MHz",
    "frequency_GHz",
    "time_index_after_tp",
    "timestamp_ns_after_toff",
    "I",
    "Q",
    "amplitude",
    "phase_rad",
    "log10_amplitude",
    "intensity",
]

ZERO_SLICE_COLUMNS = [
    "sample_id",
    "requested_pulse_amp_au",
    "available_pulse_amp_au",
    "frequency_MHz",
    "frequency_GHz",
    "zero_time_log10_amplitude",
    "zero_fft_frequency_MHz",
    "zero_freq_phase_fft",
]

SATURATION_COLUMNS = [
    "sample_id",
    "requested_pulse_amp_au",
    "available_pulse_amp_au",
    "frequency_MHz",
    "frequency_GHz",
    "zero_time_log10_amplitude",
    "zero_freq_phase_fft",
]


def load_iq_matrix(filepath: str) -> np.ndarray:
    """
    Load and validate a Figure 14 IQ matrix.

    Expected shape:
        (2, 500, n_time_samples)

    Channel mapping:
        array[0] = I
        array[1] = Q
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, "rb") as file:
        header = file.read(128)

    if header.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise RuntimeError(
            f"{filepath} is a Git LFS pointer rather than the actual data file.\n"
            "Run:\n"
            "    git lfs install\n"
            "    git lfs pull"
        )

    if not header.startswith(b"\x93NUMPY"):
        raise ValueError(
            f"{filepath} does not have a valid NumPy .npy header.\n"
            f"First bytes: {header[:80]!r}"
        )

    iq_matrix = np.load(filepath, allow_pickle=False)

    if not isinstance(iq_matrix, np.ndarray):
        raise TypeError(f"Expected a NumPy array, got {type(iq_matrix).__name__}")

    if iq_matrix.dtype == object:
        raise TypeError(
            f"{filepath} has object dtype. The original BCTDS data are "
            "expected to be numeric I/Q arrays."
        )

    if iq_matrix.ndim != 3:
        raise ValueError(
            f"Expected a 3D IQ array, but {filepath} has " f"shape {iq_matrix.shape}."
        )

    # Support an alternate channel-last representation if necessary.
    if iq_matrix.shape[0] != 2 and iq_matrix.shape[-1] == 2:
        iq_matrix = np.moveaxis(iq_matrix, -1, 0)

    if iq_matrix.shape[0] != 2:
        raise ValueError(
            f"Expected two IQ channels on axis 0, but got " f"shape {iq_matrix.shape}."
        )

    expected_frequencies = len(FREQUENCY_LIST_MHZ)

    if iq_matrix.shape[1] != expected_frequencies:
        raise ValueError(
            f"Expected {expected_frequencies} frequency rows, but "
            f"{filepath} contains {iq_matrix.shape[1]}."
        )

    if iq_matrix.shape[2] <= TP_START_SAMPLE:
        raise ValueError(
            f"The file has only {iq_matrix.shape[2]} time samples, "
            f"but cropping starts at sample {TP_START_SAMPLE}."
        )

    return iq_matrix.astype(np.float32, copy=False)


def schema_entry(
    column_name,
    data_type,
    can_have_nulls,
    maps_to_original,
    value_or_range,
    in_raw_npy,
    derivation_or_notes,
):
    return {
        "column_name": column_name,
        "data_type": data_type,
        "can_have_nulls": can_have_nulls,
        "maps_to_original": maps_to_original,
        "value_or_range": value_or_range,
        "num_columns": 1,
        "in_raw_npy": in_raw_npy,
        "derivation_or_notes": derivation_or_notes,
    }


MAIN_COLUMN_INFO = [
    schema_entry(
        "sample_id",
        "string",
        False,
        "filename prefix",
        "1950",
        False,
        "Sample or measurement identifier parsed from filename.",
    ),
    schema_entry(
        "requested_pulse_amp_au",
        "int32",
        False,
        "pulse_amp_plot_list",
        "0 to 30000 a.u.",
        False,
        "Requested amplitude used in the amplitude sweep.",
    ),
    schema_entry(
        "available_pulse_amp_au",
        "int32",
        False,
        "1950_amp_<available_amp>_IQ_avg_matrix_0.npy",
        "0 to 30000 a.u.",
        False,
        "Actual raw amplitude file loaded.",
    ),
    schema_entry(
        "frequency_MHz",
        "int32",
        False,
        "frequency row index",
        "4100 to 4599 MHz",
        False,
        "Drive frequency associated with each matrix row.",
    ),
    schema_entry(
        "frequency_GHz",
        "float32",
        False,
        "frequency_MHz / 1000",
        "4.100 to 4.599 GHz",
        False,
        "Drive frequency converted to GHz.",
    ),
    schema_entry(
        "raw_time_index",
        "int32",
        False,
        "raw time-axis index",
        "0 to n_time - 1",
        False,
        "Original sample index before cropping.",
    ),
    schema_entry(
        "timestamp_ns_raw",
        "float32",
        False,
        "raw_time_index * 1000 / 552.96",
        ">= 0 ns",
        False,
        "Raw timestamp from ADC sampling rate.",
    ),
    schema_entry(
        "I",
        "float32",
        False,
        "IQ_matrix[0]",
        "ADC dependent",
        True,
        "In-phase homodyne channel. This is one of only two raw columns stored in the .npy file.",
    ),
    schema_entry(
        "Q",
        "float32",
        False,
        "IQ_matrix[1]",
        "ADC dependent",
        True,
        "Quadrature homodyne channel. This is one of only two raw columns stored in the .npy file.",
    ),
]

DERIVED_PREVIEW_COLUMN_INFO = [
    *MAIN_COLUMN_INFO[:5],
    schema_entry(
        "time_index_after_tp",
        "int32",
        False,
        "raw time-axis index after TP_START_SAMPLE",
        "0 to n_tp - 1",
        False,
        "Index after removing display offset and transient-processing offset.",
    ),
    schema_entry(
        "timestamp_ns_after_toff",
        "float32",
        False,
        "time_index_after_tp * 1000 / 552.96",
        ">= 0 ns",
        False,
        "Timestamp after transient-processing start.",
    ),
    MAIN_COLUMN_INFO[-2],
    MAIN_COLUMN_INFO[-1],
    schema_entry(
        "amplitude",
        "float32",
        False,
        "sqrt(I^2 + Q^2)",
        ">= 0",
        False,
        "Magnitude of complex homodyne signal.",
    ),
    schema_entry(
        "phase_rad",
        "float32",
        False,
        "angle(I + iQ)",
        "[-pi, pi]",
        False,
        "Wrapped phase of complex homodyne signal.",
    ),
    schema_entry(
        "log10_amplitude",
        "float32",
        False,
        "log10(amplitude + 0.01)",
        "typically around -2 to 3",
        False,
        "Log-scaled amplitude used in Figure 14 plots.",
    ),
    schema_entry(
        "intensity", "float32", False, "amplitude^2", ">= 0", False, "Signal intensity."
    ),
]

ZERO_SLICE_COLUMN_INFO = [
    *MAIN_COLUMN_INFO[:5],
    schema_entry(
        "zero_time_log10_amplitude",
        "float32",
        False,
        "log10_amplitude_tp[:, 0]",
        "typically around -2 to 3",
        False,
        "First transient-processing time sample.",
    ),
    schema_entry(
        "zero_fft_frequency_MHz",
        "float32",
        False,
        "FFT frequency axis index 0",
        "0 MHz",
        False,
        "Zero-frequency FFT slice.",
    ),
    schema_entry(
        "zero_freq_phase_fft",
        "float32",
        False,
        "abs(fft(phase_tp))[0]",
        ">= 0",
        False,
        "Phase FFT magnitude at 0 MHz.",
    ),
]

SATURATION_COLUMN_INFO = [
    *MAIN_COLUMN_INFO[:5],
    schema_entry(
        "zero_time_log10_amplitude",
        "float32",
        False,
        "log10_amplitude_tp[4487 MHz, 0]",
        "typically around -2 to 3",
        False,
        "Zero-time log amplitude at the saturation slice frequency.",
    ),
    schema_entry(
        "zero_freq_phase_fft",
        "float32",
        False,
        "abs(fft(phase_tp[4487 MHz]))[0]",
        ">= 0",
        False,
        "Zero-frequency phase FFT at the saturation slice frequency.",
    ),
]


def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def fft_custom(trace, dt_us):
    n = len(trace)
    fft_result = np.fft.fft(trace, n)
    frequencies = np.fft.fftfreq(n, dt_us)
    return frequencies[: n // 2], np.abs(fft_result)[: n // 2]


def get_available_amp(requested_amp):
    valid = PULSE_AMP_AVAILABLE_LIST[PULSE_AMP_AVAILABLE_LIST <= requested_amp]
    if len(valid) == 0:
        raise ValueError(f"No available amplitude for requested_amp={requested_amp}")
    return int(valid[-1])


def save_pickle(df, path):
    df.to_pickle(path)
    size_mb = os.path.getsize(path) / (1024**2)
    print(f"Saved: {path} ({size_mb:.1f} MB)")


def build_main_dataframe_block(I_matrix, Q_matrix, requested_amp, available_amp):
    n_freqs, n_time = I_matrix.shape
    n_rows = n_freqs * n_time

    raw_time_index = np.arange(n_time, dtype=np.int32)
    timestamp_ns = raw_time_index.astype(np.float32) * np.float32(DT_NS)

    return pd.DataFrame(
        {
            "sample_id": np.full(n_rows, SAMPLE_ID, dtype=object),
            "requested_pulse_amp_au": np.full(n_rows, requested_amp, dtype=np.int32),
            "available_pulse_amp_au": np.full(n_rows, available_amp, dtype=np.int32),
            "frequency_MHz": np.repeat(FREQUENCY_LIST_MHZ, n_time).astype(np.int32),
            "frequency_GHz": np.repeat(FREQUENCY_LIST_GHZ, n_time).astype(np.float32),
            "raw_time_index": np.tile(raw_time_index, n_freqs),
            "timestamp_ns_raw": np.tile(timestamp_ns, n_freqs).astype(np.float32),
            "I": I_matrix.reshape(-1).astype(np.float32),
            "Q": Q_matrix.reshape(-1).astype(np.float32),
        }
    )


def build_dataset(data_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    output_main_pkl = os.path.join(output_dir, "figure14_dataset_long.pkl")
    output_preview_pkl = os.path.join(
        output_dir, "figure14_time_domain_derived_preview.pkl"
    )
    output_zero_pkl = os.path.join(output_dir, "figure14_zero_time_slices.pkl")
    output_saturation_pkl = os.path.join(
        output_dir, "figure14_saturation_slice_4487MHz.pkl"
    )
    metadata_path = os.path.join(output_dir, "figure14_metadata.json")

    main_blocks = []
    preview_blocks = []
    zero_rows = []
    saturation_rows = []

    print("\nBuilding Figure 14 datasets")
    print(f"Data directory   : {data_dir}")
    print(f"Output directory : {output_dir}")
    print("Raw .npy columns : I, Q only\n")

    for requested_amp in tqdm(PULSE_AMP_AVAILABLE_LIST, desc="Loading amplitude files"):
        requested_amp = int(requested_amp)
        available_amp = get_available_amp(requested_amp)

        filename = f"{SAMPLE_ID}_amp_{available_amp}_IQ_avg_matrix_0.npy"
        filepath = os.path.join(data_dir, filename)

        if not os.path.exists(filepath):
            print(f"WARNING: missing file {filename}; skipping")
            continue

        # IQ_matrix = np.load(filepath)
        try:
            IQ_matrix = load_iq_matrix(filepath)
        except Exception as exc:
            raise RuntimeError(
                f"Failed while loading Figure 14 file:\n{filepath}"
            ) from exc

        if IQ_matrix.ndim != 3 or IQ_matrix.shape[0] != 2:
            print(
                f"WARNING: unexpected shape {IQ_matrix.shape} for {filename}; skipping"
            )
            continue

        I_matrix = IQ_matrix[0].astype(np.float32)
        Q_matrix = IQ_matrix[1].astype(np.float32)

        if I_matrix.shape[0] != len(FREQUENCY_LIST_MHZ):
            print(
                f"WARNING: expected 500 frequencies, got {I_matrix.shape[0]} for {filename}; skipping"
            )
            continue

        main_blocks.append(
            build_main_dataframe_block(
                I_matrix=I_matrix,
                Q_matrix=Q_matrix,
                requested_amp=requested_amp,
                available_amp=available_amp,
            )
        )

        complex_matrix = I_matrix + 1j * Q_matrix
        amplitude_matrix = np.abs(complex_matrix).astype(np.float32)
        phase_matrix = np.angle(complex_matrix).astype(np.float32)
        log10_amplitude_matrix = np.log10(amplitude_matrix + np.float32(0.01)).astype(
            np.float32
        )
        intensity_matrix = (amplitude_matrix**2).astype(np.float32)

        I_tp = I_matrix[:, TP_START_SAMPLE:]
        Q_tp = Q_matrix[:, TP_START_SAMPLE:]
        amplitude_tp = amplitude_matrix[:, TP_START_SAMPLE:]
        phase_tp = phase_matrix[:, TP_START_SAMPLE:]
        log10_amplitude_tp = log10_amplitude_matrix[:, TP_START_SAMPLE:]
        intensity_tp = intensity_matrix[:, TP_START_SAMPLE:]

        n_tp = I_tp.shape[1]
        time_index_after_tp = np.arange(n_tp, dtype=np.int32)
        timestamp_ns_after_toff = time_index_after_tp.astype(np.float32) * np.float32(
            DT_NS
        )

        if requested_amp in [0, 1000, 5000, 30000]:
            for freq_mhz in [4100, 4250, 4487, 4599]:
                freq_idx = freq_mhz - 4100

                preview_blocks.append(
                    pd.DataFrame(
                        {
                            "sample_id": np.full(n_tp, SAMPLE_ID, dtype=object),
                            "requested_pulse_amp_au": np.full(
                                n_tp, requested_amp, dtype=np.int32
                            ),
                            "available_pulse_amp_au": np.full(
                                n_tp, available_amp, dtype=np.int32
                            ),
                            "frequency_MHz": np.full(n_tp, freq_mhz, dtype=np.int32),
                            "frequency_GHz": np.full(
                                n_tp, freq_mhz / 1000.0, dtype=np.float32
                            ),
                            "time_index_after_tp": time_index_after_tp,
                            "timestamp_ns_after_toff": timestamp_ns_after_toff,
                            "I": I_tp[freq_idx].astype(np.float32),
                            "Q": Q_tp[freq_idx].astype(np.float32),
                            "amplitude": amplitude_tp[freq_idx].astype(np.float32),
                            "phase_rad": phase_tp[freq_idx].astype(np.float32),
                            "log10_amplitude": log10_amplitude_tp[freq_idx].astype(
                                np.float32
                            ),
                            "intensity": intensity_tp[freq_idx].astype(np.float32),
                        }
                    )
                )

        dt_us = DT_NS / 1000.0
        zero_freq_phase_fft = np.empty(len(FREQUENCY_LIST_MHZ), dtype=np.float32)

        for freq_idx, freq_mhz in enumerate(FREQUENCY_LIST_MHZ):
            _, phase_fft = fft_custom(phase_tp[freq_idx], dt_us)
            zero_freq_phase_fft[freq_idx] = np.float32(phase_fft[0])

            zero_rows.append(
                {
                    "sample_id": SAMPLE_ID,
                    "requested_pulse_amp_au": np.int32(requested_amp),
                    "available_pulse_amp_au": np.int32(available_amp),
                    "frequency_MHz": np.int32(freq_mhz),
                    "frequency_GHz": np.float32(freq_mhz / 1000.0),
                    "zero_time_log10_amplitude": np.float32(
                        log10_amplitude_tp[freq_idx, 0]
                    ),
                    "zero_fft_frequency_MHz": np.float32(0.0),
                    "zero_freq_phase_fft": np.float32(phase_fft[0]),
                }
            )

        saturation_rows.append(
            {
                "sample_id": SAMPLE_ID,
                "requested_pulse_amp_au": np.int32(requested_amp),
                "available_pulse_amp_au": np.int32(available_amp),
                "frequency_MHz": np.int32(SATURATION_FREQ_MHZ),
                "frequency_GHz": np.float32(SATURATION_FREQ_MHZ / 1000.0),
                "zero_time_log10_amplitude": np.float32(
                    log10_amplitude_tp[SATURATION_FREQ_IDX, 0]
                ),
                "zero_freq_phase_fft": np.float32(
                    zero_freq_phase_fft[SATURATION_FREQ_IDX]
                ),
            }
        )

    if not main_blocks:
        raise RuntimeError("No valid .npy files were loaded.")

    main_df = pd.concat(main_blocks, ignore_index=True)
    preview_df = (
        pd.concat(preview_blocks, ignore_index=True)
        if preview_blocks
        else pd.DataFrame(columns=DERIVED_PREVIEW_COLUMNS)
    )
    zero_df = pd.DataFrame(zero_rows, columns=ZERO_SLICE_COLUMNS)
    saturation_df = pd.DataFrame(saturation_rows, columns=SATURATION_COLUMNS)

    print("\nSaving Pickle files...")
    save_pickle(main_df, output_main_pkl)
    save_pickle(preview_df, output_preview_pkl)
    save_pickle(zero_df, output_zero_pkl)
    save_pickle(saturation_df, output_saturation_pkl)

    print("\nSaving column-info JSON files...")
    save_json(
        MAIN_COLUMN_INFO,
        os.path.join(output_dir, "figure14_dataset_long_column_info.json"),
    )
    save_json(
        DERIVED_PREVIEW_COLUMN_INFO,
        os.path.join(
            output_dir, "figure14_time_domain_derived_preview_column_info.json"
        ),
    )
    save_json(
        ZERO_SLICE_COLUMN_INFO,
        os.path.join(output_dir, "figure14_zero_time_slices_column_info.json"),
    )
    save_json(
        SATURATION_COLUMN_INFO,
        os.path.join(output_dir, "figure14_saturation_slice_4487MHz_column_info.json"),
    )

    metadata = {
        "figure": "Figure 14",
        "description": "Pulse-amplitude sweep converted from raw IQ npy files to Pickle dataframes.",
        "raw_npy_contains": ["I", "Q"],
        "raw_npy_shape_expected": "[2, 500, n_time]",
        "sample_id": SAMPLE_ID,
        "adc_clock_mhz": ADC_CLOCK_MHZ,
        "dt_ns": DT_NS,
        "display_offset_samples": DISPLAY_OFFSET,
        "transient_processing_offset_samples": TRANSIENT_PROCESSING_OFFSET,
        "tp_start_sample": TP_START_SAMPLE,
        "frequency_MHz_start": int(FREQUENCY_LIST_MHZ[0]),
        "frequency_MHz_stop_inclusive": int(FREQUENCY_LIST_MHZ[-1]),
        # "requested_pulse_amp_au_values": PULSE_AMP_PLOT_LIST.astype(int).tolist(),
        "available_pulse_amp_au_values": PULSE_AMP_AVAILABLE_LIST.astype(int).tolist(),
        "saturation_frequency_MHz": int(SATURATION_FREQ_MHZ),
        "outputs": {
            "main_long_pickle": os.path.basename(output_main_pkl),
            "main_long_column_info": "figure14_dataset_long_column_info.json",
            "derived_preview_pickle": os.path.basename(output_preview_pkl),
            "derived_preview_column_info": "figure14_time_domain_derived_preview_column_info.json",
            "zero_time_slices_pickle": os.path.basename(output_zero_pkl),
            "zero_time_slices_column_info": "figure14_zero_time_slices_column_info.json",
            "saturation_slice_pickle": os.path.basename(output_saturation_pkl),
            "saturation_slice_column_info": "figure14_saturation_slice_4487MHz_column_info.json",
        },
    }

    save_json(metadata, metadata_path)

    print("\nDone.")
    print(f"Main shape       : {main_df.shape}")
    print(f"Preview shape    : {preview_df.shape}")
    print(f"Zero slice shape : {zero_df.shape}")
    print(f"Saturation shape : {saturation_df.shape}")
    print(f"Metadata         : {metadata_path}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Build Figure 14 IQ dataset in clean Pickle format."
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default=os.path.join(script_dir, "matrix_npy"),
        help="Folder containing 1950_amp_<amp>_IQ_avg_matrix_0.npy files.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.path.join(script_dir, "dataset"),
        help="Output folder.",
    )

    args = parser.parse_args()
    build_dataset(data_dir=args.data_dir, output_dir=args.output_dir)
