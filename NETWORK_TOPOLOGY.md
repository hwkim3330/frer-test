# FRER Test Network Topology - Actual Configuration

## 🔧 Correct Test Setup

### Physical Connections:
```
┌─────────────────┐                    ┌─────────────────┐                    ┌─────────────────┐
│   PC (Sender)   │                    │  Sender Board   │                    │ Receiver Board  │
│   10.0.100.1    │◄───────────────────│   (LAN9662)     │───────────────────►│   (LAN9662)     │
│                 │      Direct         │                 │    Redundant       │                 │
│                 │     Connection      │                 │     Paths          │                 │
│                 │      to PC          │                 │                    │                 │
│                 │                    │    ┌─────►eth1──┼────────────►eth1───┐                 │
│                 │                    │    │            │                    │                 │
│  Traffic Gen    │───────►eth3────────┼────┤  (Path 1)  │                    │  (Path 1)       │
│                 │                    │    │            │                    │                 │
│                 │                    │    └─────►eth2──┼────────────►eth2───┘                 │
│                 │                    │                 │                    │                 │
│                 │                    │     (Path 2)    │       (Path 2)     │                 │
│                 │                    │                 │                    │                 │
└─────────────────┘                    └─────────────────┘                    └─────────────────┘
                                              │                                        │
                                              ▼                                        ▼
                                        Frame Duplication                      Frame Elimination
                                         (Generation)                            (Recovery)
                                                                                       │
                                                                                       ▼
                                        ┌─────────────────┐                    ┌─────────────────┐
                                        │                 │                    │  PC (Receiver)  │
                                        │                 │◄───────────────────│   10.0.100.2    │
                                        │                 │       eth3         │                 │
                                        └─────────────────┘                    └─────────────────┘
```

## 📝 Correct Traffic Flow

### Actual Test Scenario:

1. **Traffic Generation (PC 10.0.100.1)**
   - PC generates UDP traffic targeting 10.0.100.2
   - Traffic enters Sender Board via eth3

2. **Sender Board Processing**
   - Receives packets on eth3 (access port)
   - VCAP rule classifies packets (ISDX=1)
   - FRER generation duplicates frames
   - Sends identical frames on eth1 and eth2 with R-TAG

3. **Network Path**
   - eth1 → direct cable → Receiver eth1
   - eth2 → direct cable → Receiver eth2
   - Both paths carry identical frames with sequence numbers

4. **Receiver Board Processing**
   - Receives duplicate frames on eth1 and eth2
   - VCAP rules classify by ingress port (ISDX=3,4)
   - Member streams process each path
   - Compound stream eliminates duplicates
   - Single frame forwarded to eth3

5. **Traffic Reception (PC 10.0.100.2)**
   - PC receives deduplicated traffic
   - Should see only one copy of each packet

## ⚠️ Current Issues with Documentation

### Problems Found:
1. **Incorrect IP Assignment**: Sender board shouldn't have IP 10.0.100.1 on bridge
2. **Wrong Interface Roles**: PC connects to board's eth3, not directly to bridge
3. **Missing Cable Connections**: Need to specify which PC NICs connect where

### Correct Configuration:

#### PC Side:
```bash
# Sender PC (generates traffic)
sudo ip addr add 10.0.100.1/24 dev enp2s0  # Connected to Sender Board eth3
sudo ip link set enp2s0 up

# Receiver PC (receives traffic)
sudo ip addr add 10.0.100.2/24 dev enp15s0  # Connected to Receiver Board eth3
sudo ip link set enp15s0 up
```

#### Sender Board:
```bash
# No IP needed on br0 - it's just switching
# eth3 is access port (untagged VLAN 10)
bridge vlan add dev eth3 vid 10 pvid untagged

# eth1/eth2 are FRER output ports
frer iflow 1 --generation 1 --dev1 eth1 --dev2 eth2
```

#### Receiver Board:
```bash
# No IP on bridge - just switching
# eth1/eth2 receive duplicates
# eth3 outputs deduplicated traffic
frer iflow 3 --ms_enable 1 --ms_id 28 --pop 1 --dev1 eth3
frer iflow 4 --ms_enable 1 --ms_id 30 --pop 1 --dev1 eth3
```

## 🔄 Test Verification

### How to Verify Setup:

1. **Check Physical Links**
```bash
# On PC
ethtool enp2s0 | grep "Link detected"  # Should be: yes
ethtool enp15s0 | grep "Link detected" # Should be: yes
```

2. **Generate Test Traffic**
```bash
# From 10.0.100.1 PC
ping 10.0.100.2  # Should work through the boards
iperf3 -c 10.0.100.2 -u -b 100M -t 10
```

3. **Monitor FRER Operation**
```bash
# On Sender Board (via serial)
tcpdump -i eth1 -c 5 -n -e ether proto 0xf1c1  # Should see R-TAG
tcpdump -i eth2 -c 5 -n -e ether proto 0xf1c1  # Should see R-TAG

# On Receiver Board (via SSH)
frer cs 0 --cnt  # Should show increasing passed/discarded packets
```

4. **Verify Deduplication**
```bash
# On Receiver PC (10.0.100.2)
tcpdump -i enp15s0 -n udp  # Should see single copy of each packet
```

## 📊 Expected Results

### Normal Operation:
- **Sender VCAP hits**: Should match number of packets sent
- **R-TAG frames**: Present on both eth1 and eth2 of sender
- **Receiver PassedPackets**: Should match packets sent
- **Receiver DiscardedPackets**: Should be approximately equal to PassedPackets
- **Elimination Rate**: Should be 99.9%+

### Link Failure Test:
```bash
# Disconnect one cable (e.g., eth2)
# Traffic should continue via eth1 only
# No packet loss should occur
```

## 🔧 Common Misconfigurations

1. **IP on Bridge**: Don't assign 10.0.100.x IPs to board bridges
2. **Wrong Port Masks**: Verify with `vcap -o is1` which bit represents which port
3. **VLAN Mismatch**: Ensure VLAN 10 is consistent across all interfaces
4. **Cable Swap**: eth1→eth1 and eth2→eth2 must be correctly connected