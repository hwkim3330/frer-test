#!/usr/bin/env python3
"""
Swap board roles - SSH board as sender, Serial board as receiver
"""
import subprocess
import time

print("=== Swapping Board Roles ===")
print("SSH Board (169.254.100.2) → SENDER")
print("Serial Board (ttyUSB0) → RECEIVER\n")

# Configure SSH board as SENDER
ssh_cmds = [
    # VLAN and bridge setup (already done)
    "bridge vlan show",
    
    # Remove receiver VCAP rules
    "vcap del 1001 2>/dev/null || true",
    "vcap del 1002 2>/dev/null || true", 
    
    # Add sender VCAP rule (eth3 ingress → ISDX=1)
    "vcap add 1001 is1 10 1 VCAP_KFS_NORMAL IF_IGR_PORT_MASK 0x008 0x1ff ETYPE 0x0800 = VCAP_AFS_S1 VID_REPLACE_ENA 1 VID_VAL 10 ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 1",
    
    # Configure FRER generation (ISDX=1 → duplicate to eth1/eth2)
    "frer iflow 1 --generation 1 --dev1 eth1 --dev2 eth2",
    
    # Verify
    "vcap get 1001",
    "frer iflow 1"
]

print("1. Configuring SSH board as SENDER...")
for cmd in ssh_cmds:
    result = subprocess.run(f"ssh root@169.254.100.2 '{cmd}' 2>/dev/null", 
                          shell=True, capture_output=True, text=True)
    if "vcap get" in cmd or "frer iflow" in cmd:
        print(f"\n{cmd}:")
        print(result.stdout)

print("\n✓ SSH board configured as sender")
print("\nNow configure Serial board as RECEIVER manually via serial console")
print("Required commands for receiver:")
print("  vcap add 1001 is1 11 1 VCAP_KFS_NORMAL IF_IGR_PORT_MASK 0x001 0x1ff VCAP_AFS_S1 ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 3")
print("  vcap add 1002 is1 12 1 VCAP_KFS_NORMAL IF_IGR_PORT_MASK 0x002 0x1ff VCAP_AFS_S1 ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 4")
print("  frer cs 0 --enable 1 --alg 0 --hlen 10 --reset_time 500")
print("  frer ms eth1 <MSID> --enable 1 --alg 1 --reset_time 500 --cs_id 0")
print("  frer iflow 3 --ms_enable 1 --ms_id <MSID> --pop 1 --dev1 eth3")
