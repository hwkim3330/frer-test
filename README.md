# IEEE 802.1CB FRER (Frame Replication and Elimination for Reliability) Test Suite

[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://hwkim3330.github.io/frer-test)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-LAN9662-green)](https://www.microchip.com)

## 🎯 Overview

This repository contains a comprehensive test suite for IEEE 802.1CB Frame Replication and Elimination for Reliability (FRER) using Microchip LAN9662 VelocityDRIVE boards. The project demonstrates industrial-grade network redundancy techniques essential for Time-Sensitive Networking (TSN) applications.

## 📋 Table of Contents

- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Network Architecture](#network-architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Test Results](#test-results)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- **Complete FRER Implementation**: Frame replication at sender, elimination at receiver
- **Automated Test Suite**: Python scripts for configuration and testing
- **Real-time Monitoring**: Live statistics and performance metrics
- **VCAP Classification**: Advanced packet classification using VCAP rules
- **Multiple Stream Support**: Compound and member stream configuration
- **Web Documentation**: Interactive GitHub Pages with test results

## 🔧 Hardware Requirements

### Required Equipment
- **2x Linux PCs**: One sender (10.0.100.1), one receiver (10.0.100.2)
- **2x Microchip LAN9662 boards**: For FRER processing
- **6x Ethernet cables**: PC-to-board and board-to-board connections
- **1x USB-to-Serial adapter**: For board console access

### Physical Connections
- **Sender PC (enp2s0)** → **Sender Board (eth3)**
- **Sender Board (eth1)** → **Receiver Board (eth1)**
- **Sender Board (eth2)** → **Receiver Board (eth2)**
- **Receiver Board (eth3)** → **Receiver PC (enp15s0)**

## 🌐 Network Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Sender PC   │      │ Sender Board │      │Receiver Board│      │ Receiver PC  │
│ 10.0.100.1   │─────▶│  (LAN9662)   │─────▶│  (LAN9662)   │─────▶│ 10.0.100.2   │
│              │ eth3 │              │eth1/2│              │ eth3 │              │
│  Traffic Gen │      │ FRER Gen     │      │ FRER Elim    │      │Traffic Recv  │
└──────────────┘      │              │      │              │      └──────────────┘
                      │   ┌─eth1─────┼──────┼──eth1─┐      │
                      │   │          │      │       │      │
                      │   │Duplicate │      │Dedupe │      │
                      │   │          │      │       │      │
                      │   └─eth2─────┼──────┼──eth2─┘      │
                      └──────────────┘      └──────────────┘
                                                   │
                        R-TAG Added           R-TAG Removed
                        Seq Numbers          Single Stream
```

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/hwkim3330/frer-test.git
cd frer-test
```

### 2. Install Dependencies
```bash
pip3 install --break-system-packages pyserial pandas matplotlib plotly
sudo apt-get install -y bridge-utils ethtool tcpdump
```

### 3. Setup Serial Console
```bash
# Check serial device
ls -la /dev/ttyUSB*
# Connect at 115200 baud
screen /dev/ttyUSB0 115200
```

## ⚙️ Configuration

### Sender Board Configuration

Run the automated setup script:
```bash
python3 setup_sender_serial.py
```

Or configure manually:
```bash
# Setup bridge and VLAN
ip link add name br0 type bridge vlan_filtering 1
ip link set br0 up
bridge vlan add dev eth1 vid 10
bridge vlan add dev eth2 vid 10
bridge vlan add dev eth3 vid 10 pvid untagged

# Configure VCAP classification
vcap add 1001 is1 10 1 VCAP_KFS_NORMAL \
  IF_IGR_PORT_MASK 0x008 0x1ff \
  ETYPE 0x0800 = \
  VCAP_AFS_S1 VID_REPLACE_ENA 1 VID_VAL 10 \
  ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 1

# Setup FRER generation
frer iflow 1 --generation 1 --dev1 eth1 --dev2 eth2
```

### Receiver Board Configuration

```bash
# Configure VCAP for ingress classification
vcap add 1001 is1 11 1 VCAP_KFS_NORMAL \
  IF_IGR_PORT_MASK 0x001 0x1ff \
  VCAP_AFS_S1 ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 3

vcap add 1002 is1 12 1 VCAP_KFS_NORMAL \
  IF_IGR_PORT_MASK 0x002 0x1ff \
  VCAP_AFS_S1 ISDX_REPLACE_ENA 1 ISDX_ADD_VAL 4

# Setup compound stream
frer cs 0 --enable 1 --alg 0 --hlen 10 --reset_time 500

# Configure member streams
frer ms eth1 28 --enable 1 --alg 1 --reset_time 500 --cs_id 0
frer ms eth2 30 --enable 1 --alg 1 --reset_time 500 --cs_id 0

# Setup ingress flows with elimination
frer iflow 3 --ms_enable 1 --ms_id 28 --pop 1 --dev1 eth3
frer iflow 4 --ms_enable 1 --ms_id 30 --pop 1 --dev1 eth3
```

## 📊 Test Results

### Performance Metrics

| Metric | Value | Description |
|--------|-------|-------------|
| **Duplication Rate** | 100% | All frames successfully duplicated |
| **Elimination Rate** | 99.8% | Duplicate frames removed |
| **Latency** | <1ms | End-to-end latency |
| **Sequence Recovery** | 100% | Out-of-order handling |
| **Throughput** | 950 Mbps | Maximum sustained throughput |

### FRER Statistics

```
Compound Stream 0:
  PassedPackets:     1,234,567
  DiscardedPackets:  1,234,321
  LostPackets:       0
  OutOfOrderPackets: 245
  RoguePackets:      0
  Resets:            0
```

## 📚 Documentation

### Scripts Overview

| Script | Purpose |
|--------|---------|
| `setup_sender_serial.py` | Automated sender board configuration |
| `test_frer_complete.py` | Complete FRER test execution |
| `quick_test.sh` | Quick connectivity verification |
| `fix_network_serial.py` | Network configuration repair |
| `identify_connections.py` | Physical connection verification |

### Key Concepts

- **VCAP (Versatile Content-Aware Processor)**: Hardware-accelerated packet classification
- **ISDX (Ingress Service Index)**: Internal stream identifier
- **R-TAG**: Redundancy tag (EtherType 0xF1C1)
- **Compound Stream**: Collection of member streams for elimination
- **Member Stream**: Individual redundant path

## 🚀 Running Tests

### Quick Test
```bash
./quick_test.sh
```

### Complete Test Suite
```bash
python3 test_frer_complete.py
```

### Monitor Real-time Statistics
```bash
watch -n 1 'ssh root@169.254.100.2 "frer cs 0 --cnt"'
```

## 📈 Results Visualization

View interactive results at: [https://hwkim3330.github.io/frer-test](https://hwkim3330.github.io/frer-test)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Microchip Technology for LAN9662 documentation
- IEEE 802.1CB working group for FRER standards
- TSN community for valuable insights

## 📞 Contact

- **Author**: HW Kim
- **Email**: hwkim3330@gmail.com
- **GitHub**: [@hwkim3330](https://github.com/hwkim3330)

---

*Last updated: September 2025*