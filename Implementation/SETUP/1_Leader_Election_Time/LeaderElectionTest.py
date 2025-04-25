OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"
from otns.cli import OTNS
from otns.cli.errors import OTNSExitedError
from my_functions import (
     calculate_device_roles,
    place_leader, place_routers_cross,
    place_reeds_diagonal_and_ring, place_feds_ring,
    add_fed, add_reed, add_router
)
import subprocess ,  os ,  signal
from datetime import datetime

CENTER_X, CENTER_Y = 400, 400


class LeaderElectionTest:
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
        self.ns.go(0.1)


    def check_topology_convergence(self):
        self.ns.go(0.1)


    def ScaleUP(self):pass

    def ScaleDown(self): pass

    def Closing(self):
        self.ns.close()
        print("\n\n\n⏱===End:",self.initial_devices,":",self.run_index)



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
