# Baseline Convergence Time Parser
# This script parses a .pcap and .replay file to measure
# Topology Convergence Time in an OTNS simulation baseline scenario

import json
from scapy.all import rdpcap
from datetime import datetime

# === Load replay file (OTNS event log) ===
replay_path = "otns_0.replay"
with open(replay_path, "r") as f:
    replay_lines = f.readlines()

# === Find initial topology setup ===
start_timestamp = None
for line in replay_lines:
    if "node add" in line and start_timestamp is None:
        parts = line.strip().split()
        try:
            start_timestamp = float(parts[0])
            print(f"🟢 Initial node placement started at: {start_timestamp:.3f}s")
            break
        except:
            pass

# === Load PCAP and extract key packet events ===
pcap_path = "current.pcap"
pkts = rdpcap(pcap_path)

first_mle_time = None
last_mle_time = None
first_udp_time = None

for pkt in pkts:
    if hasattr(pkt, 'time') and hasattr(pkt, 'payload'):
        try:
            pkt_time = pkt.time
            summary = str(pkt.summary())

            if "MLE" in summary:
                if first_mle_time is None:
                    first_mle_time = pkt_time
                last_mle_time = pkt_time

            if "UDP" in summary and first_udp_time is None:
                first_udp_time = pkt_time

        except Exception as e:
            continue

# === Compute Convergence Metrics ===
if start_timestamp and last_mle_time:
    convergence_time = last_mle_time - start_timestamp
    print(f"✅ Topology Convergence Time ≈ {convergence_time:.2f} seconds")
else:
    print("⚠️ Could not determine convergence timing accurately.")

# === Log to file ===
with open("log_4_Topology_Convergence_Time", "a") as log_file:
    log_file.write(f"baseline_setup,{convergence_time:.2f}\n")

print("📁 Logged baseline convergence time.")
