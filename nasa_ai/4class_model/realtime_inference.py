#!/usr/bin/env python3
"""
Real-time Gesture Recognition Inference
Uses trained model for real-time CSI gesture recognition
"""
import sys
import time
import numpy as np
import torch
from collections import deque, Counter
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import config

# Import Widar's CSI receiver
sys.path.insert(0, str(config.CSI_RECEIVER_PATH))
from csi_receiver import CSIReceiver, CSIBuffer
from data_loader import DopplerExtractor
from model import GestureRecognitionModel


class RealtimeGestureRecognizer:
    """Real-time gesture recognition using trained model"""

    def __init__(self, model_path, csi_file_pattern):
        print(f"Loading model from: {model_path}")

        # Load model
        self.model = GestureRecognitionModel().to(config.DEVICE)
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()
        print(f"  Model loaded successfully")
        print(f"  Gestures: {', '.join([f'{e} {g}' for e, g in zip(config.GESTURE_EMOJIS, config.GESTURES)])}")

        # CSI receiver
        self.receiver = CSIReceiver(csi_file_pattern)
        self.buffer = CSIBuffer(max_frames=1000)

        # Doppler extractor
        self.doppler_extractor = DopplerExtractor()

        # Doppler buffer (sliding window)
        self.doppler_buffer = deque(maxlen=config.WINDOW_SIZE)

        # Frame counter for non-overlapping Doppler calculation
        self.frame_counter = 0

        # Prediction stride
        self.prediction_stride = config.PREDICTION_STRIDE
        self.frames_since_last_prediction = 0

        # Temporal smoothing
        self.raw_prediction_history = deque(maxlen=config.SMOOTHING_WINDOW)

        # Statistics
        self.total_predictions = 0
        self.gesture_counts = {name: 0 for name in config.GESTURES}
        self.prediction_history = deque(maxlen=config.CONFIDENCE_HISTORY_LENGTH)
        self.confidence_history = {i: deque(maxlen=config.CONFIDENCE_HISTORY_LENGTH)
                                  for i in range(config.NUM_CLASSES)}

        self.setup_plot()

    def predict_gesture(self):
        """Run inference on current Doppler buffer"""
        if len(self.doppler_buffer) < config.WINDOW_SIZE:
            return None, None

        # Stack Doppler profiles
        doppler_array = np.array(list(self.doppler_buffer))  # (128, 100)

        # Convert to tensor and add batch dimension
        x = torch.FloatTensor(doppler_array).unsqueeze(0).to(config.DEVICE)  # (1, 128, 100)

        # Run inference
        with torch.no_grad():
            output = self.model(x)
            probabilities = torch.softmax(output, dim=1)
            confidences = probabilities.cpu().numpy()[0]
            predicted_class = np.argmax(confidences)

        return predicted_class, confidences

    def setup_plot(self):
        """Setup visualization"""
        self.fig = plt.figure(figsize=(16, 9))

        # Doppler spectrogram
        self.ax_doppler = plt.subplot2grid((3, 3), (0, 0), colspan=2, rowspan=2)
        self.doppler_img = None
        self.ax_doppler.set_xlabel('Time Window')
        self.ax_doppler.set_ylabel('Doppler Frequency Bin')
        self.ax_doppler.set_title('Doppler Spectrogram')

        # Prediction bar chart
        self.ax_pred = plt.subplot2grid((3, 3), (0, 2), rowspan=1)
        self.bars = self.ax_pred.barh(config.GESTURES, [0]*config.NUM_CLASSES,
                                     color=config.GESTURE_COLORS)
        self.ax_pred.set_xlim(0, 1)
        self.ax_pred.set_xlabel('Confidence')
        self.ax_pred.set_title('Current Prediction (BINARY)')
        self.ax_pred.grid(True, alpha=0.3, axis='x')

        # Confidence history
        self.ax_history = plt.subplot2grid((3, 3), (1, 2), rowspan=1)
        self.history_lines = []
        for i, (name, color) in enumerate(zip(config.GESTURES, config.GESTURE_COLORS)):
            line, = self.ax_history.plot([], [], label=name, color=color, linewidth=2)
            self.history_lines.append(line)
        self.ax_history.set_xlim(0, config.CONFIDENCE_HISTORY_LENGTH)
        self.ax_history.set_ylim(0, 1)
        self.ax_history.set_xlabel('Time')
        self.ax_history.set_ylabel('Confidence')
        self.ax_history.set_title('Confidence History')
        self.ax_history.legend(loc='upper left', fontsize=8)
        self.ax_history.grid(True, alpha=0.3)

        # Statistics panel
        self.ax_stats = plt.subplot2grid((3, 3), (2, 0), colspan=3)
        self.ax_stats.axis('off')
        self.stats_text = self.ax_stats.text(
            0.5, 0.5, '', ha='center', va='center', fontsize=12, family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9)
        )

        plt.tight_layout()

    def update_plot(self, frame):
        """Update visualization"""
        # Get new CSI frames
        new_frames = self.receiver.get_new_frames()

        new_doppler_count = 0
        for csi_frame in new_frames:
            self.buffer.add_frame(csi_frame)
            self.frame_counter += 1

            # Compute Doppler profile ONLY every SAMPLE_LENGTH frames (non-overlapping)
            # This matches how training data was created
            if len(self.buffer) >= config.SAMPLE_LENGTH and self.frame_counter % config.SAMPLE_LENGTH == 0:
                recent_frames = list(self.buffer.buffer)[-config.SAMPLE_LENGTH:]
                doppler = self.doppler_extractor.compute_doppler_profile(recent_frames)
                if doppler is not None:
                    self.doppler_buffer.append(doppler)
                    new_doppler_count += 1

        # Update Doppler spectrogram
        if len(self.doppler_buffer) > 0:
            doppler_array = np.array(list(self.doppler_buffer)).T

            if self.doppler_img is None:
                self.doppler_img = self.ax_doppler.imshow(
                    doppler_array, aspect='auto', cmap='jet',
                    origin='lower', interpolation='nearest'
                )
                plt.colorbar(self.doppler_img, ax=self.ax_doppler, label='Power')
            else:
                self.doppler_img.set_data(doppler_array)
                self.doppler_img.set_extent([0, doppler_array.shape[1], 0, 100])

        # Run prediction with stride
        self.frames_since_last_prediction += new_doppler_count

        predicted_class = None
        confidences = None

        if self.frames_since_last_prediction >= self.prediction_stride:
            raw_predicted_class, confidences = self.predict_gesture()
            if raw_predicted_class is not None:
                self.frames_since_last_prediction = 0

                # Apply confidence threshold
                max_confidence = np.max(confidences)
                if max_confidence >= config.CONFIDENCE_THRESHOLD:
                    # Add to raw prediction history for smoothing
                    self.raw_prediction_history.append(raw_predicted_class)

                    # Apply temporal smoothing (majority voting)
                    if len(self.raw_prediction_history) >= config.SMOOTHING_WINDOW:
                        predicted_class = Counter(self.raw_prediction_history).most_common(1)[0][0]
                    else:
                        # Not enough history yet, use raw prediction
                        predicted_class = raw_predicted_class

        if predicted_class is not None:
            self.total_predictions += 1
            self.prediction_history.append(predicted_class)
            self.gesture_counts[config.GESTURES[predicted_class]] += 1

            # Update confidence histories
            for i in range(config.NUM_CLASSES):
                self.confidence_history[i].append(confidences[i])

            # Update prediction bars
            for bar, conf in zip(self.bars, confidences):
                bar.set_width(conf)

            # Highlight predicted gesture
            current_gesture = config.GESTURES[predicted_class]
            max_conf = confidences[predicted_class]
            self.ax_pred.set_title(
                f'Prediction: {config.GESTURE_EMOJIS[predicted_class]} {current_gesture} '
                f'({max_conf:.2%}) [Smoothed]',
                fontweight='bold', fontsize=11
            )

        # Update history plot
        for i, line in enumerate(self.history_lines):
            if len(self.confidence_history[i]) > 0:
                line.set_data(range(len(self.confidence_history[i])),
                            list(self.confidence_history[i]))

        # Update statistics
        stats_text = f"""
╔═══════════════════════════════════════════════════════════════╗
║       BINARY GESTURE RECOGNITION - REAL-TIME                  ║
║       PyTorch CNN-BiLSTM Model                                ║
╚═══════════════════════════════════════════════════════════════╝

📊 Statistics:
   Total Predictions: {self.total_predictions}
   CSI Frames: {len(self.buffer)}
   Doppler Windows: {len(self.doppler_buffer)}/{config.WINDOW_SIZE}

🎯 Gesture Distribution:
"""
        for i, gesture in enumerate(config.GESTURES):
            count = self.gesture_counts[gesture]
            pct = (count / self.total_predictions * 100) if self.total_predictions > 0 else 0
            stats_text += f"   {config.GESTURE_EMOJIS[i]} {gesture:10s}: {count:5d} ({pct:5.1f}%)\n"

        if predicted_class is not None:
            stats_text += f"\n🔴 CURRENT: {config.GESTURE_EMOJIS[predicted_class]} {config.GESTURES[predicted_class].upper()}"

        self.stats_text.set_text(stats_text)

    def run(self):
        """Start real-time recognition"""
        print("\n" + "="*70)
        print("  Binary Gesture Recognition - Real-time")
        print("  PyTorch CNN-BiLSTM Model")
        print("="*70)
        print(f"\nGestures: {', '.join([f'{e} {n}' for e, n in zip(config.GESTURE_EMOJIS, config.GESTURES)])}")
        print(f"Device: {config.DEVICE}")
        print("\nStarting recognition...")
        print("="*70 + "\n")

        self.receiver.start()

        anim = FuncAnimation(self.fig, self.update_plot,
                           interval=config.REALTIME_UPDATE_INTERVAL,
                           blit=False, cache_frame_data=False)

        try:
            plt.show()
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            self.receiver.close()

            print("\n" + "="*70)
            print("SESSION SUMMARY")
            print("="*70)
            print(f"Total predictions: {self.total_predictions}")
            for i, gesture in enumerate(config.GESTURES):
                count = self.gesture_counts[gesture]
                pct = (count / self.total_predictions * 100) if self.total_predictions > 0 else 0
                print(f"{config.GESTURE_EMOJIS[i]} {gesture}: {count} ({pct:.1f}%)")
            print("="*70)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Real-time Binary Gesture Recognition')
    parser.add_argument('--model', default='models/gesture_model.pth',
                       help='Path to trained model')
    parser.add_argument('--csi-file', default=config.CSI_FILE_PATTERN,
                       help='CSI file pattern')

    args = parser.parse_args()

    model_path = config.PYTHON_CODE_DIR / args.model
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        print("Please train the model first by running: python3 train.py")
        return

    recognizer = RealtimeGestureRecognizer(model_path, args.csi_file)
    recognizer.run()


if __name__ == "__main__":
    main()
