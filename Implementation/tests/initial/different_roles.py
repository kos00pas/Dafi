from otns.cli import OTNS
from otns.cli.errors import OTNSExitedError
from my_functions import (
    kill_otns_port,
    calculate_device_roles,
    place_in_circle,
    place_leader,
    place_routers_cross,
    place_reeds_diagonal_and_ring,
    place_feds_ring
)

# Set paths to executables
OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"  # Adjust if different


# === Device Role Logic ===
def add_fed(ns, x, y, exe):
    node = ns.add("router", x=x, y=y, executable=exe)
    ns.set_router_upgrade_threshold(node, 99)
    ns.set_router_downgrade_threshold(node, 1)
    ns.node_cmd(node, "mode rn")
    return node

def add_reed(ns, x, y, exe):
    node = ns.add("router", x=x, y=y, executable=exe)
    ns.node_cmd(node, "mode rdn")
    return node

def add_router(ns, x, y, exe):
    node = ns.add("router", x=x, y=y, executable=exe)
    ns.node_cmd(node, "mode rdn")
    ns.node_cmd(node, "routerselectionjitter 1")
    return node


def main():
    ns = OTNS(
        otns_path=OTNS_PATH,
        otns_args=["-log", "debug"]
    )
    ns.set_title("DAfI - Role Configured Topology")
    ns.set_network_info(version="Latest", commit="main", real=False)
    ns.web()
    ns.speed = 10

    # === Configuration ===
    TOTAL_DEVICES = 510 # 510 max
    center_x, center_y = 300, 300 # centering in my small monitor
    spacing = 45 # to be okay in all architectures

    # === Role Calculation ===
    routers, reeds, feds = calculate_device_roles(TOTAL_DEVICES)
    routers_remaining = routers - 1  # 1 router used for Leader

    # === Placement ===
    place_leader(ns, center_x, center_y, OT_CLI_ftd, add_router)
    place_routers_cross(ns, center_x, center_y, routers_remaining, spacing, OT_CLI_ftd, add_router)
    place_reeds_diagonal_and_ring(ns, center_x, center_y, reeds, spacing, OT_CLI_ftd, add_reed)
    fed_radius = spacing * 3
    place_feds_ring(ns, center_x, center_y, feds, fed_radius, OT_CLI_ftd, add_fed)

    # === Run Simulation ===
    ns.go()


if __name__ == '__main__':
    try:
        kill_otns_port(9000)
        main()
    except OTNSExitedError as ex:
        if ex.exit_code != 0:
            raise
