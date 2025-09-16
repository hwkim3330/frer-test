#!/usr/bin/env python3
"""
Verify and fix sender board FRER configuration
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
    ser.read_all()  # Clear buffer
    
    print("=== Verifying Sender FRER Configuration ===\n")
    
    # Check current FRER ingress flow
    send_cmd(ser, "frer iflow 1")
    
    # Check VCAP rule hits
    send_cmd(ser, "vcap get 1001")
    
    # Ensure bridge flood is enabled for eth3 (where PC connects)
    send_cmd(ser, "bridge link set dev eth3 flood on mcast_flood on")
    
    # Disable flood on FRER output ports to prevent loops
    send_cmd(ser, "bridge link set dev eth1 flood off mcast_flood off")
    send_cmd(ser, "bridge link set dev eth2 flood off mcast_flood off")
    
    # Show bridge link status
    send_cmd(ser, "bridge link show", wait=1)
    
    # Test: Send a ping through to verify connectivity
    send_cmd(ser, "ping -c 2 10.0.100.2", wait=3)
    
    ser.close()
    print("\n✓ Verification complete")
    
except Exception as e:
    print(f"Error: {e}")
