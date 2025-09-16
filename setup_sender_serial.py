#!/usr/bin/env python3
"""
Configure LAN9662 Sender Board for FRER via Serial
"""
import serial
import time
import sys

def send_command(ser, cmd, wait=0.5):
    """Send command and read response"""
    ser.write((cmd + '\n').encode())
    time.sleep(wait)
    response = ser.read_all().decode('utf-8', errors='ignore')
    print(f">>> {cmd}")
    if response:
        print(response)
    return response

def configure_sender():
    """Configure sender board for FRER generation"""
    try:
        # Open serial connection
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        time.sleep(2)  # Wait for connection
        
        print("=== Configuring Sender Board for FRER ===\n")
        
        # Clear buffer
        ser.read_all()
        
        # Basic setup
        send_command(ser, "")  # Send enter to get prompt
        
        print("\n1. Bringing up interfaces...")
        send_command(ser, "ip link set eth1 up")
        send_command(ser, "ip link set eth2 up")
        send_command(ser, "ip link set eth3 up")
        
        print("\n2. Setting up bridge and VLAN...")
        send_command(ser, "ip link add name br0 type bridge vlan_filtering 1 || true")
        send_command(ser, "ip link set br0 up")
        send_command(ser, "ip link set eth1 master br0")
        send_command(ser, "ip link set eth2 master br0")
        send_command(ser, "ip link set eth3 master br0")
        
        # VLAN configuration
        send_command(ser, "bridge vlan del dev eth1 vid 1 2>/dev/null || true")
        send_command(ser, "bridge vlan del dev eth2 vid 1 2>/dev/null || true")
        send_command(ser, "bridge vlan del dev eth3 vid 1 2>/dev/null || true")
        send_command(ser, "bridge vlan add dev eth1 vid 10")
        send_command(ser, "bridge vlan add dev eth2 vid 10")
        send_command(ser, "bridge vlan add dev eth3 vid 10 pvid untagged")
        
        print("\n3. Configuring FRER VLAN...")
        send_command(ser, "frer vlan 10 --flood_disable 0 --learn_disable 0")
        
        print("\n4. Setting up VCAP rule for classification...")
        send_command(ser, "vcap del 1001 2>/dev/null || true")
        send_command(ser, "vcap add 1001 is1 10 1 VCAP_KFS_NORMAL IF_IGR_PORT_MASK 0x008 0x1ff ETYPE 0x0800 = VCAP_AFS_S1 VID_REPLACE_ENA 1 VID_VAL 10 ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 1")
        
        print("\n5. Configuring FRER generation (duplicate to eth1 and eth2)...")
        send_command(ser, "frer iflow 1 --generation 1 --dev1 eth1 --dev2 eth2")
        
        print("\n6. Verifying configuration...")
        send_command(ser, "vcap get 1001", wait=1)
        send_command(ser, "frer iflow 1", wait=1)
        
        print("\n=== Sender Configuration Complete ===")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if configure_sender():
        print("\n✓ Sender board configured successfully")
        sys.exit(0)
    else:
        print("\n✗ Failed to configure sender board")
        sys.exit(1)
