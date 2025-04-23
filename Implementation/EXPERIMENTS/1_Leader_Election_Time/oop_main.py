# === Refactored OOP Version for Leader Election Test ===

from datetime import datetime
from otns.cli import OTNS
from otns.cli.errors import OTNSExitedError
from MyJob.my_functions import (
    kill_otns_port, calculate_device_roles,
    place_leader, place_routers_cross,
    place_reeds_diagonal_and_ring, place_feds_ring
)
from MyJob.communication import initiate_coap_announcement
from MyJob.nodes import add_fed, add_reed, add_router
from MyJob.logging import start_log
import re

OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"
CENTER_X, CENTER_Y = 400, 400

class LeaderElectionTest:
    def __init__(self, initial_devices=10, spacing=25, log_file="mylogs.log",run_index=0):
        self.run_index=run_index
        self.initial_devices = initial_devices
        self.spacing = spacing
        self.log_file = log_file
        self.ns = OTNS(otns_path=OTNS_PATH, otns_args=["-log", "debug"])

    def setup_simulator(self):
        self.ns.set_title("DAfI - Scalable Mesh Network")
        self.ns.set_network_info(version="Latest", commit="main", real=False)
        self.ns.web()

    def configure_baseline(self):
        routers, reeds, feds = calculate_device_roles(self.initial_devices)
        routers -= 1  # reserve 1 leader

        place_leader(self.ns, CENTER_X, CENTER_Y, OT_CLI_ftd, add_router)
        place_routers_cross(self.ns, CENTER_X, CENTER_Y, routers, self.spacing, OT_CLI_ftd, add_router)
        place_reeds_diagonal_and_ring(self.ns, CENTER_X, CENTER_Y, reeds, self.spacing, OT_CLI_ftd, add_reed)
        place_feds_ring(self.ns, CENTER_X, CENTER_Y, feds, self.spacing * 3, OT_CLI_ftd, add_fed)

    def wait_for_convergence(self, max_wait=1200, interval=2):
        waited = 0
        while waited < max_wait:
            all_joined = all(
                self.ns.node_cmd(node_id, "state")[0].strip() != "detached"
                for node_id in self.ns.nodes()
            )
            if all_joined:
                return waited
            self.ns.go(interval)
            waited += interval
        return -1

    def run(self):
        print("⏱ Starting simulation")
        print(self.initial_devices,":",self.run_index)
        self.setup_simulator()
        sim_start = datetime.now()

        self.configure_baseline()
        start_baseline = datetime.now()
        convergence_time = self.wait_for_convergence()
        end_baseline = datetime.now()

        if convergence_time >= 0:
            print(f"✅ Baseline converged in {convergence_time} sim seconds.")
            initiate_coap_announcement(self.ns)
        else:
            print("❌ Baseline failed to converge.")

        self.ns.go(10)
        print("\n========== 📊 SIMULATION TIME SUMMARY ==========")
        print(f"🧱 Baseline convergence time (wall): {end_baseline - start_baseline}")
        print("===============================================")

def parse_leader_election_time(log_path):
    start_pattern = re.compile(r"\[(.*?)\].*dispatcher listening on")
    leader_pattern = re.compile(r"\[(.*?)\].*status push: \d+: \"role=4\"")

    with open(log_path, "r") as file:
        log_lines = file.readlines()

    start_time = None
    leader_time = None

    for line in log_lines:
        if start_time is None and start_pattern.search(line):
            start_time = datetime.strptime(start_pattern.search(line).group(1), "%Y-%m-%d %H:%M:%S.%f")
        elif leader_time is None and leader_pattern.search(line):
            leader_time = datetime.strptime(leader_pattern.search(line).group(1), "%Y-%m-%d %H:%M:%S.%f")
            break

    if start_time and leader_time:
        duration = (leader_time - start_time).total_seconds()
        print(f"Leader Election Time (from {log_path}): {duration:.2f} seconds")
        return duration
    else:
        print(f"Could not determine leader election time from {log_path}.")
        return None



import os
import shutil
import time
from collections import defaultdict

if __name__ == '__main__':
    try:
        log_files = []
        device_configs = [10, 20]
        runs_per_config = 2

        # === Phase 1: Run experiments ===
        for dev_count in device_configs:
            for run_index in range(1, runs_per_config + 1):
                # Setup paths
                folder_path = os.path.join(str(dev_count), str(run_index))
                os.makedirs(folder_path, exist_ok=True)

                log_file = os.path.join(folder_path, f"mylogs_{dev_count}_{run_index}.log")
                log_files.append(log_file)

                kill_otns_port(9000)
                start_log(filename=log_file)
                test = LeaderElectionTest(initial_devices=dev_count, log_file=log_file,run_index=run_index)
                test.run()

                # Move OTNS-generated files
                time.sleep(5)  # Ensure logs are flushed
                if os.path.exists("current.pcap"):
                    shutil.move("current.pcap", os.path.join(folder_path, "capture.pcap"))
                if os.path.exists("otns_0.replay"):
                    shutil.move("otns_0.replay", os.path.join(folder_path, "replay.otns"))

        time.sleep(5)
        # === Phase 2: Parse logs and collect results ===
        durations_by_device = defaultdict(list)

        for log_file in log_files:
            duration = parse_leader_election_time(log_file)
            if duration is not None:
                device_count = int(log_file.split("_")[1])
                durations_by_device[device_count].append((log_file, duration))

        # === Output per-log and grouped stats ===
        output_lines = []
        output_lines.append("\n========== 🧪 Leader Election Times ==========\n")

        for device_count in sorted(durations_by_device):
            logs = durations_by_device[device_count]
            output_lines.append(f"\n🧩 Device Count: {device_count}")
            for log, dur in logs:
                line = f"  {log}: {dur:.2f} seconds"
                print(line)
                output_lines.append(line)

            avg = sum(d[1] for d in logs) / len(logs)
            avg_line = f"  📊 AVERAGE for {device_count} devices: {avg:.2f} seconds"
            print(avg_line)
            output_lines.append(avg_line)

        # Save results summary
        with open("results.txt", "w") as result_file:
            for line in output_lines:
                result_file.write(line + "\n")

    except OTNSExitedError as ex:
        if ex.exit_code != 0:
            raise




# http://localhost:8997/visualize?addr=localhost:8998
# tshark -r  current.pcap -Y "udp.port == 19788" -V > results_pcap.txt