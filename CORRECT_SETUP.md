# FRER Test - CORRECT Setup (2 PCs + 2 Boards)

## ✅ Actual Hardware Configuration

### Components:
- **2 PCs**: Sender PC (10.0.100.1) and Receiver PC (10.0.100.2)
- **2 LAN9662 Boards**: Sender Board and Receiver Board
- **Connection**: PC → Board → Board → PC

## 🔌 Real Network Topology

```
┌──────────────┐        ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  Sender PC   │        │ Sender Board │        │Receiver Board│        │ Receiver PC  │
│ 10.0.100.1   │───────►│  (LAN9662)   │───────►│  (LAN9662)   │───────►│ 10.0.100.2   │
│              │ enp2s0 │              │eth1/2  │              │ enp15s0│              │
│              │◄──────►│     eth3     │        │     eth3     │◄──────►│              │
└──────────────┘        │              │        │              │        └──────────────┘
                        │   ┌──eth1────┼────────┼───eth1──┐    │
                        │   │          │        │          │    │
                        │   │   FRER   │        │   FRER   │    │
                        │   │   Gen    │        │   Elim   │    │
                        │   │          │        │          │    │
                        │   └──eth2────┼────────┼───eth2──┘    │
                        └──────────────┘        └──────────────┘

Traffic Flow:
1. Sender PC (10.0.100.1) → generates traffic
2. Sender Board eth3 → receives traffic
3. Sender Board → duplicates to eth1 & eth2 (with R-TAG)
4. Receiver Board eth1 & eth2 → receive duplicates
5. Receiver Board → eliminates duplicates
6. Receiver Board eth3 → outputs single stream
7. Receiver PC (10.0.100.2) → receives deduplicated traffic
```

## 💻 PC Configuration

### Sender PC (10.0.100.1)
```bash
# Configure network interface connected to Sender Board eth3
sudo ip addr add 10.0.100.1/24 dev enp2s0
sudo ip link set enp2s0 up

# Verify connection
ping 10.0.100.2  # Should work after full setup
```

### Receiver PC (10.0.100.2)
```bash
# Configure network interface connected to Receiver Board eth3
sudo ip addr add 10.0.100.2/24 dev enp15s0
sudo ip link set enp15s0 up
```

## 🎛️ Board Configuration

### Sender Board (Serial Console /dev/ttyUSB0)
```bash
# 1. Setup interfaces
ip link set eth1 up
ip link set eth2 up
ip link set eth3 up

# 2. Create bridge with VLAN filtering
ip link add name br0 type bridge vlan_filtering 1
ip link set br0 up
ip link set eth1 master br0
ip link set eth2 master br0
ip link set eth3 master br0

# 3. Configure VLAN 10
bridge vlan del dev eth1 vid 1
bridge vlan del dev eth2 vid 1
bridge vlan del dev eth3 vid 1
bridge vlan add dev eth1 vid 10       # Tagged for FRER
bridge vlan add dev eth2 vid 10       # Tagged for FRER
bridge vlan add dev eth3 vid 10 pvid untagged  # Access port for PC

# 4. FRER VLAN settings
frer vlan 10 --flood_disable 0 --learn_disable 0

# 5. VCAP rule (classify incoming traffic from PC)
vcap add 1001 is1 10 1 VCAP_KFS_NORMAL \
  IF_IGR_PORT_MASK 0x008 0x1ff \  # eth3 = bit 3
  ETYPE 0x0800 = \
  VCAP_AFS_S1 VID_REPLACE_ENA 1 VID_VAL 10 \
  ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 1

# 6. Enable FRER generation (duplicate to eth1 and eth2)
frer iflow 1 --generation 1 --dev1 eth1 --dev2 eth2
```

