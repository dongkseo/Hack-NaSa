#!/usr/bin/env python3
"""
Data Loader for CSI Gesture Recognition
Handles .npy file loading and Doppler profile extraction
"""
import numpy as np
from scipy.fftpack import fft, fftshift
from scipy.signal.windows import hann
from pathlib import Path
from typing import List, Tuple
import config


class DopplerExtractor:
    """Extract Doppler profiles from CSI data"""

    def __init__(self):
        self.sample_length = config.SAMPLE_LENGTH
        self.doppler_size = config.DOPPLER_SIZE
        self.num_subcarriers = config.NUM_SUBCARRIERS

    def compute_doppler_profile(self, csi_frames: np.ndarray) -> np.ndarray:
        """
        Compute Doppler profile from CSI frames

        Args:
            csi_frames: (sample_length, 4004) complex CSI data

        Returns:
            doppler_profile: (100,) Doppler spectrum
        """
        if len(csi_frames) < self.sample_length:
            return None

        # Reshape to (time, subcarriers, antennas, streams) and average
        csi_matrix = []
        for frame in csi_frames:
            # (4004,) -> (1001, 2, 2) then average over antennas
            frame_reshaped = frame.reshape(self.num_subcarriers,
                                          config.NUM_ANTENNAS,
                                          config.NUM_SPATIAL_STREAMS)
            frame_avg = np.mean(frame_reshaped, axis=(1, 2))  # (1001,)
            csi_matrix.append(frame_avg)

        csi_matrix = np.array(csi_matrix)  # (25, 1001)

        # Normalize by mean amplitude
        mean_amp = np.mean(np.abs(csi_matrix), axis=1, keepdims=True)
        mean_amp = np.maximum(mean_amp, 1e-10)
        csi_matrix = csi_matrix / mean_amp

        # Apply Hann window
        hann_window = hann(self.sample_length)[:, np.newaxis]
        csi_matrix_windowed = csi_matrix * hann_window

        # Compute Doppler via FFT
        csi_doppler = fft(csi_matrix_windowed, n=self.doppler_size, axis=0)
        csi_doppler = fftshift(csi_doppler, axes=0)

        # Power spectrum
        csi_d_map = np.abs(csi_doppler) ** 2
        csi_d_profile = np.sum(csi_d_map, axis=1)  # Sum over subcarriers

        # Log-scale normalization
        csi_d_profile = np.log10(csi_d_profile + 1e-10)

        # Percentile-based normalization (robust to outliers)
        p_min, p_max = np.percentile(csi_d_profile, [5, 95])
        if p_max > p_min:
            csi_d_profile = (csi_d_profile - p_min) / (p_max - p_min)
            csi_d_profile = np.clip(csi_d_profile, 0, 1)

        return csi_d_profile

    def process_csi_file(self, filepath: Path) -> List[np.ndarray]:
        """
        Process a single .npy file into Doppler windows

        Args:
            filepath: Path to .npy file

        Returns:
            samples: List of (128, 100) Doppler spectrograms
        """
        # Load CSI data
        csi_data = np.load(filepath, allow_pickle=True)  # (N, 4004) complex

        # Validate data
        if csi_data.size == 0 or len(csi_data) == 0:
            print(f"    WARNING: Empty file {filepath.name}, skipping")
            return []

        if csi_data.shape[1] != 4004:
            print(f"    WARNING: Unexpected shape {csi_data.shape} in {filepath.name}, skipping")
            return []

        if len(csi_data) < self.sample_length:
            print(f"    WARNING: Too short ({len(csi_data)} frames) {filepath.name}, skipping")
            return []

        # Extract Doppler profiles with sliding window
        doppler_profiles = []
        for i in range(0, len(csi_data) - self.sample_length, 1):
            window = csi_data[i:i+self.sample_length]
            doppler = self.compute_doppler_profile(window)
            if doppler is not None:
                doppler_profiles.append(doppler)

        # Create samples with sliding window over Doppler profiles
        samples = []
        window_size = config.WINDOW_SIZE
        stride = config.STRIDE

        for i in range(0, len(doppler_profiles) - window_size, stride):
            window = doppler_profiles[i:i+window_size]
            window_array = np.array(window)  # (128, 100)
            samples.append(window_array)

        return samples


def load_gesture_data(data_dir: Path = None) -> Tuple[List[np.ndarray], List[int], List[str]]:
    """
    Load all gesture data from directory

    Args:
        data_dir: Directory containing .npy files

    Returns:
        samples: List of (128, 100) arrays
        labels: List of class indices
        filenames: List of source filenames
    """
    if data_dir is None:
        data_dir = config.DATA_DIR

    extractor = DopplerExtractor()

    samples = []
    labels = []
    filenames = []

    print(f"\nLoading gesture data from: {data_dir}")
    print("="*70)

    for class_idx, gesture in enumerate(config.GESTURES):
        print(f"\n[{gesture.upper()}]")
        pattern = f"{gesture}_*.npy"
        files = sorted(data_dir.glob(pattern))

        if len(files) == 0:
            print(f"  WARNING: No files found for {gesture}")
            continue

        print(f"  Found {len(files)} files")

        gesture_samples = 0
        for filepath in files:
            # Check if file exists
            if not filepath.exists():
                print(f"    WARNING: File not found {filepath.name}, skipping")
                continue

            file_samples = extractor.process_csi_file(filepath)
            for sample in file_samples:
                samples.append(sample)
                labels.append(class_idx)
                filenames.append(filepath.name)
            gesture_samples += len(file_samples)

        print(f"  Generated {gesture_samples} training samples")

    print("\n" + "="*70)
    print(f"TOTAL: {len(samples)} samples")
    for i, gesture in enumerate(config.GESTURES):
        count = sum(1 for l in labels if l == i)
        pct = count / len(labels) * 100 if len(labels) > 0 else 0
        print(f"  {gesture}: {count} samples ({pct:.1f}%)")
    print("="*70)

    return samples, labels, filenames


def load_and_prepare_data() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load all data and prepare for training

    Returns:
        X: (N, 128, 100) array
        y: (N,) array of class indices
    """
    samples, labels, _ = load_gesture_data()

    X = np.array(samples, dtype=np.float32)  # (N, 128, 100)
    y = np.array(labels, dtype=np.int64)     # (N,)

    print(f"\nFinal data shape:")
    print(f"  X: {X.shape}")
    print(f"  y: {y.shape}")

    return X, y


if __name__ == "__main__":
    # Test data loading
    print("Testing data loader...")
    X, y = load_and_prepare_data()

    print(f"\nData statistics:")
    print(f"  X range: [{X.min():.3f}, {X.max():.3f}]")
    print(f"  X mean: {X.mean():.3f}")
    print(f"  X std: {X.std():.3f}")
    print(f"  y unique: {np.unique(y)}")
