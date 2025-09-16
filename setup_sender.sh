#!/bin/bash
# LAN9662 Sender Board Configuration
# To be run via serial console on sender board

# Enable interfaces
ip link set eth1 up
ip link set eth2 up
ip link set eth3 up

# Create bridge with VLAN filtering
ip link add name br0 type bridge vlan_filtering 1 || true
ip link set br0 up

# Add interfaces to bridge
ip link set eth1 master br0
ip link set eth2 master br0
ip link set eth3 master br0

# Configure VLAN 10
bridge vlan del dev eth1 vid 1 2>/dev/null
bridge vlan del dev eth2 vid 1 2>/dev/null
bridge vlan del dev eth3 vid 1 2>/dev/null

# eth3: ingress port (access/untagged)
bridge vlan add dev eth3 vid 10 pvid untagged
# eth1, eth2: egress ports (tagged for R-TAG)
bridge vlan add dev eth1 vid 10
bridge vlan add dev eth2 vid 10

# FRER VLAN settings
frer vlan 10 --flood_disable 0 --learn_disable 0

# VCAP: Classify ingress traffic from eth3 to ISDX=1
vcap del 1001 2>/dev/null
vcap add 1001 is1 10 1 VCAP_KFS_NORMAL \
  IF_IGR_PORT_MASK 0x008 0x1ff \
  VCAP_AFS_S1 ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 1

# FRER: Generate R-TAG and duplicate to eth1+eth2
frer iflow 1 --generation 1 --dev1 eth1 --dev2 eth2

echo "Sender configuration complete"
echo "ISDX=1 traffic will be duplicated with R-TAG to eth1 and eth2"