### Receiver Board (SSH 169.254.100.2)
```bash
# 1. Setup interfaces
ip link set eth1 up
ip link set eth2 up
ip link set eth3 up

# 2. Bridge and VLAN (same as sender)
ip link add name br0 type bridge vlan_filtering 1
ip link set br0 up
ip link set eth1 master br0
ip link set eth2 master br0
ip link set eth3 master br0

# 3. VLAN configuration
bridge vlan del dev eth1 vid 1
bridge vlan del dev eth2 vid 1
bridge vlan del dev eth3 vid 1
bridge vlan add dev eth1 vid 10       # Tagged from sender
bridge vlan add dev eth2 vid 10       # Tagged from sender
bridge vlan add dev eth3 vid 10 pvid untagged  # Access port to PC

# 4. VCAP rules (classify by ingress port)
vcap add 1001 is1 11 1 VCAP_KFS_NORMAL \
  IF_IGR_PORT_MASK 0x001 0x1ff \  # eth1
  VCAP_AFS_S1 ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 3

vcap add 1002 is1 12 1 VCAP_KFS_NORMAL \
  IF_IGR_PORT_MASK 0x002 0x1ff \  # eth2
  VCAP_AFS_S1 ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 4

# 5. Compound Stream (for duplicate elimination)
frer cs 0 --enable 1 --alg 0 --hlen 10 --reset_time 500

# 6. Member Streams
frer ms eth1 28 --enable 1 --alg 1 --reset_time 500 --cs_id 0
frer ms eth2 30 --enable 1 --alg 1 --reset_time 500 --cs_id 0

# 7. Ingress flows (eliminate duplicates and output to eth3)
frer iflow 3 --ms_enable 1 --ms_id 28 --pop 1 --dev1 eth3
frer iflow 4 --ms_enable 1 --ms_id 30 --pop 1 --dev1 eth3
```

## 🧪 Testing Process

### 1. Generate Traffic (on Sender PC)
```bash
# Simple ping test
ping -c 10 10.0.100.2

# UDP traffic generation
iperf3 -c 10.0.100.2 -u -b 100M -t 60

# Or use custom packet generator
python3 generate_traffic.py --dst 10.0.100.2 --rate 1000pps --duration 60
```

### 2. Monitor on Sender Board
```bash
# Check if packets are being duplicated
tcpdump -i eth1 -c 10 -n -e ether proto 0xf1c1  # Should see R-TAG
tcpdump -i eth2 -c 10 -n -e ether proto 0xf1c1  # Should see R-TAG

# Check VCAP hits
vcap get 1001  # Counter should be increasing
```

### 3. Monitor on Receiver Board
```bash
# Check FRER statistics
frer cs 0 --cnt  # Should show passed and discarded packets

# Member stream stats
frer ms eth1 28 --cnt
frer ms eth2 30 --cnt

# Output to PC
tcpdump -i eth3 -c 10 -n udp  # Should see deduplicated traffic
```

### 4. Verify on Receiver PC
```bash
# Should receive traffic without duplicates
tcpdump -i enp15s0 -n udp port 5001

# Run iperf3 server
iperf3 -s
```

## ✅ Success Criteria

1. **Sender Board**:
   - VCAP hit counter increases with traffic
   - Both eth1 and eth2 show R-TAG frames (0xf1c1)
   - No errors in FRER generation

2. **Receiver Board**:
   - PassedPackets ≈ number of unique packets
   - DiscardedPackets ≈ PassedPackets (one duplicate eliminated)
   - Elimination Rate > 99%
   - No packet loss

3. **End-to-End**:
   - Receiver PC gets all packets
   - No duplicates at receiver
   - Latency < 2ms
   - Throughput close to line rate

## 🔴 Common Issues

### No Traffic Passing:
- Check physical cables (eth1→eth1, eth2→eth2, NOT crossed!)
- Verify VLAN 10 on all interfaces
- Check VCAP port masks match actual port numbers

### No Duplication:
- Verify `frer iflow 1` shows generation=1
- Check ISDX mapping in VCAP rule

### No Elimination:
- Ensure compound stream is enabled
- Member streams must be linked to compound stream (cs_id=0)
- Check ingress flows have ms_enable=1 and pop=1

## 📊 Expected Statistics

After 1 minute of 100Mbps traffic:
```
Sender Board:
  VCAP Rule 1001: ~150,000 hits
  eth1 TX: ~150,000 frames with R-TAG
  eth2 TX: ~150,000 frames with R-TAG

Receiver Board:
  Compound Stream 0:
    PassedPackets: ~150,000
    DiscardedPackets: ~149,750
    LostPackets: 0
    Elimination Rate: 99.8%+
```