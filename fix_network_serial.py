#!/usr/bin/env python3
"""
Fix network configuration on sender board
"""
import serial
import time

def send_cmd(ser, cmd, wait=0.5):
    ser.write((cmd + '\n').encode())
    time.sleep(wait)
    resp = ser.read_all().decode('utf-8', errors='ignore')
    print(f">>> {cmd}")
    if resp:
        print(resp.strip())
    return resp

try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    time.sleep(1)
    ser.read_all()
    
    print("=== Fixing Network Configuration ===\n")
    
    # Add IP address to bridge for management
    send_cmd(ser, "ip addr add 10.0.100.1/24 dev br0")
    send_cmd(ser, "ip link set br0 up")
    
    # Verify IP configuration
    send_cmd(ser, "ip addr show br0 | grep inet")
    
    # Test connectivity
    send_cmd(ser, "ping -c 2 10.0.100.2", wait=3)
    
    # Check ARP
    send_cmd(ser, "ip neigh show")
    
    ser.close()
    print("\n✓ Network configuration complete")
    
except Exception as e:
    print(f"Error: {e}")
