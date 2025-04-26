

import re
from datetime import datetime
from collections import Counter
import pandas as pd

def analyze_leader_stability(log_path):
    leader_pattern = re.compile(r"\[(.*?)\].*state=leader")
    node_id_pattern = re.compile(r"id=(\d+).*?state=leader")

    leader_entries = []
    node_ids = []

    with open(log_path, "r") as f:
        for line in f:
            match = leader_pattern.search(line)
            if match:
                timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S.%f")
                leader_entries.append((timestamp, line.strip()))
                node_match = node_id_pattern.search(line)
                if node_match:
                    node_ids.append(int(node_match.group(1)))

    if not leader_entries:
        print("❌ No leader entries found.")
        return

    df = pd.DataFrame(leader_entries, columns=["timestamp", "log_line"])
    df["elapsed_since_first_sec"] = (df["timestamp"] - df["timestamp"].iloc[0]).dt.total_seconds()

    # Count how many times each node claimed to be leader
    leader_counts = Counter(node_ids)

    # Find the first node that appears multiple times as leader
    stable_leader_id = None
    for node_id, count in leader_counts.items():
        if count > 1:
            stable_leader_id = node_id
            break

    if stable_leader_id is not None:
        stable_leader_times = [
            row["timestamp"]
            for idx, row in df.iterrows()
            if f"id={stable_leader_id}" in row["log_line"]
        ]
        first_stable = stable_leader_times[0]
        last_stable = stable_leader_times[-1]
        stabilization_duration = (last_stable - df["timestamp"].iloc[0]).total_seconds()
    else:
        first_stable = last_stable = stabilization_duration = None

    print("\n===== Leader Stability Report =====")
    print(f"Unique Leader Claims: {dict(leader_counts)}")
    print(f"Stable Leader ID: {stable_leader_id}")
    print(f"First Appearance: {first_stable}")
    print(f"Last Confirmation: {last_stable}")
    print(f"Stabilization Duration (sec): {stabilization_duration:.2f}" if stabilization_duration else "Stabilization not detected.")

if __name__ == "__main__":
    log_file_path = "mylogs.log"  # Change if needed
    analyze_leader_stability(log_file_path)
