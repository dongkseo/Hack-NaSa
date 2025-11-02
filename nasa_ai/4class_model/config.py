#!/usr/bin/env python3
"""
Configuration for Gesture Recognition System
"""
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.parent  # SHARPax root
PYTHON_CODE_DIR = Path(__file__).parent  # 4class_model directory

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
MODEL_SAVE_DIR = PYTHON_CODE_DIR / "models"
MODEL_SAVE_DIR.mkdir(exist_ok=True)

# CSI receiver path (for real-time inference)
CSI_RECEIVER_PATH = Path(__file__).parent  # Use local csi_receiver.py

# ============================================================================
# DATA PARAMETERS
# ============================================================================
# Gestures to recognize
GESTURES = ['idle', 'wave', 'circle', 'dance']
NUM_CLASSES = len(GESTURES)

# CSI data shape
CSI_FRAMES_PER_FILE = 500
CSI_FRAME_SIZE = 4004  # Complex CSI data
NUM_SUBCARRIERS = 1001  # After reshaping (1001, 2, 2) and averaging
NUM_ANTENNAS = 2
NUM_SPATIAL_STREAMS = 2

# Doppler computation
SAMPLE_LENGTH = 25  # CSI frames per Doppler profile
DOPPLER_SIZE = 100  # FFT size for Doppler
WINDOW_SIZE = 29    # Number of Doppler profiles in one sample (~5초 @ 143Hz)
STRIDE = 8          # Sliding window stride for creating samples

# ============================================================================
# MODEL PARAMETERS
# ============================================================================
# Input shape: (batch, time_steps, features)
INPUT_TIME_STEPS = WINDOW_SIZE  # 128
INPUT_FEATURES = DOPPLER_SIZE   # 100

# CNN parameters
CNN_FILTERS = [64, 128]
CNN_KERNEL_SIZE = 3
CNN_POOL_SIZE = 2

# LSTM parameters
LSTM_HIDDEN_SIZE = 128
LSTM_NUM_LAYERS = 1
LSTM_BIDIRECTIONAL = True

# Regularization
DROPOUT_RATE = 0.3

# ============================================================================
# TRAINING PARAMETERS
# ============================================================================
# Data split
TRAIN_SPLIT = 0.8
VAL_SPLIT = 0.2
RANDOM_SEED = 42

# Training hyperparameters
BATCH_SIZE = 32
NUM_EPOCHS = 50
LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-5

# Optimization
EARLY_STOPPING_PATIENCE = 10
LR_SCHEDULER_PATIENCE = 5
LR_SCHEDULER_FACTOR = 0.5
MIN_LR = 1e-6

# Data augmentation
USE_AUGMENTATION = True
NOISE_STD = 0.01
SCALE_RANGE = (0.9, 1.1)

# ============================================================================
# REAL-TIME INFERENCE PARAMETERS
# ============================================================================
CSI_FILE_PATTERN = "/home/dongkseo/rx_realtime*.csi"
REALTIME_UPDATE_INTERVAL = 200  # ms for plot update
PREDICTION_STRIDE = 6   # Predict every N new Doppler profiles (~1초마다, 5초 윈도우 오버랩)

# Stability improvements
CONFIDENCE_THRESHOLD = 0.80  # Minimum confidence to accept prediction (80%)
SMOOTHING_WINDOW = 5         # Number of recent predictions for majority voting

# Visualization
CONFIDENCE_HISTORY_LENGTH = 50
GESTURE_COLORS = ['#95E1D3', '#FF6B6B', '#FFD93D', '#A8E6CF']  # idle, wave, circle, dance
GESTURE_EMOJIS = ['🤫', '👋', '⭕', '💃']

# ============================================================================
# DEVICE
# ============================================================================
import torch
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print(f"Configuration loaded:")
print(f"  Data directory: {DATA_DIR}")
print(f"  Gestures: {GESTURES}")
print(f"  Device: {DEVICE}")
print(f"  Model save directory: {MODEL_SAVE_DIR}")
