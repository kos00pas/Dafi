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

from MyJob.my_functions import place_in_circle

scale_up_counter = 0  # Global variable to keep track of rounds

scale_up_counter = 0
scale_up_groups = []  # List of lists to track 10 node IDs per round

def scale_up(ns, spacing):
    global scale_up_counter, scale_up_groups

    print(f"🆙 Scaling up deterministically (round {scale_up_counter + 1})")
    offset = 5 * scale_up_counter
    center_x = CENTER_X + offset
    center_y = CENTER_Y + offset

    group_node_ids = []

    # Add Router
    router_id = add_router(ns, center_x, center_y, OT_CLI_ftd)
    group_node_ids.append(router_id)

    # Add REED
    reed_pos = place_in_circle(center_x, center_y, spacing / 2, 1)[0]
    reed_id = add_reed(ns, *reed_pos, OT_CLI_ftd)
    group_node_ids.append(reed_id)

    # Add FEDs
    fed_positions = place_in_circle(center_x, center_y, spacing * 3, 8)
    for x, y in fed_positions:
        fed_id = add_fed(ns, x, y, OT_CLI_ftd)
        group_node_ids.append(fed_id)

    scale_up_groups.append(group_node_ids)
    scale_up_counter += 1





def dynamic_scaling(ns, current_total, step, max_total, spacing):
        """
        Incrementally adds `step` devices per round until reaching `max_total`.
        Each round places:
         - 1 Router at the center
         - 1 REED in a deterministic half-radius position
         - 8 FEDs in deterministic full-radius circle
        """
        rounds = 0
        while current_total < max_total:
            print(f"\n🔁 Scaling network to {current_total + step} nodes...")
            scale_up(ns, spacing=spacing)

            if wait_for_network_convergence(ns):
                print(f"✅ Converged at {current_total + step} nodes.")
                initiate_coap_announcement(ns)
            else:
                print("⚠️ Some nodes failed to join after scale-up.")

            current_total += step
            rounds += 1
        return rounds
def scale_down(ns):
    global scale_up_groups
    if not scale_up_groups:
        print("🚫 No more nodes to scale down.")
        return

    last_group = scale_up_groups.pop()
    print(f"🔽 Scaling down: removing {len(last_group)} nodes...")
    ns.delete(*last_group)

def dynamic_scaling_down(ns, rounds, spacing):
    """
    Symmetrically remove the previously added nodes, one group at a time.
    """
    print(f"\n🔁 Starting dynamic scale-down over {rounds} rounds...")
    for i in range(rounds):
        print(f"🔽 Scale-down round {i + 1}/{rounds}")
        scale_down(ns)

        # Let network rebalance
        if wait_for_network_convergence(ns):
            print("✅ Converged after scale-down.")
            initiate_coap_announcement(ns)
        else:
            print("⚠️ Some nodes failed to re-converge after removal.")

        ns.go(10)


def run_baseline_simulation():
    ns = OTNS(otns_path=OTNS_PATH, otns_args=["-log", "debug"])
    ns.set_title("DAfI - Scalable Mesh Network")
    ns.set_network_info(version="Latest", commit="main", real=False)
    ns.web()
    ns.speed = 101

    total_devices = 10
    spacing = 25

    print("⏱ Starting full simulation...")
    sim_start = datetime.now()

    # Step 1: Baseline setup
    configure_initial_topology(ns, total_devices=total_devices, spacing=spacing)

    start_baseline = datetime.now()
    if wait_for_network_convergence(ns):
        print("✅ Baseline converged.")
        initiate_coap_announcement(ns)
    end_baseline = datetime.now()

    ns.go(10)  # ⏱ Let baseline network run 10 seconds (steady state)

    # Step 2: Scale up
    print("\n⏱ Starting scaling up...")
    start_up = datetime.now()
    scale_rounds = dynamic_scaling(ns, current_total=total_devices, step=10, max_total=510, spacing=spacing)
    ns.go(30)  # ⏱ Post-scale-up steady state
    end_up = datetime.now()

    # Step 3: Scale down
    print("\n⏱ Starting scaling down...")
    start_down = datetime.now()
    dynamic_scaling_down(ns, rounds=scale_rounds, spacing=spacing)
    end_down = datetime.now()

    sim_end = datetime.now()

    # === Summary Report ===
    print("\n========== 📊 SIMULATION TIME SUMMARY ==========")
    print(f"🧱 Baseline convergence time      : {end_baseline - start_baseline}")
    print(f"📈 Scale-up phase duration        : {end_up - start_up}")
    print(f"📉 Scale-down phase duration      : {end_down - start_down}")
    print(f"🕒 TOTAL simulation time (wall)   : {sim_end - sim_start}")
    print("===============================================")




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
