#!/usr/bin/env python3
"""
Generate sample PCAP hex dumps showing R-TAG frames for FRER test
"""

import struct
import binascii
from datetime import datetime

def create_rtag_frame(seq_num, src_mac="22:f7:00:32:c9:f1", dst_mac="22:f7:00:32:c9:f1",
                      src_ip="10.0.100.1", dst_ip="10.0.100.2", src_port=45632, dst_port=5201):
    """Create a frame with R-TAG header"""

    # Ethernet header
    eth_dst = bytes.fromhex(dst_mac.replace(":", ""))
    eth_src = bytes.fromhex(src_mac.replace(":", ""))
    eth_type = struct.pack("!H", 0xf1c1)  # R-TAG EtherType

    # R-TAG header (6 bytes)
    rtag = struct.pack("!HHH",
                      0x0000,      # Reserved
                      seq_num,     # Sequence number
                      0x0000)      # Reserved

    # Inner Ethernet type (IPv4)
    inner_type = struct.pack("!H", 0x0800)

    # IPv4 header
    ip_ver_ihl = 0x45
    ip_tos = 0x00
    ip_total_len = 1500  # IP header + UDP header + payload
    ip_id = seq_num
    ip_flags_frag = 0x4000  # Don't fragment
    ip_ttl = 64
    ip_proto = 17  # UDP
    ip_checksum = 0x0000  # Will be calculated
    ip_src = struct.pack("!4B", *[int(x) for x in src_ip.split(".")])
    ip_dst = struct.pack("!4B", *[int(x) for x in dst_ip.split(".")])

    ip_header = struct.pack("!BBHHHBBH4s4s",
                           ip_ver_ihl, ip_tos, ip_total_len,
                           ip_id, ip_flags_frag,
                           ip_ttl, ip_proto, ip_checksum,
                           ip_src, ip_dst)

    # UDP header
    udp_len = 1480  # UDP header + payload
    udp_checksum = 0x0000
    udp_header = struct.pack("!HHHH", src_port, dst_port, udp_len, udp_checksum)

    # Payload (iperf3 pattern)
    payload = b"\x00\x01\x02\x03\x04\x05\x06\x07" * 184  # 1472 bytes

    # Combine all parts
    frame = eth_dst + eth_src + eth_type + rtag + inner_type + ip_header + udp_header + payload

    return frame

def create_pcap_header():
    """Create PCAP file header"""
    magic = 0xa1b2c3d4
    version_major = 2
    version_minor = 4
    thiszone = 0
    sigfigs = 0
    snaplen = 65535
    network = 1  # Ethernet

    return struct.pack("!IHHiIII", magic, version_major, version_minor,
                      thiszone, sigfigs, snaplen, network)

def create_pcap_packet(frame, timestamp=None):
    """Create PCAP packet record"""
    if timestamp is None:
        timestamp = datetime.now().timestamp()

    ts_sec = int(timestamp)
    ts_usec = int((timestamp - ts_sec) * 1000000)
    incl_len = len(frame)
    orig_len = len(frame)

    header = struct.pack("!IIII", ts_sec, ts_usec, incl_len, orig_len)
    return header + frame

def generate_hex_dump(data, offset=0, width=16):
    """Generate hex dump output similar to tcpdump -xx"""
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"0x{offset+i:04x}:  {hex_part:<48}  {ascii_part}")
    return '\n'.join(lines)

