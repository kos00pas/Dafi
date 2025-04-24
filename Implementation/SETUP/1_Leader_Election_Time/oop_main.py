OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"
from otns.cli import OTNS
from otns.cli.errors import OTNSExitedError
CENTER_X, CENTER_Y = 400, 400
import os, time, shutil, socket, sys
from LeaderElectionTest import LeaderElectionTest













def run_single_experiment(dev_count, run_index, log_files):

    # Create the dir of experiment
    # Kill previous communication
    # Experiment
    # Results
    # Ensure OTNS port is available again
    # cleanup:  replay , pcap , tmp


    pass

if __name__ == '__main__':
    try:
        log_files = []
        device_configs = [10]
        # device_configs = [10, 25, 40, 80, 150, 250, 350, 450, 500]
        # runs_per_config = 5
        runs_per_config = 1

        for dev_count in device_configs:
            for run_index in range(1, runs_per_config + 1):
                run_single_experiment(dev_count, run_index, log_files)

        time.sleep(5)

    except OTNSExitedError as ex:
        if ex.exit_code != 0:
            raise