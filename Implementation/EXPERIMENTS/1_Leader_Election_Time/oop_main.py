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

import os, time, shutil, socket, sys

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
            states = {node_id: self.ns.node_cmd(node_id, "state")[0].strip() for node_id in self.ns.nodes()}

            # Log all states to debug output
            print(f"[{waited}s] Node states: {states}")

            if "leader" in states.values():
                print(f"🟩 Leader found at {waited}s: " +
                      ", ".join([f"{nid}={role}" for nid, role in states.items()]))
                return waited

            self.ns.go(interval)
            waited += interval

        print("🟥 No leader elected within the timeout.")
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
        time.sleep(1)
        self.ns.close()  # ⬅️ Ensures OTNS is properly shut down
        print("\n========== 📊 SIMULATION TIME SUMMARY ==========")
        print(self.initial_devices,":",self.run_index)
        print(f"🧱 Baseline convergence time (wall): {end_baseline - start_baseline}")
        print("===============================================")

import re
from datetime import datetime

def parse_leader_election_time(log_path):
    time_fmt = "%Y-%m-%d %H:%M:%S.%f"
    start_time = None
    role_changes = {}

    with open(log_path, 'r') as f:
        for line in f:
            # Simulation start
            if "dispatcher listening on" in line and start_time is None:
                match = re.search(r"\[(.*?)\]", line)
                if match:
                    start_time = datetime.strptime(match.group(1), time_fmt)

            # Role change log
            role_match = re.search(r'status push: (\d+): "role=(\d+)"', line)
            if role_match and start_time:
                node_id = int(role_match.group(1))
                role = int(role_match.group(2))
                log_time = datetime.strptime(line.split(']')[0][1:], time_fmt)

                if role == 4:  # Leader
                    return {
                        "duration": (log_time - start_time).total_seconds(),
                        "leader_node": node_id,
                        "leader_time": log_time.strftime(time_fmt)
                    }

    return None  # If no leader elected







def run_single_experiment(dev_count, run_index, log_files):

    folder_path = os.path.join(str(dev_count), str(run_index))
    if os.path.isfile(folder_path):
        os.remove(folder_path)
    os.makedirs(folder_path, exist_ok=True)

    log_file = os.path.join(folder_path, f"mylogs_{dev_count}_{run_index}.log")
    log_files.append(log_file)

    kill_otns_port(9000)
    log_handle = start_log(filename=log_file)
    test = LeaderElectionTest(initial_devices=dev_count, log_file=log_file, run_index=run_index)
    test.run()

    log_handle.close()
    sys.stdout = sys.__stdout__

    if hasattr(os, 'sync'):
        os.sync()

    time.sleep(3)
    waited = 0
    while waited < 10:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', 9000)) != 0:
                break
        print("⏳ Waiting for OTNS port to become available...")
        time.sleep(1)
        waited += 1

    print(f"🟢 Finished experiment: {dev_count} devices, run {run_index}")

    time.sleep(5)
    pcap_dst = os.path.join(folder_path, "capture.pcap")
    replay_dst = os.path.join(folder_path, "replay.otns")

    if os.path.exists("current.pcap"):
        shutil.move("current.pcap", pcap_dst)
        print(f"📦 Saved: {pcap_dst}")

    if os.path.exists("otns_0.replay"):
        shutil.move("otns_0.replay", replay_dst)
        print(f"📦 Saved: {replay_dst}")

    for file in ["current.pcap", "otns_0.replay"]:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"🧹 Removed leftover: {file}")
            except Exception as e:
                print(f"⚠️ Could not remove {file}: {e}")

    if os.path.exists("tmp"):
        try:
            shutil.rmtree("tmp")
            print("🧹 Cleaned up tmp/ directory.")
        except Exception as e:
            print(f"⚠️ Failed to remove tmp/: {e}")

def parse_and_summarize_results(log_files):
    import os
    from collections import defaultdict

    durations_by_device = defaultdict(list)

    for log_file in log_files:
        duration = parse_leader_election_time(log_file)
        if duration is not None:
            device_count = int(log_file.split("_")[1])
            durations_by_device[device_count].append((log_file, duration))

    output_lines = []
    output_lines.append("\n========== 🧪 Leader Election Times ==========\n")

    for device_count in sorted(durations_by_device):
        logs = durations_by_device[device_count]
        output_lines.append(f"\n🧩 Device Count: {device_count}")
        for log, dur_data in logs:
            duration = dur_data["duration"]
            leader = dur_data["leader_node"]
            line = f"  {log}: {duration:.2f} seconds (leader: node {leader})"
            print(line)
            output_lines.append(line)

        avg = sum(d["duration"] for _, d in logs) / len(logs)
        avg_line = f"  📊 AVERAGE for {device_count} devices: {avg:.2f} seconds"
        print(avg_line)
        output_lines.append(avg_line)

    with open("results.txt", "w") as result_file:
        for line in output_lines:
            result_file.write(line + "\n")


if __name__ == '__main__':
    try:
        log_files = []
        device_configs = [10, 25, 40, 80, 150, 250, 350, 450, 500]
        runs_per_config = 5

        for dev_count in device_configs:
            for run_index in range(1, runs_per_config + 1):
                run_single_experiment(dev_count, run_index, log_files)

        time.sleep(5)
        parse_and_summarize_results(log_files)

    except OTNSExitedError as ex:
        if ex.exit_code != 0:
            raise





# http://localhost:8997/visualize?addr=localhost:8998
# tshark -r  current.pcap -Y "udp.port == 19788" -V > results_pcap.txt