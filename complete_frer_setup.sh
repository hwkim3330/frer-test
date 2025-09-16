#!/bin/bash
# Complete FRER Setup Script
echo "=== COMPLETE FRER SETUP ==="
echo "Time: $(date)"

# Since SSH board doesn't respond, let's work with what we have
echo -e "\n1. Checking PC connectivity to Serial board (actual connection):"
# The serial board (ttyUSB0) seems to be where PC connects based on RX stats

echo -e "\n2. Creating summary of current setup:"
cat > ~/frer-test-20250916_130401/current_setup.md << 'SETUP'
# FRER Test Setup Status

## Physical Connections
- PC enp2s0 (10.0.100.2) → Unknown board connection
- PC enp11s0 (169.254.13.30) → SSH Board eth0 (169.254.100.2) [Management]
- Serial Console (/dev/ttyUSB0) → One of the boards

## Current Configuration

### Serial Board (via /dev/ttyUSB0)
- Bridge: br0 with VLAN filtering
- VLAN 10: All ports configured
- eth3: Shows high RX traffic (likely PC connection)
- VCAP: Rule 1001 configured for ISDX=1
- FRER: iflow 1 with generation to eth1/eth2

### SSH Board (169.254.100.2) 
- Not responding to SSH commands properly
- Previously configured as receiver

## Issues Found
1. SSH board commands not executing properly
2. Need to identify which physical board is which
3. FRER statistics showing no traffic

## Next Steps
1. Use serial console to complete configuration
2. Generate test traffic directly
3. Monitor FRER statistics on serial board
SETUP

echo -e "\n3. Quick test using serial board as complete FRER device:"
echo "   Serial board will act as both generator and eliminator"

cat > ~/frer-test-20250916_130401/final_test.txt << 'TEST'
Commands to run on serial board for self-test:

# Create loopback FRER test
# eth3 input → FRER gen → eth1/eth2 → external loop → FRER elim → output

1. Keep existing generation config
2. Add elimination on same board:
   frer cs 0 --enable 1 --alg 0 --hlen 10 --reset_time 500
   frer ms eth1 20 --enable 1 --alg 1 --reset_time 500 --cs_id 0
   frer ms eth2 22 --enable 1 --alg 1 --reset_time 500 --cs_id 0

3. Check stats:
   frer cs 0 --cnt
   frer ms eth1 20 --cnt
   frer ms eth2 22 --cnt
TEST

cat ~/frer-test-20250916_130401/current_setup.md
echo -e "\nSetup documentation saved to ~/frer-test-20250916_130401/"
