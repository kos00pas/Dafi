
import subprocess
import os
import signal

def kill_otns_port(port=9000):
    try:
        result = subprocess.check_output(f"lsof -t -i :{port}", shell=True).decode().strip()
        if result:
            print(f"Killing existing OTNS process on port {port}: PID(s) {result}")
            for pid in result.splitlines():
                os.kill(int(pid), signal.SIGKILL)
    except subprocess.CalledProcessError:
        pass  # No process found, it's OK

import math

def calculate_device_roles(total_devices):
    routers = min(math.ceil(total_devices * 0.1), 32)
    reeds = routers
    feds = total_devices - routers - reeds
    print(routers, reeds, feds)
    # exit()
    if feds < 0:
        raise ValueError("Not enough devices for proper role balance.")
    return routers, reeds, feds

def place_in_circle(center_x, center_y, radius, count):
    """Returns integer (x, y) coordinates evenly spaced in a circle."""
    return [
        (
            int(center_x + radius * math.cos(2 * math.pi * i / count)),
            int(center_y + radius * math.sin(2 * math.pi * i / count)),
        )
        for i in range(count)
    ]

def radius_by_count(count, base_spacing=2):
        return int(base_spacing * math.sqrt(count))  # grows gently with node count

def place_leader(ns, x, y, exe, add_router):
    add_router(ns, x, y, exe)


def place_routers_cross(ns, center_x, center_y, count, spacing, exe, add_router):
    router_directions = [
        (0, -spacing),
        (-spacing, 0),
        (spacing, 0),
        (0, spacing),
        (-spacing, -spacing),
        (spacing, -spacing),
        (-spacing, spacing),
        (spacing, spacing),
    ]
    for dx, dy in router_directions[:count]:
        add_router(ns, center_x + dx, center_y + dy, exe)


def place_reeds_diagonal_and_ring(ns, center_x, center_y, count, spacing, exe, add_reed):
    reed_spacing = int(spacing * 1.5)
    reed_directions = [
        (-reed_spacing, -reed_spacing),
        (reed_spacing, -reed_spacing),
        (-reed_spacing, reed_spacing),
        (reed_spacing, reed_spacing),
    ]
    for i in range(min(count, len(reed_directions))):
        dx, dy = reed_directions[i]
        add_reed(ns, center_x + dx, center_y + dy, exe)

    remaining = count - min(count, len(reed_directions))
    if remaining > 0:
        radius = int(spacing * 2.2)
        positions = place_in_circle(center_x, center_y, radius, remaining)
        for x, y in positions:
            add_reed(ns, x, y, exe)


def place_feds_ring(ns, center_x, center_y, count, radius, exe, add_fed):
    positions = place_in_circle(center_x, center_y, radius, count)
    for x, y in positions:
        add_fed(ns, x, y, exe)



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





