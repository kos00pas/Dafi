from otns import OTNS
from otns import OTNSExitedError

OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OT_CLI_mtd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OT_CLI_radio = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"  # ✅ full path to your built OTNS


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



def main():
    ns = OTNS(
        otns_path=OTNS_PATH,  # 👈 fixed here
        otns_args=["-log", "debug"]
    )
    ns.set_title("Simple Example")
    ns.set_network_info(version="Latest", commit="main", real=False)
    ns.web()
    ns.speed=30
    ns.add("router", x=300, y=300, executable=OT_CLI_ftd)
    ns.add("router", x=200, y=300, executable=OT_CLI_ftd)
    ns.add("fed",    x=300, y=200, executable=OT_CLI_ftd)
    ns.add("med",    x=400, y=300, executable=OT_CLI_ftd)
    ns.add("sed",    x=300, y=400, executable=OT_CLI_ftd)

    ns.go()

if __name__ == '__main__':
    try:
        kill_otns_port(9000)  # 👈 Kill any leftover OTNS process
        main()
    except OTNSExitedError as ex:
        if ex.exit_code != 0:
            raise

