
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

kill_otns_port()