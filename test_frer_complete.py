#!/usr/bin/env python3
"""
Complete FRER Test - Send traffic and monitor results
"""
import subprocess
import time
import threading
import json

def send_udp_traffic(duration=10):
    """Send UDP traffic from 10.0.100.1 to 10.0.100.2"""
    print("Starting UDP traffic generation...")
    cmd = f"timeout {duration} iperf3 -c 10.0.100.2 -u -b 10M -p 5001 -t {duration}"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print("Traffic generation completed")
        return result.stdout
    except Exception as e:
        print(f"Traffic generation error: {e}")
        return None

def check_frer_stats():
    """Check FRER statistics on receiver"""
    print("\n=== Checking FRER Statistics on Receiver ===")
    
    commands = [
        "frer cs 0 --cnt",
        "frer ms eth1 28 --cnt",
        "frer ms eth2 30 --cnt"
    ]
    
    stats = {}
    for cmd in commands:
        ssh_cmd = f"ssh -o ConnectTimeout=5 root@169.254.100.2 '{cmd}' 2>/dev/null"
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            stats[cmd] = result.stdout
            print(f"\n{cmd}:")
            print(result.stdout)
    
    return stats

def monitor_receiver_interface():
    """Monitor eth3 on receiver for deduplicated traffic"""
    print("\n=== Monitoring Receiver eth3 ===")
    ssh_cmd = "ssh -o ConnectTimeout=5 root@169.254.100.2 'tcpdump -i eth3 -c 10 -n udp' 2>/dev/null"
    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=15)
    if result.returncode == 0:
        print("Packets on eth3 (deduplicated):")
        print(result.stdout)
    return result.stdout

def monitor_sender_interfaces():
    """Monitor eth1 and eth2 on sender for R-TAG frames"""
    print("\n=== Checking for R-TAG on Sender Interfaces ===")
    
    for iface in ['eth1', 'eth2']:
        cmd = f"sudo timeout 3 tcpdump -i {iface} -c 5 -n -e ether proto 0xf1c1 2>/dev/null"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"\nR-TAG frames on {iface}:")
        if result.stdout:
            print(result.stdout)
        else:
            print(f"No R-TAG frames captured on {iface}")

def run_complete_test():
    """Run complete FRER test"""
    print("="*60)
    print("FRER COMPLETE TEST")
    print("="*60)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Check initial stats
    print("\n1. Initial FRER Statistics")
    initial_stats = check_frer_stats()
    
    # 2. Start monitoring threads
    print("\n2. Starting Traffic Test")
    
    # Send traffic in background
    traffic_thread = threading.Thread(target=send_udp_traffic, args=(10,))
    traffic_thread.start()
    
    # Wait a bit for traffic to start
    time.sleep(2)
    
    # 3. Monitor interfaces
    monitor_sender_interfaces()
    monitor_receiver_interface()
    
    # Wait for traffic to complete
    traffic_thread.join()
    
    # 4. Check final stats
    print("\n3. Final FRER Statistics")
    final_stats = check_frer_stats()
    
    # 5. Analyze results
    print("\n="*60)
    print("TEST ANALYSIS")
    print("="*60)
    
    # Parse stats for analysis
    for cmd in final_stats:
        if "PassedPackets" in final_stats[cmd]:
            lines = final_stats[cmd].split('\n')
            for line in lines:
                if "PassedPackets" in line or "DiscardedPackets" in line:
                    print(f"{cmd.split()[1]}: {line.strip()}")
    
    print("\n✓ Test completed successfully")
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'initial_stats': initial_stats,
            'final_stats': final_stats
        }, f, indent=2)
    
    print("Results saved to test_results.json")

if __name__ == "__main__":
    run_complete_test()
