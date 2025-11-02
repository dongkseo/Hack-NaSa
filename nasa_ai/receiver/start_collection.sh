#!/bin/bash
################################################################################
# 42Seoul CSI Data Collection Script
# Based on working SHARPax configuration
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  42Seoul CSI Data Collection${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Cleanup existing PicoScenes processes (NO SUDO!)
echo -e "${YELLOW}[1/3] Cleaning up existing processes...${NC}"
pkill -9 PicoScenes 2>/dev/null
sleep 1
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Start PicoScenes in background (NO SUDO!)
echo -e "${YELLOW}[2/3] Starting PicoScenes CSI capture @ 80 MHz...${NC}"
cd /home/dongkseo

PicoScenes "-i 2 --mode logger --output rx_realtime --rx-cbw 80 --rxcm 3 --txcm 3" &
PICO_PID=$!

echo -e "${GREEN}✓ PicoScenes started (PID: $PICO_PID)${NC}"
echo -e "${YELLOW}Waiting 5 seconds for initialization...${NC}"
sleep 5
echo ""

# Check if PicoScenes is still running
if ! ps -p $PICO_PID > /dev/null; then
    echo -e "${RED}✗ PicoScenes failed to start${NC}"
    exit 1
fi

# Start ping to generate continuous Wi-Fi traffic (use gateway)
echo -e "${YELLOW}Generating Wi-Fi traffic...${NC}"
GATEWAY=$(ip route | grep default | awk '{print $3}' | head -1)
if [ -n "$GATEWAY" ]; then
    ping -i 0.01 $GATEWAY > /dev/null 2>&1 &
    PING_PID=$!
    echo -e "${GREEN}✓ Ping started to $GATEWAY (PID: $PING_PID)${NC}"
else
    echo -e "${YELLOW}⚠ No gateway found, using 8.8.8.8${NC}"
    ping -i 0.01 8.8.8.8 > /dev/null 2>&1 &
    PING_PID=$!
fi
echo ""

# Start visualizer
echo -e "${YELLOW}[3/3] Starting CSI Visualizer...${NC}"
echo ""
echo -e "${CYAN}Instructions:${NC}"
echo "  - Click gesture button to START recording"
echo "  - Perform gesture"
echo "  - Click same button to STOP recording"
echo "  - Collect 10-20 samples per gesture"
echo ""
echo -e "  Data saved to: ${GREEN}./collected_data/${NC}"
echo ""

# Activate venv and start visualizer
source /home/dongkseo/Widar/.venv/bin/activate
cd /home/dongkseo/Widar/receiver
python csi_visualizer_verbose.py --csi-file /home/dongkseo/rx_realtime*.csi --save-dir ./collected_data

# Cleanup on exit
echo ""
echo -e "${YELLOW}Stopping processes...${NC}"
kill $PICO_PID 2>/dev/null
pkill -9 PicoScenes 2>/dev/null
if [ -n "$PING_PID" ]; then
    kill $PING_PID 2>/dev/null
fi

echo -e "${GREEN}✓ Done${NC}"
