#!/usr/bin/env python3
"""
FRER Traffic Test Script
Tests Frame Replication and Elimination between two LAN9662 boards
"""

import subprocess
import time
import threading
import json
from datetime import datetime

def run_command(cmd, host=None):
    """Run command locally or via SSH"""
    if host:
        cmd = f"ssh root@{host} '{cmd}'"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout
    except:
        return ""

def get_frer_stats(host):
    """Get FRER statistics from receiver board"""
    stats = {}

    # Get compound stream stats
    output = run_command("frer cs 0 --cnt", host)
    for line in output.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            stats[f"cs0_{key.strip()}"] = int(value.strip())

    # Get member stream stats for eth1 path (MS ID 28)
    output = run_command("frer ms eth1 28 --cnt", host)
    for line in output.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            stats[f"ms28_{key.strip()}"] = int(value.strip())

    # Get member stream stats for eth2 path (MS ID 30)
    output = run_command("frer ms eth2 30 --cnt", host)
    for line in output.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            stats[f"ms30_{key.strip()}"] = int(value.strip())

    return stats

def capture_traffic(interface, duration=10):
    """Capture traffic on specified interface"""
    print(f"Capturing traffic on {interface} for {duration} seconds...")

    # Capture R-TAG frames
    cmd = f"sudo timeout {duration} tcpdump -i {interface} -w /tmp/{interface}_capture.pcap ether proto 0xf1c1 2>/dev/null"
    subprocess.run(cmd, shell=True)

    # Count packets
    cmd = f"sudo tcpdump -r /tmp/{interface}_capture.pcap 2>/dev/null | wc -l"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return int(result.stdout.strip())

def generate_udp_traffic(target_ip, port=5001, duration=10):
    """Generate UDP traffic using iperf3"""
    print(f"Generating UDP traffic to {target_ip}:{port} for {duration} seconds...")
    cmd = f"iperf3 -c {target_ip} -p {port} -u -b 10M -t {duration} -J"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    try:
        data = json.loads(result.stdout)
        return {
            'sent_packets': data['end']['sum']['packets'],
            'lost_packets': data['end']['sum']['lost_packets'],
            'lost_percent': data['end']['sum']['lost_percent']
        }
    except:
        return None

def main():
    print("=== FRER Test Started ===")
    print(f"Time: {datetime.now()}")

    receiver_ip = "169.254.100.2"
    test_duration = 30

    # Clear FRER counters
    print("\n1. Clearing FRER counters on receiver...")
    run_command("frer cs 0 --clr", receiver_ip)
    run_command("frer ms eth1 28 --clr", receiver_ip)
    run_command("frer ms eth2 30 --clr", receiver_ip)

    # Get initial stats
    print("\n2. Getting initial FRER stats...")
    initial_stats = get_frer_stats(receiver_ip)

    # Start packet capture threads
    print("\n3. Starting packet captures...")
    captures = {}
    interfaces = ['enp11s0', 'enp15s0', 'enp2s0']

    threads = []
    for iface in interfaces:
        t = threading.Thread(target=lambda i=iface: captures.update({i: capture_traffic(i, test_duration)}))
        t.start()
        threads.append(t)

    # Generate traffic
    print("\n4. Generating UDP test traffic...")
    time.sleep(2)  # Let captures start
    traffic_stats = generate_udp_traffic('10.0.100.2', duration=test_duration-4)

    # Wait for captures to complete
    for t in threads:
        t.join()

    # Get final FRER stats
    print("\n5. Getting final FRER stats...")
    final_stats = get_frer_stats(receiver_ip)

    # Calculate results
    print("\n=== TEST RESULTS ===")

    if traffic_stats:
        print(f"\nTraffic Generation:")
        print(f"  Sent: {traffic_stats.get('sent_packets', 0)} packets")
        print(f"  Lost: {traffic_stats.get('lost_packets', 0)} packets ({traffic_stats.get('lost_percent', 0):.2f}%)")

    print(f"\nPacket Captures:")
    for iface, count in captures.items():
        print(f"  {iface}: {count} R-TAG frames")

    print(f"\nFRER Statistics:")
    print(f"  Compound Stream (CS 0):")
    print(f"    Passed: {final_stats.get('cs0_PassedPackets', 0) - initial_stats.get('cs0_PassedPackets', 0)}")
    print(f"    Discarded: {final_stats.get('cs0_DiscardedPackets', 0) - initial_stats.get('cs0_DiscardedPackets', 0)}")
    print(f"    Lost: {final_stats.get('cs0_LostPackets', 0) - initial_stats.get('cs0_LostPackets', 0)}")

    print(f"\n  Member Stream eth1 (MS 28):")
    print(f"    Passed: {final_stats.get('ms28_PassedPackets', 0) - initial_stats.get('ms28_PassedPackets', 0)}")
    print(f"    Discarded: {final_stats.get('ms28_DiscardedPackets', 0) - initial_stats.get('ms28_DiscardedPackets', 0)}")

    print(f"\n  Member Stream eth2 (MS 30):")
    print(f"    Passed: {final_stats.get('ms30_PassedPackets', 0) - initial_stats.get('ms30_PassedPackets', 0)}")
    print(f"    Discarded: {final_stats.get('ms30_DiscardedPackets', 0) - initial_stats.get('ms30_DiscardedPackets', 0)}")

    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_duration': test_duration,
        'traffic_stats': traffic_stats,
        'captures': captures,
        'frer_initial': initial_stats,
        'frer_final': final_stats
    }

    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n=== Test Complete ===")
    print("Results saved to test_results.json")

if __name__ == "__main__":
    main()