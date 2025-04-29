# metrics/_1leader_election_phase.py
from datetime import datetime


class LeaderElectionPhase:
    def __init__(self, ns , result_file):
        self.ns = ns
        self.result_file=result_file
        self.steps = [
            ("Step 1: Attach Status", self._1_wait_for_non_detached_nodes),
            ("Step 2: Single Leader", self._2_single_leader_verification),
            ("Step 3: Valid Roles", self._3_valid_roles),
            ("Step 4: RLOC16 Stability", self._4_rloc16_stability),
            ("Step 5: IPv6 Stability", self._5_ipv6_address_stability),
            ("Step 6: State Stability", self._6_state_stability),
            ("Step 7: Routing Silence", self._7_routing_message_silence),

        ]

    def run(self):
        for name, func in self.steps:
            print(f"# {name}")
            try:
                func()
            except AssertionError as e:
                print(f"^ {name} FAILED:", e)
                return False
        return True

    def _get_node_states(self):
        states = {}
        detached = []
        for node_id in self.ns.nodes().keys():
            state = self.ns.node_cmd(node_id, "state")[0].strip()
            states[node_id] = state
            if state in ["detached", "disabled"]:
                detached.append((node_id, state))
        return states, detached

    from datetime import datetime

    def _1_wait_for_non_detached_nodes(self, max_wait=1200, interval=1):
        # Write Step Title (only once at the start)
        self.result_file.write("\n========= [ 1. Leader Election Phase ] =========\n")
        self.result_file.write("Step 1: Attach Status Check\n")
        self.result_file.flush()

        start_time = datetime.now()  # <=== Start timing
        waited = 0

        while waited <= max_wait:
            self.ns.go(interval)
            states, detached_nodes = self._get_node_states()

            if not detached_nodes:
                print("! Step 1")
                end_time = datetime.now()  # <=== End timing
                duration = (end_time - start_time).total_seconds()

                self.result_file.write(f"\tDone: {duration:.6f}s\n--------------------------------------------\n")
                self.result_file.write("")
                self.result_file.flush()
                return

            waited += interval

        # If failure (after max_wait)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        fail_msg = f"Result: FAIL — Detached nodes after {max_wait}s: {detached_nodes}\n"
        self.result_file.write(fail_msg)
        self.result_file.write(f"\tTime Elapsed: {duration:.2f}s\n")
        self.result_file.write("--------------------------------------------\n")
        self.result_file.flush()
        raise AssertionError(fail_msg)

    def _2_single_leader_verification(self, max_wait=1200, interval=1):
        # Write Step Title (only once at the start)
        self.result_file.write("\nStep 2: Single Leader Verification\n")
        self.result_file.flush()

        waited = 0
        final_leader_line = ""  # Capture the final successful leader detection
        start_time = datetime.now()  # <=== Start timing

        while waited <= max_wait:
            self.ns.go(interval)
            states, _ = self._get_node_states()
            leader_nodes = [nid for nid, state in states.items() if state == "leader"]


            if len(leader_nodes) == 1:
                print(f"! Step 2  : Leader = {leader_nodes[0]}")

                end_time = datetime.now()  # <=== End timing
                duration = (end_time - start_time).total_seconds()

                self.result_file.write(f"\tDone: {duration:.6f}s\n--------------------------------------------\n")
                self.result_file.flush()
                return

            waited += interval

        # If failure (after max_wait), write a failure line
        fail_msg = f"Result: FAIL — Expected 1 leader, found {len(leader_nodes)} → {leader_nodes}\n"
        self.result_file.write(fail_msg)
        self.result_file.write("--------------------------------------------\n")
        self.result_file.flush()
        raise AssertionError(fail_msg)

    def _3_valid_roles(self, max_wait=1200, interval=1):
        # Write Step Title (only once at the start)
        self.result_file.write("\nStep 3: Valid Roles Across Nodes\n")
        self.result_file.flush()
        start_time = datetime.now()  # <=== Start timing

        waited = 0
        final_valid_roles_line = ""  # Capture the final successful valid state

        while waited <= max_wait:
            self.ns.go(interval)
            states, _ = self._get_node_states()
            invalid_nodes = [
                (nid, state) for nid, state in states.items()
                if state != "leader" and state not in ["router", "child"]
            ]



            if not invalid_nodes:
                print("! Step 3")

                end_time = datetime.now()  # <=== End timing
                duration = (end_time - start_time).total_seconds()

                self.result_file.write(f"\tDone: {duration:.6f}s\n--------------------------------------------\n")
                self.result_file.flush()
                return

            waited += interval

        # If failure (after max_wait), write a failure line
        fail_msg = f"Result: FAIL — Invalid roles found after {max_wait}s: {invalid_nodes}\n"
        self.result_file.write(fail_msg)
        self.result_file.write("--------------------------------------------\n")
        self.result_file.flush()
        raise AssertionError(fail_msg)

    def _4_rloc16_stability(self, delay=5, max_wait=1200, interval=1):
        # Write Step Title (only once at the start)
        self.result_file.write("\nStep 4: RLOC16 Stability\n")
        self.result_file.flush()
        start_time = datetime.now()  # <=== Start timing

        waited = 0
        final_rloc16_line = ""  # Capture the final stability line

        while waited <= max_wait:
            def capture():
                return {
                    nid: self.ns.node_cmd(nid, "rloc16")[0].strip()
                    for nid, state in self._get_node_states()[0].items()
                    if state in ["leader", "router"]
                }

            first = capture()
            self.ns.go(delay)
            second = capture()

            changed = [(nid, first[nid], second.get(nid, "missing")) for nid in first if
                       nid not in second or first[nid] != second[nid]]


            if not changed:
                print("! Step 4")

                end_time = datetime.now()  # <=== End timing
                duration = (end_time - start_time).total_seconds()

                self.result_file.write(f"\tDone: {duration:.6f}s\n--------------------------------------------\n")
                self.result_file.flush()
                return

            waited += interval

        # If failure (after max_wait), write a failure line
        fail_msg = f"Result: FAIL — RLOC16 changed after {max_wait}s: {changed}\n"
        self.result_file.write(fail_msg)
        self.result_file.write("--------------------------------------------\n")
        self.result_file.flush()
        raise AssertionError(fail_msg)

    def _5_ipv6_address_stability(self, delay=5, max_wait=1200, interval=1):
        # Write Step Title (only once at the start)
        start_time = datetime.now()  # <=== Start timing
        self.result_file.write("\nStep 5: IPv6 Address Stability\n")
        self.result_file.flush()

        waited = 0
        final_ipv6_line = ""  # Capture the final stability line

        while waited <= max_wait:
            def get_addrs():
                return {
                    nid: sorted(ip.strip() for ip in self.ns.node_cmd(nid, "ipaddr"))
                    for nid in self.ns.nodes()
                }

            before = get_addrs()
            self.ns.go(delay)
            after = get_addrs()

            changed = [
                {"node": nid, "before": before[nid], "after": after[nid]}
                for nid in before if before[nid] != after[nid]
            ]

            

            if not changed:
                print("! Step 5")

                end_time = datetime.now()  # <=== End timing
                duration = (end_time - start_time).total_seconds()

                self.result_file.write(f"\tDone: {duration:.6f}s\n--------------------------------------------\n")
                self.result_file.flush()
                return

            waited += interval

        # If failure (after max_wait), write a failure line
        fail_msg = f"Result: FAIL — IPv6 addresses changed after {max_wait}s: {changed}\n"
        self.result_file.write(fail_msg)
        self.result_file.write("--------------------------------------------\n")
        self.result_file.flush()
        raise AssertionError(fail_msg)

    def _6_state_stability(self, delay=5, max_wait=1200, interval=1):
        # Write Step Title (only once at the start)
        start_time = datetime.now()  # <=== Start timing
        self.result_file.write("\nStep 6: State Stability\n")
        self.result_file.flush()

        waited = 0
        final_state_line = ""  # Capture the final successful stability line

        while waited <= max_wait:
            def capture():
                return {
                    nid: self.ns.node_cmd(nid, "state")[0].strip()
                    for nid in self.ns.nodes()
                }

            first = capture()
            self.ns.go(delay)
            second = capture()

            changed = [
                {"node": nid, "before": first[nid], "after": second[nid]}
                for nid in first if first[nid] != second[nid]
            ]



            if not changed:
                print("! Step 6")

                end_time = datetime.now()  # <=== End timing
                duration = (end_time - start_time).total_seconds()

                self.result_file.write(f"\tDone: {duration:.6f}s\n--------------------------------------------\n")
                self.result_file.flush()
                return

            waited += interval

        # If failure (after max_wait), write a failure line
        fail_msg = f"Result: FAIL — State changed after {max_wait}s: {changed}\n"
        self.result_file.write(fail_msg)
        self.result_file.write("--------------------------------------------\n")
        self.result_file.flush()
        raise AssertionError(fail_msg)

    def _7_routing_message_silence(self, delay=5, max_wait=1200, interval=1):
        # Write Step Title (only once at the start)
        self.result_file.write("\nStep 7: Routing Message Silence\n")
        self.result_file.flush()
        start_time = datetime.now()  # <=== Start timing

        waited = 0

        while waited <= max_wait:
            def get_counters():
                result = {}
                for nid, state in self._get_node_states()[0].items():
                    if state not in ["leader", "router"]:
                        continue
                    counters = self.ns.node_cmd(nid, "counters")
                    dio = dao = 0
                    for line in counters:
                        if line.startswith("mpl.in"):
                            dio = int(line.split()[-1])
                        elif line.startswith("dao.sent"):
                            dao = int(line.split()[-1])
                    result[nid] = {"dio": dio, "dao": dao}
                return result

            before = get_counters()
            self.ns.go(delay)
            after = get_counters()

            changed = [
                {"node": nid, "before": before[nid], "after": after[nid]}
                for nid in before
                if after[nid]["dio"] > before[nid]["dio"] or after[nid]["dao"] > before[nid]["dao"]
            ]



            if not changed:
                print("! Step 7")
                end_time = datetime.now()  # <=== End timing
                duration = (end_time - start_time).total_seconds()

                self.result_file.write(f"\tDone: {duration:.9f}s\n--------------------------------------------\n")
                self.result_file.flush()
                return

            waited += interval

        # If failure (after max_wait), write a failure line
        fail_msg = f"Result: FAIL — Routing messages (DIO/DAO) increased after {max_wait}s: {changed}\n"
        self.result_file.write(fail_msg)
        self.result_file.write("--------------------------------------------\n")
        self.result_file.flush()
        raise AssertionError(fail_msg)
