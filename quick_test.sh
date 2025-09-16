#!/bin/bash
# Quick FRER test script

echo "=== Quick FRER Test ==="
echo "Time: $(date)"

RECEIVER="169.254.100.2"

# Check current FRER stats on receiver
echo -e "\n1. Current FRER stats on receiver:"
ssh root@$RECEIVER 'frer cs 0 --cnt | head -3'
ssh root@$RECEIVER 'vcap get 1001 2>/dev/null | grep Counter || echo "No VCAP hits yet"'

# Check if we can see any traffic
echo -e "\n2. Checking for R-TAG frames on interfaces:"
sudo timeout 5 tcpdump -i enp11s0 -c 3 ether proto 0xf1c1 2>&1 | grep -E "packets|0xf1c1" || echo "No R-TAG on enp11s0"
sudo timeout 5 tcpdump -i enp15s0 -c 3 ether proto 0xf1c1 2>&1 | grep -E "packets|0xf1c1" || echo "No R-TAG on enp15s0"

# Send test UDP packet
echo -e "\n3. Sending test UDP packets to 10.0.100.2..."
echo "test" | nc -u -w1 10.0.100.2 5001

# Check counters again
echo -e "\n4. FRER stats after test:"
ssh root@$RECEIVER 'frer cs 0 --cnt | grep PassedPackets'
ssh root@$RECEIVER 'frer ms eth1 28 --cnt | grep PassedPackets' 2>/dev/null || echo "MS 28 not found"
ssh root@$RECEIVER 'frer ms eth2 30 --cnt | grep PassedPackets' 2>/dev/null || echo "MS 30 not found"

echo -e "\n=== Test complete ==="