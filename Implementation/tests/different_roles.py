from otns.cli import OTNS
from otns.cli.errors import OTNSExitedError
from my_functions import *

# Set paths to executables
OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"  # Adjust if different


def add_fed(ns, x, y, exe):
    node = ns.add("router", x=x, y=y, executable=exe)
    ns.set_router_upgrade_threshold(node, 99)
    ns.set_router_downgrade_threshold(node, 1)
    ns.node_cmd(node, "mode rn")  # ✅ FIXED: no 's'
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
    ns.speed = 10  # Faster simulation

    # === Configuration ===
    TOTAL_DEVICES = 80
    center_x, center_y = 300, 300
    spacing = 70

    # === Calculate Role Counts ===
    routers, reeds, feds = calculate_device_roles(TOTAL_DEVICES)
    routers_remaining = routers - 1  # 1 is used for Leader

    # === Add Leader (center) ===
    add_router(ns, center_x, center_y, OT_CLI_ftd)

    # === Add Routers (cross-style) ===
    router_directions = [
        (0, -spacing),  # Up
        (-spacing, 0),  # Left
        (spacing, 0),  # Right
        (0, spacing),  # Down
        (-spacing, -spacing),  # Diagonals if needed
        (spacing, -spacing),
        (-spacing, spacing),
        (spacing, spacing)
    ]
    for i in range(min(routers_remaining, len(router_directions))):
        dx, dy = router_directions[i]
        add_router(ns, center_x + dx, center_y + dy, OT_CLI_ftd)

    # === Add REEDs ===
    # Diagonal REEDs (× shape)
    reed_spacing = int(spacing * 1.5)
    reed_directions = [
        (-reed_spacing, -reed_spacing),
        (reed_spacing, -reed_spacing),
        (-reed_spacing, reed_spacing),
        (reed_spacing, reed_spacing)
    ]
    for i in range(min(reeds, len(reed_directions))):
        dx, dy = reed_directions[i]
        add_reed(ns, center_x + dx, center_y + dy, OT_CLI_ftd)

    # Remaining REEDs in a small ring
    remaining_reeds = reeds - min(reeds, len(reed_directions))
    if remaining_reeds > 0:
        reed_ring_radius = int(spacing * 2.2)
        reed_ring_positions = place_in_circle(center_x, center_y, reed_ring_radius, remaining_reeds)
        for x, y in reed_ring_positions:
            add_reed(ns, x, y, OT_CLI_ftd)

    # === Add FEDs (outer ring) ===
    fed_radius = spacing * 3
    fed_positions = place_in_circle(center_x, center_y, fed_radius, feds)
    for x, y in fed_positions:
        add_fed(ns, x, y, OT_CLI_ftd)

    ns.go()


if __name__ == '__main__':
    try:
        kill_otns_port(9000)  # 👈 Kill any leftover OTNS process
        main()
    except OTNSExitedError as ex:
        if ex.exit_code != 0:
            raise
