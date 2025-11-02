#!/usr/bin/env python3
"""
CNN-BiLSTM Model for Gesture Recognition
Based on Forbes et al. (2020): WiFi-based Human Activity Recognition using Raspberry Pi
"""
import torch
import torch.nn as nn
import config


class GestureRecognitionModel(nn.Module):
    """
    CNN-BiLSTM architecture for WiFi CSI gesture recognition

    Architecture:
        Input: (batch, time_steps, features) = (batch, 128, 100)
        -> Conv1D(64) -> ReLU -> BatchNorm -> MaxPool
        -> Conv1D(128) -> ReLU -> BatchNorm -> MaxPool
        -> Bidirectional LSTM(128)
        -> Dropout(0.3)
        -> Dense(num_classes)
    """

    def __init__(self):
        super(GestureRecognitionModel, self).__init__()

        # Input: (batch, 128, 100)
        # Reshape for Conv1D: (batch, features, time) = (batch, 100, 128)

        # CNN layers
        self.conv1 = nn.Conv1d(
            in_channels=config.INPUT_FEATURES,  # 100
            out_channels=config.CNN_FILTERS[0],  # 64
            kernel_size=config.CNN_KERNEL_SIZE,  # 3
            padding=1
        )
        self.bn1 = nn.BatchNorm1d(config.CNN_FILTERS[0])
        self.pool1 = nn.MaxPool1d(kernel_size=config.CNN_POOL_SIZE)  # 2

        self.conv2 = nn.Conv1d(
            in_channels=config.CNN_FILTERS[0],  # 64
            out_channels=config.CNN_FILTERS[1],  # 128
            kernel_size=config.CNN_KERNEL_SIZE,  # 3
            padding=1
        )
        self.bn2 = nn.BatchNorm1d(config.CNN_FILTERS[1])
        self.pool2 = nn.MaxPool1d(kernel_size=config.CNN_POOL_SIZE)  # 2

        # Calculate LSTM input size after CNN
        # Input: 128 time steps
        # After pool1: 128 // 2 = 64
        # After pool2: 64 // 2 = 32
        lstm_input_size = config.CNN_FILTERS[1]  # 128 (from conv2 output)
        lstm_seq_length = config.INPUT_TIME_STEPS // (config.CNN_POOL_SIZE ** 2)  # 32

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=lstm_input_size,  # 128
            hidden_size=config.LSTM_HIDDEN_SIZE,  # 128
            num_layers=config.LSTM_NUM_LAYERS,  # 1
            batch_first=True,
            bidirectional=config.LSTM_BIDIRECTIONAL,  # True
            dropout=0 if config.LSTM_NUM_LAYERS == 1 else config.DROPOUT_RATE
        )

        # Dropout
        self.dropout = nn.Dropout(config.DROPOUT_RATE)

        # Output layer
        lstm_output_size = config.LSTM_HIDDEN_SIZE * (2 if config.LSTM_BIDIRECTIONAL else 1)
        self.fc = nn.Linear(lstm_output_size, config.NUM_CLASSES)

        self._init_weights()

    def _init_weights(self):
        """Initialize weights"""
        for m in self.modules():
            if isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.LSTM):
                for name, param in m.named_parameters():
                    if 'weight_ih' in name:
                        nn.init.xavier_uniform_(param.data)
                    elif 'weight_hh' in name:
                        nn.init.orthogonal_(param.data)
                    elif 'bias' in name:
                        param.data.fill_(0)

    def forward(self, x):
        """
        Forward pass

        Args:
            x: (batch, time_steps, features) = (batch, 128, 100)

        Returns:
            output: (batch, num_classes)
        """
        # Reshape for Conv1D: (batch, features, time)
        x = x.transpose(1, 2)  # (batch, 100, 128)

        # CNN block 1
        x = self.conv1(x)  # (batch, 64, 128)
        x = torch.relu(x)
        x = self.bn1(x)
        x = self.pool1(x)  # (batch, 64, 64)

        # CNN block 2
        x = self.conv2(x)  # (batch, 128, 64)
        x = torch.relu(x)
        x = self.bn2(x)
        x = self.pool2(x)  # (batch, 128, 32)

        # Reshape for LSTM: (batch, seq_len, features)
        x = x.transpose(1, 2)  # (batch, 32, 128)

        # LSTM
        # lstm_out: (batch, seq_len, hidden_size * num_directions)
        lstm_out, (h_n, c_n) = self.lstm(x)  # (batch, 32, 256)

        # Use last time step output
        x = lstm_out[:, -1, :]  # (batch, 256)

        # Dropout
        x = self.dropout(x)

        # Output layer
        x = self.fc(x)  # (batch, num_classes)

        return x


def count_parameters(model):
    """Count trainable parameters"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Test model
    print("Testing model...")

    model = GestureRecognitionModel()
    print(model)

    print(f"\nTotal trainable parameters: {count_parameters(model):,}")

    # Test forward pass
    batch_size = 4
    x = torch.randn(batch_size, config.INPUT_TIME_STEPS, config.INPUT_FEATURES)
    print(f"\nInput shape: {x.shape}")

    output = model(x)
    print(f"Output shape: {output.shape}")

    # Test with actual batch
    print(f"\nPredictions shape: {output.shape}")
    print(f"Sample predictions: {torch.softmax(output[0], dim=0)}")
