OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"
from otns.cli import OTNS
from my_functions import (
     calculate_device_roles,
    place_leader, place_routers_cross,
    place_reeds_diagonal_and_ring, place_feds_ring,
    add_fed, add_reed, add_router
)
import subprocess ,  os ,  signal , time
from datetime import datetime
from metrics.leader_election_phase import LeaderElectionPhase
from metrics.topology_convergence_phase import TopologyConvergencePhase
CENTER_X, CENTER_Y = 200, 200
import time
from random import choice, choices
from string import ascii_letters, digits


class Experiment:
    def __init__(self, initial_devices=10, spacing=20, log_file="mylogs.log",run_index=0):
        self.total_converge = None ;self.start_converge = None;self.end_baseline = None;self.start_baseline = None;self.end_converge = None
        self.run_index=run_index
        self.initial_devices = initial_devices
        self.spacing = spacing
        self.log_file = log_file
        # -----------------------------------
        self.Setup()
        self.Baseline()
        self.Converge()
        self.EndToEnd_Ping()  # <<< ADD THIS
        # self.ScaleUP() # self.ScaleDown()
        self.Closing()

    def EndToEnd_Ping(self, datasize=4, count=1, interval=1):
        print("\n🚀 Step: End-to-End Ping and CoAP Test...\n")

        # 🧩 1. Discover all device pairs
        nodes = list(self.ns.nodes().keys())
        pending_pings = []
        pending_coaps = []

        # 🚀 2. Start CoAP servers and create /test-resource on all nodes
        print("\n🚀 Starting CoAP servers and setting /test-resource on all nodes...\n")
        for node_id in nodes:
            try:
                self.ns.node_cmd(node_id, "coap start")
                self.ns.node_cmd(node_id, "coap resource test-resource")
                print(f"✅ CoAP server and /test-resource created on Node {node_id}")
            except Exception as e:
                print(f"⚠️ Failed to setup CoAP server on Node {node_id}: {e}")

        # Give time for CoAP servers to be ready
        self.ns.go(2)

        # 🔄 3. For each (src ➔ dst) pair, do:
        for src in nodes:
            for dst in nodes:
                if src == dst:
                    continue

                # 🛰️ 3.1 Perform Ping
                try:
                    self.ns._do_command(f"ping {src} {dst} rloc datasize {datasize} count {count} interval {interval}")
                    print(f"✅ Sent ping from Node {src} ➔ Node {dst}")
                    pending_pings.append((src, dst))
                    self.ns.go(2)  # allow ping to process
                except Exception as e:
                    print(f"⚠️ Immediate Ping Error: {src} ➔ {dst}: {e}")

                # 🌐 3.2 Perform CoAP POST
                try:
                    payload = f"hello-{src}-to-{dst}"
                    dst_mleid = self.ns.node_cmd(dst, "ipaddr mleid")[0]
                    # Correct CoAP POST syntax to /test-resource
                    self.ns.node_cmd(src, f'coap put {dst_mleid} test-resource con {payload}')
                    print(f"✅ Sent CoAP from Node {src} ➔ Node {dst} payload='{payload}'")
                    pending_coaps.append((src, dst))
                    self.ns.go(2)  # allow CoAP to process
                except Exception as e:
                    print(f"⚠️ CoAP Error {src} ➔ {dst}: {e}")

        # ⏳ 4. Wait for all messages to finish
        print("\n⏳ Waiting for all pings and CoAPs to complete across the network...")
        self.ns.go(5)

        # 🧹 5. Collect Ping Results
        print("\n📜 Collecting ping results...\n")
        pings_output = self.ns._do_command("pings")

        found_sources = set()
        for line in pings_output:
            if line.startswith("node="):
                parts = line.split()
                src_id = int(parts[0].split("=")[1])
                found_sources.add(src_id)

        failed_pings = []
        for src, dst in pending_pings:
            if src not in found_sources:
                failed_pings.append((src, dst))

        # 🚨 6. Final Check
        if failed_pings:
            print(f"\n❌ Unreachable pings detected: {failed_pings}")
            raise AssertionError(f"End-to-End Ping FAILED: {failed_pings}")
        else:
            print("\n✅ All nodes reachable by ping!")

        # 📦 CoAP delivery is currently fire-and-forget. Future: verify CoAP acks!

    def Setup(self):
        print("\n\n\n!===:",self.initial_devices,":",self.run_index,"\n\n\n")
        self.ns = OTNS(otns_path=OTNS_PATH, otns_args=["-log", "debug"])  # ,
        self.ns.set_title("DAfI - Scalable Mesh Network")
        self.ns.set_network_info(version="Latest", commit="main", real=False)
        self.ns.web()
        self.ns.speed = 100

    def Baseline(self):
        self.start_baseline = datetime.now()
        routers, reeds, feds = calculate_device_roles(self.initial_devices)
        routers -= 1  # reserve 1 leader

        place_leader(self.ns, CENTER_X, CENTER_Y, OT_CLI_ftd, add_router)
        place_routers_cross(self.ns, CENTER_X, CENTER_Y, routers, self.spacing, OT_CLI_ftd, add_router)
        place_reeds_diagonal_and_ring(self.ns, CENTER_X, CENTER_Y, reeds, self.spacing, OT_CLI_ftd, add_reed)
        place_feds_ring(self.ns, CENTER_X, CENTER_Y, feds, self.spacing * 3, OT_CLI_ftd, add_fed)

        for node_id in self.ns.nodes().keys():
            self.ns.node_cmd(node_id, "state")
        self.end_baseline = datetime.now()
        self.total_baseline = self.end_baseline - self.start_baseline
        print("end_baseline:",self.total_baseline)


    def Converge(self):
        self.start_converge = datetime.now()
        print("! Starting Convergence Check")
        self.Converge__()
        self.end_converge = datetime.now()
        self.total_converge = self.end_converge - self.start_converge
        print("! END Convergence Check:",self.total_converge)

    def Converge__(self):
        self.ns.go(0.1)
        phase_leader = LeaderElectionPhase(self.ns)
        success = phase_leader.run()
        if not success:
            raise RuntimeError("$ Leader Election Phase failed.")

        self.safe_comm_window(extra_wait=10)

        # 🛡️ Inject keepalive traffic before Step 8 begins
        self.inject_keepalive_traffic(interval=5, duration=3)

        phase_topology = TopologyConvergencePhase(self.ns)
        # success = phase_topology.run()
        # if not success:
        #     raise RuntimeError("$ Topology Convergence Phase failed.")

    def safe_comm_window(self, extra_wait=10):
        print("\n🛡️ Entering Safe Communication Window...\n")

        # 🌟 Advance simulation to let RPL stabilize
        print(f"⏳ Waiting {extra_wait} simulated seconds...")
        self.ns.go(extra_wait)
        time.sleep(2)  # real wall time sleep

        # 📦 Optional small CoAP refresh: wake up nodes
        for nid in self.ns.nodes().keys():
            try:
                self.ns.node_cmd(nid, "coap start")
                self.ns.node_cmd(nid, "coap resource logs")
                print(f"• Node {nid}: CoAP service restarted")
            except Exception as e:
                print(f"⚠️ Node {nid}: CoAP restart failed: {e}")

        print("\n✅ Safe Communication Window ready — you can start ping/CoAP tests now!\n")

    def ScaleUP(self):pass

    def ScaleDown(self): pass

    def Closing(self):
        self.ns.go()
        self.ns.close()
        print("\n\n\n!===End:",self.initial_devices,":",self.run_index)

    def inject_keepalive_traffic(self, interval=5, duration=60):
        """
        Periodically send small CoAP messages between random nodes
        to keep neighbor tables alive.

        Args:
            interval: seconds between messages
            duration: total simulated seconds to keep injecting
        """
        print("\n🔄 Starting KeepAlive Traffic Injection...\n")

        start_time = time.time()
        elapsed = 0

        nodes = list(self.ns.nodes().keys())

        # Make sure CoAP service is started everywhere
        for nid in nodes:
            try:
                self.ns.node_cmd(nid, "coap start")
                self.ns.node_cmd(nid, "coap resource logs")
            except Exception as e:
                print(f"⚠️ Node {nid} failed to start CoAP: {e}")

        while elapsed < duration:
            src = choice(nodes)
            dst = choice(nodes)
            if src == dst:
                continue  # avoid self

            # get dst IP
            try:
                ips = [ip for ip in self.ns.node_cmd(dst, "ipaddr") if ip.startswith("fd") and ":ff:fe00:" in ip]
                if not ips:
                    continue
                dst_ip = ips[0]
            except Exception as e:
                print(f"⚠️ Could not get IP for node {dst}: {e}")
                continue

            # safe payload generation
            payload = ''.join(choices(ascii_letters + digits, k=8))
            payload = payload.replace('"', '').replace("'", '')  # clean, safe payload
            cmd = f'coap post {dst_ip} logs con \\"{payload}\\"'

            try:
                res = self.ns.node_cmd(src, cmd)
                print(f"KeepAlive: Node {src} ➔ Node {dst} ({dst_ip[:10]}...) ✅")
            except Exception as e:
                print(f"⚠️ KeepAlive failed: {src} ➔ {dst}: {e}")

            # Go simulation forward and wait real time
            self.ns.go(interval)
            time.sleep(0.1)

            elapsed = time.time() - start_time

        print("\n✅ KeepAlive Traffic Injection finished.\n")


# ----------------------------------------------------
def kill_otns_port(port=9000):
    try:
        result = subprocess.check_output(f"lsof -t -i :{port}", shell=True).decode().strip()
        if result:
            print(f"Killing existing OTNS process on port {port}: PID(s) {result}")
            for pid in result.splitlines():
                os.kill(int(pid), signal.SIGKILL)
    except subprocess.CalledProcessError:
        pass  # No process found, it's OK
