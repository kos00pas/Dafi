# === Imports ===
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


# === Constants ===
OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"
CENTER_X, CENTER_Y = 400, 400


# === Core Functions ===
def configure_initial_topology(ns, total_devices, spacing):
    routers, reeds, feds = calculate_device_roles(total_devices)
    routers -= 1  # Reserve 1 for leader

    place_leader(ns, CENTER_X, CENTER_Y, OT_CLI_ftd, add_router)
    place_routers_cross(ns, CENTER_X, CENTER_Y, routers, spacing, OT_CLI_ftd, add_router)
    place_reeds_diagonal_and_ring(ns, CENTER_X, CENTER_Y, reeds, spacing, OT_CLI_ftd, add_reed)
    place_feds_ring(ns, CENTER_X, CENTER_Y, feds, spacing * 3, OT_CLI_ftd, add_fed)


def wait_for_network_convergence(ns, max_wait=120, interval=2):
    waited = 0
    while waited < max_wait:
        all_joined = all(
            ns.node_cmd(node_id, "state")[0].strip() != "detached"
            for node_id in ns.nodes()
        )
        if all_joined:
            return True
        ns.go(interval)
        waited += interval
    return False


from MyJob.my_functions import place_in_circle

from MyJob.my_functions import place_in_circle

def scale_up(ns, spacing):
    print("🆙 Scaling up deterministically")

    # Center router
    add_router(ns, CENTER_X, CENTER_Y, OT_CLI_ftd)

    # One REED in half-radius
    reed_pos = place_in_circle(CENTER_X, CENTER_Y, spacing / 2, 1)[0]
    add_reed(ns, *reed_pos, OT_CLI_ftd)

    # 8 FEDs in full-radius
    fed_positions = place_in_circle(CENTER_X-10, CENTER_Y-10, spacing* 3, 8)
    for x, y in fed_positions:
        add_fed(ns, x, y, OT_CLI_ftd)



def dynamic_scaling(ns, current_total, step, max_total, spacing):
    """
    Incrementally adds `step` devices per round until reaching `max_total`.
    Each round places:
      - 1 Router at the center
      - 1 REED in a deterministic half-radius position
      - 8 FEDs in deterministic full-radius circle
    """
    while current_total < max_total:
        print(f"\n🔁 Scaling network to {current_total + step} nodes...")

        scale_up(ns, spacing=spacing)  # adds 10 new nodes

        if wait_for_network_convergence(ns):
            print(f"✅ Converged at {current_total + step} nodes.")
            initiate_coap_announcement(ns)
        else:
            print("⚠️ Some nodes failed to join after scale-up.")

        current_total += step


def run_baseline_simulation():
    ns = OTNS(otns_path=OTNS_PATH, otns_args=["-log", "debug"])
    ns.set_title("DAfI - Scalable Mesh Network")
    ns.set_network_info(version="Latest", commit="main", real=False)
    ns.web()
    ns.speed = 101
    total_devices = 10
    spacing = 25
    configure_initial_topology(ns, total_devices=total_devices, spacing=spacing)

    if wait_for_network_convergence(ns):
        print("✅ Baseline converged.")
        initiate_coap_announcement(ns)

    ns.go(10)  # simulate initial stability
    dynamic_scaling(ns, current_total=total_devices, step=10, max_total=510, spacing=spacing)

    ns.go()  # let it run


# === Entrypoint ===
if __name__ == '__main__':
    try:
        kill_otns_port(9000)
        start_log()
        run_baseline_simulation()
    except OTNSExitedError as ex:
        if ex.exit_code != 0:
            raise


# http://localhost:8997/visualize?addr=localhost:8998
