OT_CLI_ftd = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
OTNS_PATH = "/home/otns/go/bin/otns"
from otns.cli.errors import OTNSExitedError
import os, time, shutil, socket, sys
from Experiment import Experiment , kill_otns_port
import errno





def cleanup_after_experiment(folder_path):
    # log_handle.close()
    sys.stdout = sys.__stdout__

    if hasattr(os, 'sync'):
        os.sync()
    # time.sleep(3)
    port = 9000
    timeout = 10
    for waited in range(timeout):
        try:
            with socket.create_connection(('localhost', port), timeout=1):
                # Port is in use
                print("⏳ Waiting for OTNS_ port to become available...")
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                # Port is free
                break
        time.sleep(0.5)

    # time.sleep(5)
    pcap_dst = os.path.join(folder_path, "capture.pcap")
    replay_dst = os.path.join(folder_path, "replay.otns")

    saved = []
    for src, dst in [("current.pcap", pcap_dst), ("otns_0.replay", replay_dst)]:
        if os.path.exists(src):
            shutil.move(src, dst)
            saved.append(dst)

    if saved:
        print("$ Saved:", ", ".join(saved))

    for f in ["current.pcap", "otns_0.replay"]:
        try:
            if os.path.exists(f):
                os.remove(f)
                print(f"$ Removed leftover: {f}")
        except Exception as e:
            print(f"* Could not remove {f}: {e}")

    try:
        if os.path.exists("tmp"):
            shutil.rmtree("tmp")
            print("$ Cleaned up tmp/ directory.")
    except Exception as e:
        print(f"* Failed to remove tmp/: {e}")

def run_single_experiment(dev_count, run_index, log_files):
    folder_path = os.path.join(str(dev_count), str(run_index))
    if os.path.isfile(folder_path):
        os.remove(folder_path)
    os.makedirs(folder_path, exist_ok=True)

    # log_file = os.path.join(folder_path, f"mylogs_{dev_count}_{run_index}.log")
    # log_files.append(log_file)

    kill_otns_port(9000)
    # log_handle = start_log(filename=log_file)
    # test = LeaderElectionTest(initial_devices=dev_count, log_file=log_file, run_index=run_index)
    Experiment(initial_devices=dev_count, run_index=run_index)

    # continue cleanup after experiment
    cleanup_after_experiment(folder_path)


if __name__ == '__main__':
    try:
        log_files = []
        device_configs = [200]
        # device_configs = [10,11]
        # device_configs = [10, 25, 40, 80, 150, 250, 350, 450, 500]
        # runs_per_config = 5
        runs_per_config = 1

        for dev_count in device_configs:
            for run_index in range(1, runs_per_config + 1):
                run_single_experiment(dev_count, run_index, log_files)


    except OTNSExitedError as ex:
        if ex.exit_code != 0:
            raise

# http://localhost:8997/visualize?addr=localhost:8998