def main():
    print("=" * 80)
    print("FRER R-TAG Frame Examples")
    print("=" * 80)
    print()

    # Generate sample frames with different sequence numbers
    for seq in [0x0001, 0x0002, 0x0003, 0x1234, 0xEB48]:
        print(f"Frame with Sequence Number: 0x{seq:04X}")
        print("-" * 40)

        # Create frame for eth1
        frame_eth1 = create_rtag_frame(seq, src_mac="22:f7:00:32:c9:f1")

        # Show first 128 bytes in hex dump format
        print("Sender eth1 output:")
        print(generate_hex_dump(frame_eth1[:128]))
        print()

        # Highlight R-TAG bytes
        rtag_start = 12  # After Ethernet header
        rtag_bytes = frame_eth1[rtag_start:rtag_start+8]
        print(f"R-TAG Header bytes: {binascii.hexlify(rtag_bytes).decode()}")
        print(f"  EtherType: 0x{struct.unpack('!H', rtag_bytes[0:2])[0]:04x} (IEEE 802.1CB R-TAG)")
        print(f"  Reserved:  0x{struct.unpack('!H', rtag_bytes[2:4])[0]:04x}")
        print(f"  Sequence:  0x{struct.unpack('!H', rtag_bytes[4:6])[0]:04x} (decimal: {seq})")
        print(f"  Next Type: 0x{struct.unpack('!H', rtag_bytes[6:8])[0]:04x} (IPv4)")
        print()

    # Show deduplicated frame (without R-TAG)
    print("=" * 80)
    print("Deduplicated Frame (Receiver eth3 output)")
    print("-" * 40)

    # Create normal Ethernet frame without R-TAG
    eth_dst = bytes.fromhex("22:f7:00:32:c9:f3".replace(":", ""))
    eth_src = bytes.fromhex("22:f7:00:32:c9:f3".replace(":", ""))
    eth_type = struct.pack("!H", 0x0800)  # IPv4

    # Same IP and UDP as before
    ip_header = struct.pack("!BBHHHBBH4s4s",
                          0x45, 0x00, 1500,
                          0x1234, 0x4000,
                          64, 17, 0x0000,
                          struct.pack("!4B", 10, 0, 100, 1),
                          struct.pack("!4B", 10, 0, 100, 2))

    udp_header = struct.pack("!HHHH", 45632, 5201, 1480, 0x0000)
    payload = b"\x00\x01\x02\x03\x04\x05\x06\x07" * 184

    normal_frame = eth_dst + eth_src + eth_type + ip_header + udp_header + payload

    print("After FRER elimination:")
    print(generate_hex_dump(normal_frame[:96]))
    print()

    # Generate sample PCAP file content
    print("=" * 80)
    print("Sample PCAP File Structure")
    print("-" * 40)

    pcap_header = create_pcap_header()
    print(f"PCAP Header ({len(pcap_header)} bytes):")
    print(generate_hex_dump(pcap_header))
    print()

    # Create a few packets
    timestamp = datetime.now().timestamp()
    packets = []
    for i in range(3):
        frame = create_rtag_frame(i + 1)
        packet = create_pcap_packet(frame, timestamp + i * 0.0001)
        packets.append(packet)

    print(f"First packet record ({len(packets[0][:32])} bytes of header + frame):")
    print(generate_hex_dump(packets[0][:32]))
    print()

    # Write sample PCAP files
    print("=" * 80)
    print("Creating sample PCAP files...")
    print("-" * 40)

    # Create a small sample PCAP with R-TAG frames
    with open("/home/kim/frer-test-20250916_130401/test_logs/sample_rtag.pcap", "wb") as f:
        f.write(pcap_header)
        for i in range(10):
            frame = create_rtag_frame(i + 1)
            packet = create_pcap_packet(frame, timestamp + i * 0.001)
            f.write(packet)
    print("Created: test_logs/sample_rtag.pcap (10 R-TAG frames)")

    # Create a sample of deduplicated frames
    with open("/home/kim/frer-test-20250916_130401/test_logs/sample_deduplicated.pcap", "wb") as f:
        f.write(pcap_header)
        for i in range(10):
            packet = create_pcap_packet(normal_frame, timestamp + i * 0.001)
            f.write(packet)
    print("Created: test_logs/sample_deduplicated.pcap (10 normal frames)")

    print()
    print("Sample frames can be analyzed with:")
    print("  tcpdump -r test_logs/sample_rtag.pcap -xx")
    print("  tshark -r test_logs/sample_rtag.pcap -V")
    print("  wireshark test_logs/sample_rtag.pcap")

if __name__ == "__main__":
    main()