OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"
from otns.cli import OTNS
from otns.cli.errors import OTNSExitedError

class LeaderElectionTest:
    def __init__(self, initial_devices=10, spacing=25, log_file="mylogs.log",run_index=0):
        self.run_index=run_index
        self.initial_devices = initial_devices
        self.spacing = spacing
        self.log_file = log_file
        # -----------------------------------
        self.Setup()
        self.Baseline()
        self.Converge()
        # self.ScaleUP()
        # self.ScaleDown()
        self.Closing()



    def Setup(self):
        self.ns = OTNS(otns_path=OTNS_PATH)  # , otns_args=["-log", "debug"]

    def Baseline(self):
        pass

    def Converge(self):
        pass

    def ScaleUP(self):
        pass

    def ScaleDown(self):
        pass

    def Closing(self):
        pass
