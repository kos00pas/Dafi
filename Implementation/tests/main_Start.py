from datetime import datetime

real_start = None

from otns.cli import OTNS
from otns.cli.errors import OTNSExitedError
from MyJob.my_functions import (
    kill_otns_port,
    calculate_device_roles,
    place_leader,
    place_routers_cross,
    place_reeds_diagonal_and_ring,
    place_feds_ring
)
from MyJob.communication import (
initiate_coap_announcement
)

from MyJob.nodes import (
add_fed,
add_reed,
add_router
)

from  MyJob.logging import (start_log)

# Set paths to executables
OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"  # Adjust if different



def configuration(ns,TOTAL_DEVICES):
    # === Configuration ===
    center_x, center_y = 400, 400  # centering in my small monitor
    spacing = 50  # < 45 to be okay in all architectures

    # === Role Calculation ===
    routers, reeds, feds = calculate_device_roles(TOTAL_DEVICES)
    routers_remaining = routers - 1  # 1 router used for Leader

    # === Placement ===
    place_leader(ns, center_x, center_y, OT_CLI_ftd, add_router)
    place_routers_cross(ns, center_x, center_y, routers_remaining, spacing, OT_CLI_ftd, add_router)
    place_reeds_diagonal_and_ring(ns, center_x, center_y, reeds, spacing, OT_CLI_ftd, add_reed)
    fed_radius = spacing * 3
    place_feds_ring(ns, center_x, center_y, feds, fed_radius, OT_CLI_ftd, add_fed)
    # print("=============================================================")
    # === Run Simulation ===


def wait_for_network_convergence(ns, max_wait=120, interval=2):
    """
    Blocks until all nodes have joined the mesh (i.e., are not 'detached').
    Times out after `max_wait` seconds.
    """
    # print("\n⏳ Waiting for all nodes to join the mesh...")
    waited = 0
    while waited < max_wait:
        all_joined = True
        for node_id in ns.nodes():
            try:
                state = ns.node_cmd(node_id, "state")[0].strip()  # FIXED: Use .node_cmd
                if state == "detached":
                    all_joined = False
                    # print(f"🔸 Node {node_id} still detached.")
                    break
            except Exception as e:
                # print(f"❌ Error checking node {node_id}: {e}")
                all_joined = False
                break
        if all_joined:
            # print("ALL_JOINED_MY_MESHHH:", ns.sim_time())
            # exit()
            print(f"✅ All nodes joined the mesh.\n")
            # print("******************************************************")
            return True
        ns.go(interval)
        waited += interval
    # print("⚠️ Timeout: Some nodes did not join the mesh.")
    return False




def Baseline():
    ns = OTNS(
        otns_path=OTNS_PATH,
        otns_args=["-log", "debug"]
    )
    ns.set_title("DAfI - Role Configured Topology")
    real_start = datetime.now()

    ns.set_network_info(version="Latest", commit="main", real=False)
    ns.web()
    ns.speed = 101
    TOTAL_DEVICES = 10# 510 max
    configuration(ns,TOTAL_DEVICES)
    if wait_for_network_convergence(ns):
        # print("Ready to initiate communication.")
        # print("Current nodes:", ns.nodes())  # Check if nodes exist here
        initiate_coap_announcement(ns)

    else:
        pass
        # print("Network not fully converged. Continuing anyway...")
    ns.go()

def ScaleUP():
    pass


if __name__ == '__main__':
    try:
        kill_otns_port(9000)
        start_log()
        Baseline()
        ScaleUP()
    except OTNSExitedError as ex:
        if ex.exit_code != 0:
            raise

# http://localhost:8997/visualize?addr=localhost:8998
