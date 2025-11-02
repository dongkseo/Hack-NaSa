#!/usr/bin/env python3
"""
Real-time CSI Visualizer with VERBOSE Data Collection Monitoring
Shows detailed statistics and monitoring information
"""
import sys
import time
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
from datetime import datetime
from pathlib import Path
from collections import deque

sys.path.insert(0, '..')
from csi_receiver import CSIReceiver, CSIBuffer


class CSIVisualizerVerbose:
    """Real-time CSI visualization with VERBOSE monitoring"""

    def __init__(self, csi_file_pattern, save_dir='collected_data'):
        self.receiver = CSIReceiver(csi_file_pattern)
        self.buffer = CSIBuffer(max_frames=600)

        # Data collection
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self.is_recording = False
        self.is_waiting = False  # Waiting period before recording starts
        self.current_label = None
        self.recording_buffer = []
        self.recording_start_time = None
        self.waiting_start_time = None
        self.wait_duration = 5.0  # Wait 5 seconds before recording
        self.auto_stop_duration = 10.0  # Auto-stop after 10 seconds

        # Statistics tracking
        self.frame_timestamps = deque(maxlen=100)
        self.motion_stats = {'min': float('inf'), 'max': 0, 'mean': 0}
        self.motion_baseline = None
        self.total_frames_received = 0
        self.total_samples_saved = 0
        self.samples_per_gesture = {g: 0 for g in ['wave', 'swirl', 'flap', 'idle']}

        # No warmup - ready immediately
        self.warmup_complete = True  # Always ready

        # CSI statistics
        self.csi_amp_history = deque(maxlen=100)
        self.csi_phase_history = deque(maxlen=100)

        # Visualization parameters
        self.display_frames = 500
        self.num_subcarriers = 114  # Default, will be updated from first frame if different
        self.heatmap_data = np.zeros((self.num_subcarriers, self.display_frames))
        self.motion_history = []
        self.max_motion_history = 200

        # Setup plot
        self.setup_plot()
        self.start_time = time.time()

    def setup_plot(self):
        """Setup matplotlib figure with detailed monitoring panels"""
        self.fig = plt.figure(figsize=(18, 10))

        # Main heatmap (left side, larger)
        self.ax_heatmap = plt.subplot2grid((6, 6), (0, 0), colspan=4, rowspan=3)
        self.heatmap_img = self.ax_heatmap.imshow(
            self.heatmap_data,
            aspect='auto',
            cmap='jet',
            vmin=0,
            vmax=100,
            interpolation='nearest'
        )
        self.ax_heatmap.set_xlabel('Time (frames)')
        self.ax_heatmap.set_ylabel('Subcarrier Index')
        self.ax_heatmap.set_title('CSI Amplitude Heatmap')
        plt.colorbar(self.heatmap_img, ax=self.ax_heatmap, label='Amplitude')

        # Motion level graph
        self.ax_motion = plt.subplot2grid((6, 6), (3, 0), colspan=4, rowspan=1)
        self.motion_line, = self.ax_motion.plot([], [], 'b-', linewidth=2, label='Motion')
        self.baseline_line = self.ax_motion.axhline(y=0, color='g', linestyle='--', alpha=0.5, label='Baseline')
        self.ax_motion.set_xlim(0, self.max_motion_history)
        self.ax_motion.set_ylim(0, 400)
        self.ax_motion.set_xlabel('Time (samples)')
        self.ax_motion.set_ylabel('Motion Level')
        self.ax_motion.set_title('Motion Detection')
        self.ax_motion.legend(loc='upper right')
        self.ax_motion.grid(True, alpha=0.3)

        # Statistics panel (right side)
        self.ax_stats = plt.subplot2grid((6, 6), (0, 4), colspan=2, rowspan=3)
        self.ax_stats.axis('off')
        self.stats_text = self.ax_stats.text(
            0.05, 0.95, '',
            ha='left', va='top',
            fontsize=9,
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9)
        )

        # Collection summary (right side bottom)
        self.ax_collection = plt.subplot2grid((6, 6), (3, 4), colspan=2, rowspan=1)
        self.ax_collection.axis('off')
        self.collection_text = self.ax_collection.text(
            0.05, 0.95, '',
            ha='left', va='top',
            fontsize=9,
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9)
        )

        # CSI Statistics (bottom left)
        self.ax_csi_stats = plt.subplot2grid((6, 6), (4, 0), colspan=2, rowspan=1)
        self.ax_csi_stats.axis('off')
        self.csi_stats_text = self.ax_csi_stats.text(
            0.05, 0.95, '',
            ha='left', va='top',
            fontsize=9,
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.9)
        )

        # Status bar
        self.ax_status = plt.subplot2grid((6, 6), (4, 2), colspan=4, rowspan=1)
        self.ax_status.axis('off')
        self.status_text = self.ax_status.text(
            0.5, 0.5, 'Status: Waiting for CSI data...',
            ha='center', va='center',
            fontsize=12,
            bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8)
        )

        # Recording buttons - simplified gestures
        button_y = 0.02
        button_height = 0.05
        button_width = 0.15
        button_spacing = 0.03
        start_x = 0.1

        gestures = ['wave', 'swirl', 'flap', 'idle']  # wave, swirl, flap, idle
        gesture_labels = {
            'wave': 'WAVE\n(Hand Wave)',
            'swirl': 'SWIRL\n(Circle)',
            'flap': 'FLAP\n(Up/Down)',
            'idle': 'IDLE\n(Still)'
        }
        self.buttons = {}
        self.button_axes = {}

        for i, gesture in enumerate(gestures):
            ax_button = plt.axes([start_x + i * (button_width + button_spacing), button_y, button_width, button_height])
            button = Button(ax_button, gesture_labels[gesture], color='lightgray', hovercolor='0.95')
            button.on_clicked(lambda event, g=gesture: self.toggle_recording(g))
            self.buttons[gesture] = button
            self.button_axes[gesture] = ax_button

        plt.tight_layout()

    def toggle_recording(self, label):
        """Start recording (auto-stops after duration)"""
        if self.is_recording or self.is_waiting:
            # Already recording or waiting, ignore
            print(f"⚠️  Already in progress, please wait...")
            return
        else:
            self.start_waiting(label)

    def start_waiting(self, label):
        """Start 10-second waiting period before recording (all gestures)"""
        self.is_waiting = True
        self.current_label = label
        self.waiting_start_time = time.time()

        # All gestures get 10 seconds to prepare
        self.wait_duration = 10

        # Change button color to YELLOW during waiting
        self.button_axes[label].set_facecolor('yellow')
        self.buttons[label].color = 'yellow'
        self.buttons[label].hovercolor = 'gold'
        self.fig.canvas.draw_idle()

        print("\n" + "="*70)
        print(f"⏳ WAITING: {label.upper()} - Get ready! Recording starts in {self.wait_duration} seconds...")
        print("="*70)
        self.update_status(f"⏳ Get ready! Recording starts in {self.wait_duration}s...")

    def start_recording(self, label):
        """Start recording CSI data with label"""
        self.is_waiting = False
        self.is_recording = True
        self.recording_buffer = []
        self.recording_start_time = time.time()

        # Change button color to RED when recording
        self.button_axes[label].set_facecolor('red')
        self.buttons[label].color = 'red'
        self.buttons[label].hovercolor = 'darkred'
        self.fig.canvas.draw_idle()

        print("\n" + "="*70)
        print(f"🔴 RECORDING STARTED: {label.upper()}")
        print("="*70)
        self.update_status(f"🔴 RECORDING: {label.upper()}")

    def stop_recording(self):
        """Stop recording and save data"""
        if not self.is_recording:
            return

        # Reset button color back to gray
        self.button_axes[self.current_label].set_facecolor('lightgray')
        self.buttons[self.current_label].color = 'lightgray'
        self.buttons[self.current_label].hovercolor = '0.95'
        self.fig.canvas.draw_idle()

        duration = time.time() - self.recording_start_time
        num_frames = len(self.recording_buffer)

        print("\n" + "="*70)
        print(f"⏹️  RECORDING STOPPED: {self.current_label.upper()}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Frames collected: {num_frames}")
        print(f"   Frame rate: {num_frames/duration:.1f} fps")

        if num_frames < 50:  # Lowered from 100 for low frame rate environments
            print(f"⚠️  WARNING: Too few frames ({num_frames}), discarding...")
            print("="*70)
            self.update_status(f"⚠️  Recording discarded (only {num_frames} frames)")
        else:
            # Calculate statistics
            data_array = np.array(self.recording_buffer)
            mean_amp = np.abs(data_array).mean()
            std_amp = np.abs(data_array).std()

            # Save data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.save_dir / f"{self.current_label}_{timestamp}_{num_frames}frames.npy"
            np.save(filename, data_array)

            self.total_samples_saved += 1
            self.samples_per_gesture[self.current_label] += 1

            print(f"✅ SAVED: {filename.name}")
            print(f"   Shape: {data_array.shape}")
            print(f"   Mean amplitude: {mean_amp:.2f}")
            print(f"   Std amplitude: {std_amp:.2f}")
            print(f"   File size: {filename.stat().st_size / 1024:.1f} KB")
            print("="*70)

            self.update_status(f"✅ Saved: {filename.name}")

        self.is_recording = False
        self.current_label = None
        self.recording_buffer = []

    def update_status(self, text):
        """Update status text"""
        self.status_text.set_text(text)

    def update_statistics(self):
        """Update all statistics panels"""
        # Runtime
        runtime = time.time() - self.start_time

        # Frame rate calculation
        if len(self.frame_timestamps) > 1:
            time_diffs = np.diff(list(self.frame_timestamps))
            avg_interval = np.mean(time_diffs)
            fps = 1.0 / avg_interval if avg_interval > 0 else 0
        else:
            fps = 0

        # Motion statistics
        if len(self.motion_history) > 10:
            recent_motion = self.motion_history[-100:]
            motion_min = min(recent_motion)
            motion_max = max(recent_motion)
            motion_mean = np.mean(recent_motion)
            motion_std = np.std(recent_motion)

            # Calculate baseline (10th percentile)
            if self.motion_baseline is None and len(recent_motion) > 50:
                self.motion_baseline = np.percentile(recent_motion, 10)
                self.baseline_line.set_ydata([self.motion_baseline])
        else:
            motion_min = motion_max = motion_mean = motion_std = 0

        # Main statistics panel
        stats_str = f"""╔══════════════════════════════╗
║      SYSTEM STATISTICS       ║
╚══════════════════════════════╝

⏱️  Runtime: {runtime:.1f}s

📊 Buffer & Frames:
   Total received: {self.total_frames_received}
   Buffer size: {len(self.buffer)}/{self.buffer.max_frames}
   Display frames: {self.display_frames}
   Frame rate: {fps:.1f} fps

📈 Motion Statistics:
   Current: {self.motion_history[-1] if self.motion_history else 0:.1f}
   Baseline: {self.motion_baseline if self.motion_baseline else 0:.1f}
   Min: {motion_min:.1f}
   Max: {motion_max:.1f}
   Mean: {motion_mean:.1f}
   Std: {motion_std:.1f}
"""
        self.stats_text.set_text(stats_str)

        # Collection summary panel
        total_collected = sum(self.samples_per_gesture.values())
        collection_str = f"""╔══════════════════════════════╗
║   COLLECTION SUMMARY         ║
╚══════════════════════════════╝

💾 Total: {total_collected} samples

📝 Gestures:
   WAVE (Hand Wave): {self.samples_per_gesture['wave']:2d}
   SWIRL (Circle):   {self.samples_per_gesture['swirl']:2d}
   FLAP (Up/Down):   {self.samples_per_gesture['flap']:2d}
   IDLE (Still):     {self.samples_per_gesture['idle']:2d}

🎯 Target: 10-15 each

📁 Save: {str(self.save_dir)[-22:]}
"""
        self.collection_text.set_text(collection_str)

        # CSI statistics panel
        if len(self.csi_amp_history) > 0:
            recent_amp = list(self.csi_amp_history)[-50:]
            amp_mean = np.mean(recent_amp)
            amp_std = np.std(recent_amp)
            amp_min = np.min(recent_amp)
            amp_max = np.max(recent_amp)
        else:
            amp_mean = amp_std = amp_min = amp_max = 0

        csi_stats_str = f"""╔═══════════════════════╗
║   CSI STATISTICS      ║
╚═══════════════════════╝

🌊 Amplitude:
   Mean: {amp_mean:.2f}
   Std:  {amp_std:.2f}
   Min:  {amp_min:.2f}
   Max:  {amp_max:.2f}

📡 Subcarriers: {self.num_subcarriers}
"""
        self.csi_stats_text.set_text(csi_stats_str)

    def update(self, frame):
        """Animation update function"""
        current_time = time.time()

        # Check for waiting period completion
        if self.is_waiting:
            elapsed = current_time - self.waiting_start_time
            if elapsed >= self.wait_duration:
                # Waiting complete, start recording
                self.start_recording(self.current_label)

        # Check for auto-stop
        if self.is_recording:
            elapsed = current_time - self.recording_start_time
            if elapsed >= self.auto_stop_duration:
                self.stop_recording()

        # Get new frames
        new_frames = self.receiver.get_new_frames()

        if len(new_frames) > 0:
            self.total_frames_received += len(new_frames)
            self.frame_timestamps.append(current_time)

            # Only print every 10 batches to reduce console spam
            if self.total_frames_received % 50 == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Buffer: {len(self.buffer)} frames")

        for csi_frame in new_frames:
            self.buffer.add_frame(csi_frame)

            # Track CSI statistics
            amp = np.abs(csi_frame).mean()
            self.csi_amp_history.append(amp)

            # If recording, add to recording buffer
            if self.is_recording:
                self.recording_buffer.append(csi_frame)

        # Update heatmap (avoid full copy with list())
        if len(self.buffer) > 0:
            # Direct slice from deque - no full copy
            buffer_len = len(self.buffer.buffer)
            start_idx = max(0, buffer_len - self.display_frames)

            if buffer_len > 0:
                heatmap_frames = []

                # First pass: detect the most common frame size
                frame_sizes = []
                for i in range(start_idx, buffer_len):
                    frame = self.buffer.buffer[i]
                    frame_size = len(frame)
                    if frame_size % 4 == 0:
                        frame_sizes.append(frame_size)

                if len(frame_sizes) > 0:
                    # Use the most common frame size
                    from collections import Counter
                    most_common_size = Counter(frame_sizes).most_common(1)[0][0]
                    expected_subcarriers = most_common_size // 4

                    # Update if different from current
                    if expected_subcarriers != self.num_subcarriers:
                        self.num_subcarriers = expected_subcarriers
                        self.heatmap_data = np.zeros((self.num_subcarriers, self.display_frames))
                        print(f"Auto-detected {self.num_subcarriers} subcarriers (frame size: {most_common_size})")

                    # Second pass: only process frames matching the expected size
                    expected_size = self.num_subcarriers * 4
                    for i in range(start_idx, buffer_len):
                        frame = self.buffer.buffer[i]

                        # Only process frames with correct size
                        if len(frame) != expected_size:
                            continue

                        try:
                            reshaped = frame.reshape(self.num_subcarriers, 2, 2)
                            amp = np.abs(reshaped).mean(axis=(1, 2))
                            heatmap_frames.append(amp)
                        except ValueError:
                            # Skip frames that can't be reshaped
                            continue

                if len(heatmap_frames) > 0:
                    heatmap_array = np.array(heatmap_frames).T

                    if heatmap_array.shape[1] < self.display_frames:
                        padding = np.zeros((self.num_subcarriers, self.display_frames - heatmap_array.shape[1]))
                        heatmap_array = np.concatenate([padding, heatmap_array], axis=1)
                    else:
                        heatmap_array = heatmap_array[:, -self.display_frames:]

                    self.heatmap_data = heatmap_array
                    self.heatmap_img.set_data(self.heatmap_data)

                    # Auto-scale colorbar
                    vmin, vmax = self.heatmap_data.min(), self.heatmap_data.max()
                    self.heatmap_img.set_clim(vmin=vmin, vmax=vmax)

        # Update motion level
        motion = self.buffer.get_motion_level()
        self.motion_history.append(motion)
        if len(self.motion_history) > self.max_motion_history:
            self.motion_history.pop(0)

        if len(self.motion_history) > 0:
            self.motion_line.set_data(range(len(self.motion_history)), self.motion_history)
            self.ax_motion.set_xlim(0, max(self.max_motion_history, len(self.motion_history)))

            # Auto-scale Y axis
            if len(self.motion_history) > 10:
                ymax = max(400, max(self.motion_history[-100:]) * 1.2)
                self.ax_motion.set_ylim(0, ymax)

        # Update statistics
        self.update_statistics()

        # Update title
        buffer_size = len(self.buffer)
        baseline = self.motion_baseline if self.motion_baseline else 0
        motion_delta = motion - baseline

        title = f"CSI Heatmap | Frames: {buffer_size} | Motion: {motion:.1f} (Δ{motion_delta:+.1f})"

        if self.is_recording:
            recording_duration = time.time() - self.recording_start_time
            remaining = self.auto_stop_duration - recording_duration
            title += f" | 🔴 REC {self.current_label.upper()}: {remaining:.1f}s left ({len(self.recording_buffer)} frames)"

        self.ax_heatmap.set_title(title, fontweight='bold')

        # No need to return anything when blit=False
        # This allows all artists (including text) to update

    def run(self):
        """Start visualization"""
        print("=" * 80)
        print("  CSI VERBOSE VISUALIZER & DATA COLLECTOR")
        print("=" * 80)
        print()
        print("📊 MONITORING FEATURES:")
        print("  • Real-time CSI heatmap")
        print("  • Motion level tracking with baseline detection")
        print("  • Frame rate and buffer statistics")
        print("  • Collection summary per gesture")
        print("  • Detailed CSI amplitude/phase statistics")
        print()
        print("🎮 AUTO-RECORDING MODE (3-MINUTE LONG RECORDINGS):")
        print(f"  1. Click gesture button (WAVE, SWIRL, FLAP, or IDLE)")
        print(f"  2. Wait 10 seconds (button turns YELLOW)")
        print(f"  3. Perform gesture continuously for 3 minutes (button turns RED)")
        print(f"  4. Recording AUTO-STOPS after {self.auto_stop_duration:.0f} seconds")
        print("  5. Repeat 3 times per gesture (will be split into ~176 samples each)")
        print()
        print(f"💾 Data directory: {self.save_dir.absolute()}")
        print()
        print("Press Ctrl+C or close window to exit")
        print("=" * 80)
        print()

        # Start receiver
        self.receiver.start()

        # Start animation (blit=False for text updates)
        anim = FuncAnimation(
            self.fig,
            self.update,
            interval=50,  # Update every 50ms (20 FPS)
            blit=False,
            cache_frame_data=False
        )

        try:
            plt.show()
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            if self.is_recording:
                print("\nStopping ongoing recording...")
                self.stop_recording()

            self.receiver.close()

            # Final summary
            print("\n" + "=" * 80)
            print("📊 FINAL SUMMARY")
            print("=" * 80)
            print(f"Total runtime: {time.time() - self.start_time:.1f}s")
            print(f"Total frames received: {self.total_frames_received}")
            print(f"Total samples saved: {self.total_samples_saved}")
            print()
            print("Samples per gesture:")
            for gesture, count in self.samples_per_gesture.items():
                print(f"  {gesture.upper():8s}: {count:2d}")
            print("=" * 80)
            print("Goodbye!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Verbose CSI Visualizer & Data Collector')
    parser.add_argument('--csi-file', default='/home/dongkseo/rx_realtime*.csi',
                        help='CSI file pattern to monitor')
    parser.add_argument('--save-dir', default='collected_data',
                        help='Directory to save collected data')

    args = parser.parse_args()

    visualizer = CSIVisualizerVerbose(args.csi_file, args.save_dir)
    visualizer.run()


if __name__ == "__main__":
    main()
