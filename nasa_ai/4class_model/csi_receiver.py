#!/usr/bin/env python3
"""
CSI Receiver Module
Reads CSI data from PicoScenes file in real-time with incremental reading
"""
import sys
import numpy as np
import time
import glob
import struct
import os
from collections import deque

sys.path.insert(0, '/home/dongkseo/SHARPax/PicoScenes-Python-Toolbox')
from picoscenes import Picoscenes


class CSIReceiver:
    """
    Reads CSI data from PicoScenes .csi file in real-time
    Uses incremental reading (tail -f style) to avoid re-parsing entire file
    """
    def __init__(self, csi_file_pattern):
        self.csi_file_pattern = csi_file_pattern
        self.csi_file = None
        self.file_position = 0  # Last read position in file
        self.temp_ps_file = "/tmp/picoscenes_incremental.csi"
        self.skipped_frames = {'mimo': 0, 'size': 0, 'parse_error': 0}
        self.warned_mimo = False
        self.frame_count = 0

    def find_latest_file(self):
        """Find the latest CSI file matching pattern"""
        files = glob.glob(self.csi_file_pattern)
        if not files:
            return None
        return max(files, key=lambda f: f)

    def start(self, skip_existing=True):
        """
        Initialize receiver
        Args:
            skip_existing: If True, skip existing data and only read new data
        """
        print(f"CSI Receiver monitoring files: {self.csi_file_pattern}")

        if skip_existing:
            # Move to end of existing file to skip old data
            csi_file = self.find_latest_file()
            if csi_file and os.path.exists(csi_file):
                self.csi_file = csi_file
                self.file_position = os.path.getsize(csi_file)
                print(f"  → Skipping existing data, starting from position: {self.file_position} bytes")
            else:
                print(f"  → No existing file, will start fresh")

    def get_new_frames(self):
        """
        Parse CSI file incrementally and return only new frames
        Returns: list of CSI arrays or empty list
        """
        try:
            # Find latest file
            csi_file = self.find_latest_file()
            if csi_file is None:
                return []

            # If file changed, reset position
            if self.csi_file != csi_file:
                self.csi_file = csi_file
                self.file_position = 0
                print(f"  → Monitoring file: {csi_file}")

            # Get current file size
            file_size = os.path.getsize(csi_file)

            # No new data
            if file_size <= self.file_position:
                return []

            # Read only new bytes from file
            with open(csi_file, 'rb') as f:
                f.seek(self.file_position)
                new_data = f.read(file_size - self.file_position)

            # If we got new data, write to temp file and parse
            if not new_data:
                return []

            # Write new data to temporary file for parsing
            with open(self.temp_ps_file, 'wb') as f:
                f.write(new_data)

            # Parse using PicoScenes toolbox
            try:
                ps = Picoscenes(self.temp_ps_file, if_report=False)
                ps.read()
            except Exception as e:
                # Incomplete frame at end - wait for next iteration
                return []

            # Update file position
            self.file_position = file_size

            # Extract CSI from parsed frames
            new_frames = []
            for frame in ps.raw:
                if 'CSI' in frame:
                    csi_info = frame['CSI']
                    csi_raw = csi_info.get('CSI', [])
                    num_tones = csi_info.get('numTones', 0)
                    num_tx = csi_info.get('numTx', 0)
                    num_rx = csi_info.get('numRx', 0)

                    if isinstance(csi_raw, list) and len(csi_raw) > 0:
                        csi_array = np.array(csi_raw)

                        # Check if we have 2x2 MIMO AND 80MHz bandwidth (1001 tones)
                        if num_tx == 2 and num_rx == 2 and num_tones == 1001:
                            # Reshape to (num_tones, num_tx, num_rx)
                            expected_size = num_tones * num_tx * num_rx
                            if csi_array.shape[0] == expected_size:
                                csi_reshaped = csi_array.reshape(num_tones, num_tx, num_rx)

                                # Use all available subcarriers for 80MHz (1001 tones)
                                csi_flattened = csi_reshaped.flatten()  # 1001*2*2=4004 for 80MHz
                                new_frames.append(csi_flattened)
                                self.frame_count += 1
                            else:
                                # Skip frames with mismatched size
                                self.skipped_frames['size'] += 1
                        else:
                            # Skip non-2x2 MIMO or non-80MHz frames (silently count)
                            if num_tx != 2 or num_rx != 2:
                                self.skipped_frames['mimo'] += 1
                            else:
                                self.skipped_frames['size'] += 1
                            if not self.warned_mimo:
                                print(f"Note: Only accepting 2x2 MIMO @ 80MHz (1001 tones)")
                                self.warned_mimo = True

            return new_frames

        except Exception as e:
            self.skipped_frames['parse_error'] += 1
            return []

    def close(self):
        """Close receiver and cleanup"""
        if os.path.exists(self.temp_ps_file):
            os.remove(self.temp_ps_file)
        print(f"CSI Receiver closed (processed {self.frame_count} frames)")
        print(f"  Skipped: MIMO={self.skipped_frames['mimo']}, Size={self.skipped_frames['size']}, Parse errors={self.skipped_frames['parse_error']}")


class CSIBuffer:
    """
    Circular buffer to store CSI frames for sliding window processing
    """
    def __init__(self, max_frames=400):
        self.max_frames = max_frames
        self.buffer = deque(maxlen=max_frames)
        self.last_frame = None
        self.expected_size = None

    def add_frame(self, csi_frame):
        """Add a CSI frame to buffer"""
        # Set expected size from first frame
        if self.expected_size is None:
            self.expected_size = len(csi_frame)

        # Only add frames with matching size
        if len(csi_frame) == self.expected_size:
            self.buffer.append(csi_frame)
            self.last_frame = csi_frame

    def get_motion_level(self):
        """Calculate motion level from recent frames"""
        if len(self.buffer) < 50:
            return 0.0

        recent = list(self.buffer)[-50:]
        variances = []
        for i in range(len(recent) - 1):
            diff = np.abs(recent[i+1] - recent[i])
            variances.append(np.mean(diff))

        return np.mean(variances) if variances else 0.0

    def get_recent_frames(self, num_frames):
        """
        Get the most recent N frames
        Returns: list of CSI arrays, or None if not enough frames
        """
        if len(self.buffer) < num_frames:
            return None

        # Get last num_frames
        return list(self.buffer)[-num_frames:]

    def get_window(self, num_frames):
        """
        Get a sliding window of frames
        Returns: list of CSI arrays, or None if not enough frames
        """
        return self.get_recent_frames(num_frames)

    def __len__(self):
        return len(self.buffer)
