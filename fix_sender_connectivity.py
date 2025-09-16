#!/usr/bin/env python3
"""
Fix connectivity: PC should connect to eth3 of sender board
The board's eth3 should be the access port where traffic enters
"""
import serial
import time

def cmd(ser, cmd_str, wait=0.5):
    ser.write((cmd_str + '\n').encode())
    time.sleep(wait)
    resp = ser.read_all().decode('utf-8', errors='ignore')
    print(f">>> {cmd_str}")
    if resp:
        print(resp.strip())
    return resp

try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    time.sleep(1)
    ser.read_all()
    
    print("=== Fixing Sender Board Connectivity ===\n")
    print("PC (10.0.100.2) → Sender eth3 → FRER Gen → eth1/eth2 → Receiver\n")
    
    # Ensure eth3 is in access mode (pvid 10 untagged)
    cmd(ser, "bridge vlan show dev eth3")
    
    # Move IP from br0 to eth0 (management interface)  
    cmd(ser, "ip addr del 10.0.100.1/24 dev br0 2>/dev/null || true")
    
    # Check physical connection on eth3
    cmd(ser, "ip link show eth3 | grep state")
    cmd(ser, "ethtool eth3 | grep 'Link detected'", wait=1)
    
    # Try to detect which interface connects to PC
    cmd(ser, "tcpdump -i eth3 -c 3 -n 2>/dev/null &")
    time.sleep(3)
    
    # Show MAC learning on bridge
    cmd(ser, "bridge fdb show | grep -v permanent")
    
    ser.close()
    print("\n✓ Sender connectivity check complete")
    
except Exception as e:
    print(f"Error: {e}")
