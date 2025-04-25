OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"
from otns.cli import OTNS
from my_functions import (
     calculate_device_roles,
    place_leader, place_routers_cross,
    place_reeds_diagonal_and_ring, place_feds_ring,
    add_fed, add_reed, add_router
)
import subprocess ,  os ,  signal
from datetime import datetime

CENTER_X, CENTER_Y = 400, 400


class Experiment:
    def __init__(self, initial_devices=10, spacing=25, log_file="mylogs.log",run_index=0):
        self.total_converge = None ;self.start_converge = None;self.end_baseline = None;self.start_baseline = None;self.end_converge = None
        self.run_index=run_index
        self.initial_devices = initial_devices
        self.spacing = spacing
        self.log_file = log_file
        # -----------------------------------
        self.Setup()
        self.Baseline()
        self.Converge()
        # self.ScaleUP() # self.ScaleDown()
        self.Closing()



    def Setup(self):
        print("\n\n\n⏱===:",self.initial_devices,":",self.run_index,"\n\n\n")
        self.ns = OTNS(otns_path=OTNS_PATH)  # , otns_args=["-log", "debug"]
        self.ns.set_title("DAfI - Scalable Mesh Network")
        self.ns.set_network_info(version="Latest", commit="main", real=False)
        self.ns.web()


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
        print("⏱ Starting Convergence Check")
        self.Converge__()
        self.end_converge = datetime.now()
        self.total_converge = self.end_converge - self.start_converge
        print("⏱ END Convergence Check:",self.total_converge)
    def Converge__(self):
        self.ns.go(0.1)
        self.check_leader_election()
        self.check_topology_convergence()

    def check_leader_election(self):

        def get_node_states():
            states = {}
            detached = []
            for node_id in self.ns.nodes().keys():
                state = self.ns.node_cmd(node_id, "state")[0].strip()
                states[node_id] = state
                if state in ["detached", "disabled"]:
                    detached.append((node_id, state))
            return states, detached

        def _1_wait_for_non_detached_nodes(max_wait=1200, interval=2):
            print("🔍 Step 1")
            waited = 0
            while waited <= max_wait:
                self.ns.go(interval)
                states, detached_nodes = get_node_states()
                print(f"⏱ {waited:>2}s | " + " ".join(f"{nid}:{state}" for nid, state in states.items()))

                if not detached_nodes:
                    print("✅ Step 1")
                    return
                waited += interval

            raise AssertionError(f"❌ Step 1 FAILED: Detached nodes after {max_wait}s → {detached_nodes}")

        def _2_single_leader_verification():
            print("🔍 Step 2")
            states, _ = get_node_states()
            leader_nodes = [nid for nid, state in states.items() if state == "leader"]
            if len(leader_nodes) != 1:
                raise AssertionError(f"❌ Step 2 FAILED: Expected 1 leader, found {len(leader_nodes)} → {leader_nodes}")
            print(f"✅ Step 2  : Leader = {leader_nodes[0]}")

        def _3_valid_roles():
            print("🔍 Step 3")
            states, _ = get_node_states()
            invalid_nodes = [
                (nid, state) for nid, state in states.items()
                if state != "leader" and state not in ["router", "child"]
            ]
            if invalid_nodes:
                raise AssertionError(f"❌ Step 3 FAILED: Non-leader nodes with invalid roles → {invalid_nodes}")
            print("✅ Step 3")

        def _4_rloc16_stability(delay=5):
            print("🔍 Step 4")

            def capture_rloc16():
                rlocs = {}
                for node_id in self.ns.nodes().keys():
                    state = self.ns.node_cmd(node_id, "state")[0].strip()
                    if state in ["leader", "router"]:
                        rloc = self.ns.node_cmd(node_id, "rloc16")[0].strip()
                        rlocs[node_id] = rloc
                return rlocs

            first_snapshot = capture_rloc16()
            self.ns.go(delay)
            second_snapshot = capture_rloc16()

            changed = [(nid, first_snapshot[nid], second_snapshot[nid])
                       for nid in first_snapshot
                       if first_snapshot[nid] != second_snapshot[nid]]

            if changed:
                raise AssertionError(f"❌ Step 4 FAILED: RLOC16 changed for nodes → {changed}")

            print("✅ Step 4")

        def _5_ipv6_address_stability(delay=5):
            print("🔍 Step 5")

            def get_ipaddrs():
                ip_table = {}
                for node_id in self.ns.nodes().keys():
                    ip_list = self.ns.node_cmd(node_id, "ipaddr")
                    ip_table[node_id] = sorted([ip.strip() for ip in ip_list])
                return ip_table

            snapshot1 = get_ipaddrs()
            self.ns.go(delay)
            snapshot2 = get_ipaddrs()

            changed = []
            for node_id in snapshot1:
                if snapshot1[node_id] != snapshot2[node_id]:
                    changed.append({
                        "node": node_id,
                        "before": snapshot1[node_id],
                        "after": snapshot2[node_id]
                    })

            if changed:
                raise AssertionError(f"❌ Step 5 FAILED: IPv6 addresses changed → {changed}")

            print("✅ Step 5")

        def _6_state_stability(delay=5):
            print("🔍 Step 6")

            def capture_states():
                state_map = {}
                for node_id in self.ns.nodes().keys():
                    state = self.ns.node_cmd(node_id, "state")[0].strip()
                    state_map[node_id] = state
                return state_map

            snapshot1 = capture_states()
            self.ns.go(delay)
            snapshot2 = capture_states()

            changed = []
            for node_id in snapshot1:
                if snapshot1[node_id] != snapshot2[node_id]:
                    changed.append({
                        "node": node_id,
                        "before": snapshot1[node_id],
                        "after": snapshot2[node_id]
                    })

            if changed:
                raise AssertionError(f"❌ Step 6 FAILED: Node state changed → {changed}")

            print("✅ Step 6")

        def _7_routing_message_silence(delay=5):
            print("🔍 Step 7")

            def get_dio_dao_counters():
                counters = {}
                for node_id in self.ns.nodes().keys():
                    state = self.ns.node_cmd(node_id, "state")[0].strip()
                    if state not in ["leader", "router"]:
                        continue

                    counter_output = self.ns.node_cmd(node_id, "counters")
                    dio = 0
                    dao = 0
                    for line in counter_output:
                        if line.startswith("mpl.in"):
                            dio = int(line.split()[-1])
                        elif line.startswith("dao.sent"):
                            dao = int(line.split()[-1])
                    counters[node_id] = {"dio": dio, "dao": dao}
                return counters

            before = get_dio_dao_counters()
            self.ns.go(delay)
            after = get_dio_dao_counters()

            changed = []
            for node_id in before:
                if after[node_id]["dio"] > before[node_id]["dio"] or after[node_id]["dao"] > before[node_id]["dao"]:
                    changed.append({
                        "node": node_id,
                        "before": before[node_id],
                        "after": after[node_id]
                    })

            if changed:
                raise AssertionError(f"❌ Step 7 FAILED: Routing messages still active → {changed}")

            print("✅ Step 7")

        _1_wait_for_non_detached_nodes()
        _2_single_leader_verification()
        _3_valid_roles()
        _4_rloc16_stability()
        _5_ipv6_address_stability()
        _6_state_stability()
        _7_routing_message_silence()


    def ScaleUP(self):pass

    def ScaleDown(self): pass

    def Closing(self):
        self.ns.close()
        print("\n\n\n⏱===End:",self.initial_devices,":",self.run_index)

    def check_topology_convergence(self):
        pass


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
