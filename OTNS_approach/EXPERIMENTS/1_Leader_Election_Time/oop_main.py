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
        self.ns = OTNS(otns_path=OTNS_PATH) #, otns_args=["-log", "debug"]

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

        for node_id in self.ns.nodes().keys():
            self.ns.node_cmd(node_id, "state")

    import time

    def wait_for_convergence(self, max_wait=1200, interval=1):
        waited = 0
        dump_interval = 10  # for debug printing
        start_time = time.time()

        leader_elected_at = None
        topology_converged_at = None

        stable_leader = None
        stable_leader_count = 0
        required_stable_intervals = 3  # theory: stability requires N consistent checks

        last_states = None
        stable_topology_count = 0

        while waited < max_wait:
            states = {node_id: self.ns.node_cmd(node_id, "state")[0].strip()
                      for node_id in self.ns.nodes()}


            # === Theory Step 1: All nodes must be attached (no 'detached')
            if any(state == "detached" for state in states.values()):
                stable_leader = None
                stable_leader_count = 0
                stable_topology_count = 0
                last_states = None
                self.ns.go(interval)
                waited += interval
                continue

            # === Theory Step 2: One stable leader for N intervals
            # check for leader election time
            leader_nodes = [nid for nid, role in states.items() if role == "leader"]
            if len(leader_nodes) == 1:
                current_leader = leader_nodes[0]
                if current_leader == stable_leader:
                    stable_leader_count += 1
                else:
                    stable_leader = current_leader
                    stable_leader_count = 1

                # Log leader election time when stability confirmed
                if stable_leader_count == required_stable_intervals and leader_elected_at is None:
                    leader_elected_at = time.time()
                    print(f"🏁 Stable leader elected at {int(leader_elected_at - start_time)}s → Node {current_leader}")
            else:
                stable_leader = None
                stable_leader_count = 0

            # # === Optional Debug Dump
            # if waited % dump_interval == 0:
            #     for node_id in self.ns.nodes():
            #         print(f"🔁 Node {node_id} [@{waited}s] Neighbor Table:")
            #         neighbors = self.ns.node_cmd(node_id, "neighbor table")
            #         for line in neighbors:
            #             print(f"  {line.strip()}")
            #
            #         print(f"📡 Node {node_id} [@{waited}s] Route Table:")
            #         routes = self.ns.node_cmd(node_id, "route")
            #         for line in routes:
            #             print(f"  {line.strip()}")

            # === Theory Step 3: Convergence = Stable topology for N intervals
            if leader_elected_at is not None:
                if last_states == states:
                    stable_topology_count += 1
                else:
                    stable_topology_count = 1
                    last_states = states.copy()

                if stable_topology_count == required_stable_intervals:
                    print(f"[{waited}s] Node states: {states}")

                    topology_converged_at = time.time()
                    total_time = int(topology_converged_at - start_time)
                    leader_time = int(leader_elected_at - start_time)
                    print(f"✅ Topology converged at {total_time}s")
                    print(f"⏱️ Leader elected at {leader_time}s")
                    return {
                        "leader_election_time": leader_time,
                        "topology_convergence_time": total_time,
                        "leader_node": stable_leader
                    }

            self.ns.go(interval)
            waited += interval

        print("🟥 Network did not fully converge in time.")
        return {
            "leader_election_time": -1,
            "topology_convergence_time": -1,
            "leader_node": None
        }

    def run(self):
        print("⏱ Starting simulation")
        print(self.initial_devices,":",self.run_index)
        self.setup_simulator()
        sim_start = datetime.now()

        self.configure_baseline()

        start_baseline = datetime.now()

        print("⏱ Starting Convergence Check")
        convergence_time = self.wait_for_convergence()
        end_baseline = datetime.now()
        print("⏱ END Convergence Check")


        if convergence_time["topology_convergence_time"] >= 0:
            print(f"✅ Baseline converged in {convergence_time} sim seconds.")
            # initiate_coap_announcement(self.ns)
        else:
            print("❌ Baseline failed to converge.")

        self.ns.go(4)
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
        device_configs = [10]
        # device_configs = [10, 25, 40, 80, 150, 250, 350, 450, 500]
        # runs_per_config = 5
        runs_per_config = 1

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