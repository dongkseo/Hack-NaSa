#!/usr/bin/env python3
"""
PyTorch Dataset for Gesture Recognition
"""
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
import numpy as np
from typing import Tuple
import config


class GestureDataset(Dataset):
    """PyTorch Dataset for gesture recognition"""

    def __init__(self, X: np.ndarray, y: np.ndarray, augment: bool = False):
        """
        Args:
            X: (N, 128, 100) Doppler spectrograms
            y: (N,) class labels
            augment: Whether to apply data augmentation
        """
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)
        self.augment = augment

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        x = self.X[idx]
        y = self.y[idx]

        if self.augment:
            x = self._augment(x)

        return x, y

    def _augment(self, x: torch.Tensor) -> torch.Tensor:
        """
        Apply data augmentation

        Args:
            x: (128, 100) tensor

        Returns:
            Augmented tensor
        """
        # Random Gaussian noise
        if config.USE_AUGMENTATION and torch.rand(1).item() > 0.5:
            noise = torch.randn_like(x) * config.NOISE_STD
            x = x + noise

        # Random amplitude scaling
        if config.USE_AUGMENTATION and torch.rand(1).item() > 0.5:
            scale = torch.FloatTensor(1).uniform_(*config.SCALE_RANGE).item()
            x = x * scale

        # Clip to valid range
        x = torch.clamp(x, 0, 1)

        return x


def create_dataloaders(X: np.ndarray, y: np.ndarray) -> Tuple[DataLoader, DataLoader]:
    """
    Create train and validation dataloaders

    Args:
        X: (N, 128, 100) array
        y: (N,) array

    Returns:
        train_loader, val_loader
    """
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y,
        test_size=config.VAL_SPLIT,
        random_state=config.RANDOM_SEED,
        stratify=y
    )

    print(f"\nData split:")
    print(f"  Train: {len(X_train)} samples")
    print(f"  Val:   {len(X_val)} samples")

    # Create datasets
    train_dataset = GestureDataset(X_train, y_train, augment=True)
    val_dataset = GestureDataset(X_val, y_val, augment=False)

    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=True,
        num_workers=0,  # Set to 0 to avoid multiprocessing issues
        pin_memory=True if torch.cuda.is_available() else False
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=True if torch.cuda.is_available() else False
    )

    return train_loader, val_loader


def compute_class_weights(y: np.ndarray) -> torch.Tensor:
    """
    Compute class weights for imbalanced data

    Args:
        y: (N,) class labels

    Returns:
        weights: (num_classes,) tensor
    """
    from sklearn.utils.class_weight import compute_class_weight

    classes = np.unique(y)
    weights = compute_class_weight(
        'balanced',
        classes=classes,
        y=y
    )

    weights_tensor = torch.FloatTensor(weights)

    print(f"\nClass weights:")
    for i, gesture in enumerate(config.GESTURES):
        print(f"  {gesture}: {weights[i]:.3f}")

    return weights_tensor


if __name__ == "__main__":
    # Test dataset
    from data_loader import load_and_prepare_data

    print("Testing dataset...")
    X, y = load_and_prepare_data()

    # Create dataloaders
    train_loader, val_loader = create_dataloaders(X, y)

    print(f"\nDataloader info:")
    print(f"  Train batches: {len(train_loader)}")
    print(f"  Val batches: {len(val_loader)}")

    # Test one batch
    x_batch, y_batch = next(iter(train_loader))
    print(f"\nBatch shapes:")
    print(f"  x: {x_batch.shape}")
    print(f"  y: {y_batch.shape}")

    # Compute class weights
    class_weights = compute_class_weights(y)
