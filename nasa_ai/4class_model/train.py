#!/usr/bin/env python3
"""
Training Script for Gesture Recognition Model
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import time
from pathlib import Path

import config
from data_loader import load_and_prepare_data
from dataset import create_dataloaders, compute_class_weights
from model import GestureRecognitionModel, count_parameters


class EarlyStopping:
    """Early stopping to prevent overfitting"""

    def __init__(self, patience=7, min_delta=0, verbose=True):
        self.patience = patience
        self.min_delta = min_delta
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_acc_max = 0

    def __call__(self, val_acc, model, path):
        score = val_acc

        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(val_acc, model, path)
        elif score < self.best_score + self.min_delta:
            self.counter += 1
            if self.verbose:
                print(f'EarlyStopping counter: {self.counter}/{self.patience}')
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.save_checkpoint(val_acc, model, path)
            self.counter = 0

    def save_checkpoint(self, val_acc, model, path):
        if self.verbose:
            print(f'Validation accuracy increased ({self.val_acc_max:.4f} --> {val_acc:.4f}). Saving model...')
        torch.save(model.state_dict(), path)
        self.val_acc_max = val_acc


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    running_loss = 0.0
    all_preds = []
    all_labels = []

    for batch_idx, (data, target) in enumerate(dataloader):
        data, target = data.to(device), target.to(device)

        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        # Get predictions
        _, predicted = torch.max(output.data, 1)
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(target.cpu().numpy())

    epoch_loss = running_loss / len(dataloader)
    epoch_acc = accuracy_score(all_labels, all_preds)

    return epoch_loss, epoch_acc


def validate(model, dataloader, criterion, device):
    """Validate model"""
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for data, target in dataloader:
            data, target = data.to(device), target.to(device)

            output = model(data)
            loss = criterion(output, target)

            running_loss += loss.item()

            _, predicted = torch.max(output.data, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(target.cpu().numpy())

    epoch_loss = running_loss / len(dataloader)
    epoch_acc = accuracy_score(all_labels, all_preds)

    return epoch_loss, epoch_acc, all_preds, all_labels


def train_model():
    """Main training function"""
    print("="*70)
    print("GESTURE RECOGNITION TRAINING")
    print("="*70)

    # Load data
    print("\n[1/6] Loading data...")
    X, y = load_and_prepare_data()

    # Create dataloaders
    print("\n[2/6] Creating dataloaders...")
    train_loader, val_loader = create_dataloaders(X, y)

    # Compute class weights
    class_weights = compute_class_weights(y)

    # Create model
    print("\n[3/6] Creating model...")
    model = GestureRecognitionModel().to(config.DEVICE)
    print(f"Total parameters: {count_parameters(model):,}")

    # Loss and optimizer
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(config.DEVICE))
    optimizer = optim.Adam(
        model.parameters(),
        lr=config.LEARNING_RATE,
        weight_decay=config.WEIGHT_DECAY
    )

    # Learning rate scheduler
    scheduler = ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=config.LR_SCHEDULER_FACTOR,
        patience=config.LR_SCHEDULER_PATIENCE,
        min_lr=config.MIN_LR
    )

    # Early stopping
    early_stopping = EarlyStopping(
        patience=config.EARLY_STOPPING_PATIENCE,
        verbose=True
    )

    # Training loop
    print("\n[4/6] Training model...")
    print("="*70)

    model_path = config.MODEL_SAVE_DIR / "gesture_model.pth"
    best_val_acc = 0

    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []

    start_time = time.time()

    for epoch in range(config.NUM_EPOCHS):
        epoch_start = time.time()

        # Train
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, config.DEVICE
        )

        # Validate
        val_loss, val_acc, val_preds, val_labels = validate(
            model, val_loader, criterion, config.DEVICE
        )

        # Update scheduler
        scheduler.step(val_loss)

        # Save metrics
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        train_accs.append(train_acc)
        val_accs.append(val_acc)

        epoch_time = time.time() - epoch_start

        # Print progress
        print(f"Epoch [{epoch+1}/{config.NUM_EPOCHS}] ({epoch_time:.1f}s) | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | "
              f"LR: {optimizer.param_groups[0]['lr']:.6f}")

        # Early stopping
        early_stopping(val_acc, model, model_path)
        if early_stopping.early_stop:
            print("\nEarly stopping triggered!")
            break

        if val_acc > best_val_acc:
            best_val_acc = val_acc

    training_time = time.time() - start_time
    print("="*70)
    print(f"Training completed in {training_time:.1f}s ({training_time/60:.1f}m)")

    # Load best model
    print("\n[5/6] Loading best model...")
    model.load_state_dict(torch.load(model_path))

    # Final evaluation
    print("\n[6/6] Final evaluation...")
    print("="*70)

    # Train set evaluation
    train_loss, train_acc, train_preds, train_labels = validate(
        model, train_loader, criterion, config.DEVICE
    )
    print(f"\nTrain Accuracy: {train_acc*100:.2f}%")

    # Validation set evaluation
    val_loss, val_acc, val_preds, val_labels = validate(
        model, val_loader, criterion, config.DEVICE
    )
    print(f"Val Accuracy: {val_acc*100:.2f}%")

    # Per-class accuracy
    print(f"\nPer-class Accuracy (Validation):")
    for i, gesture in enumerate(config.GESTURES):
        mask = np.array(val_labels) == i
        if np.sum(mask) > 0:
            class_acc = np.mean(np.array(val_preds)[mask] == np.array(val_labels)[mask])
            print(f"  {gesture}: {class_acc*100:.2f}% ({np.sum(mask)} samples)")

    # Confusion matrix
    cm = confusion_matrix(val_labels, val_preds)
    print(f"\nConfusion Matrix (Validation):")
    print(f"           Predicted")
    header = "           " + "  ".join([f"{g:>6s}" for g in config.GESTURES])
    print(header)
    for i, gesture in enumerate(config.GESTURES):
        row = f"Actual {gesture:>5s}  " + "  ".join([f"{cm[i,j]:6d}" for j in range(len(config.GESTURES))])
        print(row)

    # Classification report
    print(f"\nClassification Report (Validation):")
    print(classification_report(
        val_labels, val_preds,
        target_names=config.GESTURES,
        digits=4
    ))

    print("="*70)
    print(f"✓ Model saved to: {model_path}")
    print("="*70)

    # Save training history
    history = {
        'train_losses': train_losses,
        'val_losses': val_losses,
        'train_accs': train_accs,
        'val_accs': val_accs,
    }
    history_path = config.MODEL_SAVE_DIR / "training_history.pth"
    torch.save(history, history_path)
    print(f"✓ Training history saved to: {history_path}")

    return model, history


if __name__ == "__main__":
    model, history = train_model()

    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("1. Run real-time inference:")
    print("   python3 realtime_inference.py")
