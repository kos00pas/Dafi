from otns import OTNS
from otns import OTNSExitedError

import my_functions
OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OT_CLI_mtd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OT_CLI_radio = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"  # ✅ full path to your built OTNS






def main():
    ns = OTNS(
        otns_path=OTNS_PATH,  # 👈 fixed here
        otns_args=["-log", "debug"]
    )
    ns.set_title("Simple Example")
    ns.set_network_info(version="Latest", commit="main", real=False)
    ns.web()
    ns.speed= 10  # 🔁 Speed up simulation by 10x

    ns.add("router", x=300, y=300, executable=OT_CLI_ftd)
    ns.add("router", x=200, y=300, executable=OT_CLI_ftd)
    ns.add("fed",    x=300, y=200, executable=OT_CLI_ftd)
    ns.add("med",    x=400, y=300, executable=OT_CLI_ftd)
    ns.add("sed",    x=300, y=400, executable=OT_CLI_ftd)

    ns.go()

if __name__ == '__main__':
    try:
        my_functions.kill_otns_port(9000)  # 👈 Kill any leftover OTNS process
        main()
    except OTNSExitedError as ex:
        if ex.exit_code != 0:
            raise

