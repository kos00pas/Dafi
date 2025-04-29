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
from metrics._1leader_election_phase import LeaderElectionPhase
from metrics._4topology_convergence_phase import TopologyConvergencePhase
from metrics._2_rpl_stability_phase import RPLStabilityPhase
from metrics._5multicast_delay_phase import MulticastDelayPhase
from metrics._36packet_delivery_phase import PDR_ipv6
from metrics._7_lowpan_compression_phase import LowpanCompressionPhase
CENTER_X, CENTER_Y = 200, 200
import time
from random import choice, choices
from string import ascii_letters, digits


class Experiment:
    def __init__(self, initial_devices=10, spacing=35, log_file="mylogs.log",run_index=0):
        self.total_converge = None ;self.start_converge = None;self.end_baseline = None;self.start_baseline = None;self.end_converge = None
        self.run_index=run_index
        self.initial_devices = initial_devices
        self.spacing = spacing
        self.log_file = log_file
        self.result_file = open(os.path.join(str(self.initial_devices), str(self.run_index), "result.txt"), "w")

        # -----------------------------------
        self.Setup()
        self.Baseline()
        self.Converge()
        # self.ScaleUP() # self.ScaleDown()
        self.Closing()


    def Setup(self):
        print("\n\n\n!===:",self.initial_devices,":",self.run_index,"\n\n\n")
        self.ns = OTNS(otns_path=OTNS_PATH, otns_args=["-log", "debug"])  # ,
        self.ns.set_title("DAfI - Scalable Mesh Network")
        self.ns.set_network_info(version="Latest", commit="main", real=False)
        self.ns.web()
        self.ns.speed = 1000000000

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
        self._Converge()
        self.end_converge = datetime.now()
        self.total_converge = self.end_converge - self.start_converge
        print("! END Convergence Check:",self.total_converge)

    def _Converge(self):
        self.ns.go(0.1)

        # 🥇 1 Step 1-7: Leader Election and Initial Stability Checks
        phase_leader = LeaderElectionPhase(self.ns,self.result_file)  # from _1leader_election_phase.py
        success = phase_leader.run()
        if not success:
            raise RuntimeError("$ Leader Election Phase failed.")

        # 🛠️ 4 Step 8-11: Topology and Neighbor Table Convergence
        phase_topology = TopologyConvergencePhase(self.ns , self.result_file)  # from _4topology_convergence_phase.py
        success = phase_topology.run()
        if not success:
            raise RuntimeError("$ Topology Convergence Phase failed.")

        # 🌳 2 Step 12-13: RPL Route Stability and DIO/DAO Decay
        phase_rpl = RPLStabilityPhase(self.ns,self.result_file)  # from _2_rpl_stability_phase.py
        success = phase_rpl.run()
        if not success:
            raise RuntimeError("$ RPL Stability Phase failed.")

        # 📡5  Step 14-16: Multicast Propagation Delay (MPD) Measurement
        # phase_mcast = MulticastDelayPhase(self.ns,self.result_file)  # from _5multicast_delay_phase.py
        # success = phase_mcast.run()
        # if not success:
        #     raise RuntimeError("$ Multicast Delay Phase failed.")


        phase_packet_delivery = PDR_ipv6(self.ns,self.result_file)
        success, coap_results, role_batches = phase_packet_delivery.run()
        if not success:
            raise RuntimeError("$ Packet Delivery Phase failed.")

        phase_lowpan = LowpanCompressionPhase(self.ns,self.result_file)
        print(role_batches)
        phase_lowpan.run( role_batches)


    def ScaleUP(self):pass

    def ScaleDown(self): pass

    def Closing(self):
        # self.ns.go()
        self.ns.close()
        print("\n\n\n!===End:",self.initial_devices,":",self.run_index)
        self.result_file.close()

    # def inject_keepalive_traffic(self, interval=5, duration=60):
    #     """
    #     Periodically send small CoAP messages between random nodes
    #     to keep neighbor tables alive.
    #
    #     Args:
    #         interval: seconds between messages
    #         duration: total simulated seconds to keep injecting
    #     """
    #     print("\n🔄 Starting KeepAlive Traffic Injection...\n")
    #
    #     start_time = time.time()
    #     elapsed = 0
    #
    #     nodes = list(self.ns.nodes().keys())
    #
    #     # Make sure CoAP service is started everywhere
    #     for nid in nodes:
    #         try:
    #             self.ns.node_cmd(nid, "coap start")
    #             self.ns.node_cmd(nid, "coap resource logs")
    #         except Exception as e:
    #             print(f"⚠️ Node {nid} failed to start CoAP: {e}")
    #
    #     while elapsed < duration:
    #         src = choice(nodes)
    #         dst = choice(nodes)
    #         if src == dst:
    #             continue  # avoid self
    #
    #         # get dst IP
    #         try:
    #             ips = [ip for ip in self.ns.node_cmd(dst, "ipaddr") if ip.startswith("fd") and ":ff:fe00:" in ip]
    #             if not ips:
    #                 continue
    #             dst_ip = ips[0]
    #         except Exception as e:
    #             print(f"⚠️ Could not get IP for node {dst}: {e}")
    #             continue
    #
    #         # safe payload generation
    #         payload = ''.join(choices(ascii_letters + digits, k=8))
    #         payload = payload.replace('"', '').replace("'", '')  # clean, safe payload
    #         cmd = f'coap post {dst_ip} logs con \\"{payload}\\"'
    #
    #         try:
    #             res = self.ns.node_cmd(src, cmd)
    #             print(f"KeepAlive: Node {src} ➔ Node {dst} ({dst_ip[:10]}...) ✅")
    #         except Exception as e:
    #             print(f"⚠️ KeepAlive failed: {src} ➔ {dst}: {e}")
    #
    #         # Go simulation forward and wait real time
    #         self.ns.go(interval)
    #         time.sleep(0.1)
    #
    #         elapsed = time.time() - start_time
    #
    #     print("\n✅ KeepAlive Traffic Injection finished.\n")


    # def safe_comm_window(self, extra_wait=10):
    #     print("\n🛡️ Entering Safe Communication Window...\n")
    #
    #     # 🌟 Advance simulation to let RPL stabilize
    #     print(f"⏳ Waiting {extra_wait} simulated seconds...")
    #     self.ns.go(extra_wait)
    #     time.sleep(2)  # real wall time sleep
    #
    #     # 📦 Optional small CoAP refresh: wake up nodes
    #     for nid in self.ns.nodes().keys():
    #         try:
    #             self.ns.node_cmd(nid, "coap start")
    #             self.ns.node_cmd(nid, "coap resource logs")
    #             print(f"• Node {nid}: CoAP service restarted")
    #         except Exception as e:
    #             print(f"⚠️ Node {nid}: CoAP restart failed: {e}")
    #
    #     print("\n✅ Safe Communication Window ready — you can start ping/CoAP tests now!\n")

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
