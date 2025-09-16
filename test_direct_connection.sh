#!/bin/bash
# Test direct connection between PC and boards

echo "=== Testing Direct Connection ==="
echo "1. PC Network Configuration:"
ip addr show | grep -E "enp11s0|enp15s0|enp2s0" -A 2

echo -e "\n2. ARP Table:"
arp -n | grep -E "10.0.100|169.254.100"

echo -e "\n3. Testing connection to receiver board (SSH):"
ping -c 2 169.254.100.2

echo -e "\n4. Checking if sender board is reachable:"
ping -c 2 10.0.100.1

echo -e "\n5. Interface link status:"
for iface in enp11s0 enp15s0 enp2s0; do
    if ip link show $iface 2>/dev/null | grep -q "UP"; then
        echo "$iface: UP"
        ethtool $iface 2>/dev/null | grep -E "Link detected|Speed"
    fi
done
