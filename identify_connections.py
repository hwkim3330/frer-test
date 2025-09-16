#!/usr/bin/env python3
"""
Identify actual physical connections between boards and PC
"""
import serial
import subprocess
import time

def test_connection():
    """Test which board is actually the sender"""
    print("=== Identifying Physical Connections ===\n")
    
    # PC interfaces status
    print("1. PC Interface Status:")
    for iface in ['enp2s0', 'enp11s0']:
        result = subprocess.run(f"ip addr show {iface} | grep inet", shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"  {iface}: {result.stdout.strip()}")
    
    print("\n2. Testing from PC:")
    
    # Send test packet from enp2s0 (10.0.100.2)
    print("\nSending test packet from enp2s0 (10.0.100.2)...")
    subprocess.run("sudo arping -I enp2s0 -c 2 10.0.100.1 2>/dev/null", shell=True)
    
    # Check serial board (currently thought as sender)
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        time.sleep(1)
        ser.read_all()
        
        # Check ARP on serial board
        ser.write(b"ip neigh show\n")
        time.sleep(0.5)
        resp = ser.read_all().decode('utf-8', errors='ignore')
        print(f"\n3. Serial Board (/dev/ttyUSB0) ARP table:")
        print(resp)
        
        # Check interface stats
        ser.write(b"ip -s link show eth3 | grep -A1 'RX:'\n")
        time.sleep(0.5)
        resp = ser.read_all().decode('utf-8', errors='ignore')
        print(f"\n4. Serial Board eth3 RX stats:")
        print(resp)
        
        ser.close()
    except:
        pass
    
    # Check SSH board (receiver)
    print("\n5. SSH Board (169.254.100.2) check:")
    result = subprocess.run("ssh -o ConnectTimeout=2 root@169.254.100.2 'ip neigh show' 2>/dev/null", 
                          shell=True, capture_output=True, text=True)
    if result.stdout:
        print(f"  ARP: {result.stdout.strip()}")

test_connection()
