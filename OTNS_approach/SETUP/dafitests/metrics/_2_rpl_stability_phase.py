# metrics/_2_rpl_stability_phase.py
from datetime import datetime

from OTNS_approach.SETUP.dafitests.otns.cli.OTNS import now

import time

class RPLStabilityPhase:
    def __init__(self, ns,result_file):
        self.ns = ns
        self.result_file = result_file

    def run(self):
        print("\n🚀 Starting RPL Stability Phase (Steps 12-13)...\n")
        self._12_route_table_snapshot_stability()
        self._13_dio_dao_decay_time()
        print("\n✅ RPL Stability Phase completed successfully!\n")
        return True

    from datetime import datetime

    def _12_route_table_snapshot_stability(self, snapshot_interval=10, total_duration=120):
        self.result_file.write("\n========= [ 2. Route Table Snapshot Stability ] =========\n")
        self.result_file.write("Step 12: Route Table Snapshot Stability\n")
        self.result_file.flush()

        print("\n📖 Step 12: Route Table Snapshot Stability\n")
        start_time = datetime.now()

        def clean_router_table(raw_table):
            cleaned = []
            for line in raw_table:
                if "|" in line and "RLOC16" not in line and "+" not in line:
                    parts = line.split("|")
                    cleaned.append("|".join([
                        parts[1].strip(),  # Router ID
                        parts[2].strip(),  # RLOC16
                        parts[3].strip(),  # Next Hop
                        parts[8].strip()  # Extended MAC
                    ]))
            return cleaned

        snapshots = []
        timestamps = []

        rounds = total_duration // snapshot_interval
        for r in range(rounds):
            snapshot = {
                nid: clean_router_table(self.ns.node_cmd(nid, "router table"))
                for nid in self.ns.nodes().keys()
            }
            snapshots.append(snapshot)
            timestamps.append(now())

            print(f"Snapshot {r}: Captured at t={timestamps[-1]}")
            self.ns.go(snapshot_interval)

        # Compare snapshots
        reference = snapshots[0]
        for idx, snap in enumerate(snapshots[1:], start=1):
            for nid in reference:
                if reference[nid] != snap.get(nid, []):
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    fail_msg = f"Result: FAIL — Route table changed at node {nid} between snapshot 0 and snapshot {idx}\n"
                    self.result_file.write(fail_msg)
                    self.result_file.write(
                        f"\tTime Elapsed: {duration:.2f}s\n--------------------------------------------\n")
                    self.result_file.write("")
                    self.result_file.flush()
                    raise AssertionError(f"Step 12 FAILED: Route table instability detected at node {nid}")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print("\n✅ Step 12: Route Tables remained stable across snapshots!\n")

        self.result_file.write(f"\tDone: {duration:.9f}s\n--------------------------------------------\n")
        self.result_file.write("")
        self.result_file.flush()
    from datetime import datetime

    def _13_dio_dao_decay_time(self, check_interval=5, max_wait=300):
        self.result_file.write("Step 13: DIO/DAO Message Decay Time\n")
        self.result_file.flush()

        print("\n📖 Step 13: DIO/DAO Message Decay Time\n")
        start_time = datetime.now()  # Start timing

        def get_counters():
            counters = {}
            for nid in self.ns.nodes().keys():
                if self._get_node_state(nid) not in ["leader", "router"]:
                    continue
                ctrs = self.ns.node_cmd(nid, "counters")
                dio = dao = 0
                for line in ctrs:
                    if line.startswith("mpl.in"):
                        dio = int(line.split()[-1])
                    elif line.startswith("dao.sent"):
                        dao = int(line.split()[-1])
                counters[nid] = {"dio": dio, "dao": dao}
            return counters

        initial = get_counters()
        waited = 0

        while waited <= max_wait:
            self.ns.go(check_interval)
            current = get_counters()

            delta = []
            for nid in initial:
                if (current[nid]["dio"] > initial[nid]["dio"] or
                        current[nid]["dao"] > initial[nid]["dao"]):
                    delta.append(nid)

            if not delta:
                print(f"\n✅ Step 13: No new DIO/DAO messages after {waited} seconds.")
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                self.result_file.write(f"\tDone: {duration:.9f}s")
                self.result_file.write("")
                self.result_file.flush()
                exit()
                return

            print(f"@ {waited:>3}s | Active DIO/DAO detected on nodes: {delta}")
            initial = current
            waited += check_interval

        # If failure
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        fail_msg = "Result: FAIL — DIO/DAO did not fully decay within expected time.\n"
        self.result_file.write(fail_msg)
        self.result_file.write(f"\tTime Elapsed: {duration:.2f}s\n--------------------------------------------\n")
        self.result_file.write("")
        self.result_file.flush()
        raise AssertionError("^Step 13 FAILED: DIO/DAO did not fully decay within expected time.")

    def _get_node_state(self, nid):
        return self.ns.node_cmd(nid, "state")[0].strip()
