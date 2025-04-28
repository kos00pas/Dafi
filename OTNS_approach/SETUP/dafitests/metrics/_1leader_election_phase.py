# metrics/_1leader_election_phase.py

class LeaderElectionPhase:
    def __init__(self, ns):
        self.ns = ns
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

    def _1_wait_for_non_detached_nodes(self, max_wait=1200, interval=1):
        waited = 0
        while waited <= max_wait:
            self.ns.go(interval)
            states, detached_nodes = self._get_node_states()
            print(f"@ {waited:>2}s | " + " ".join(f"{nid}:{state}" for nid, state in states.items()))
            if not detached_nodes:
                print("! Step 1")
                return
            waited += interval
        raise AssertionError(f"^Step 1 FAILED: Detached nodes after {max_wait}s → {detached_nodes}")

    def _2_single_leader_verification(self, max_wait=1200, interval=1):
        waited = 0
        while waited <= max_wait:
            self.ns.go(interval)
            states, _ = self._get_node_states()
            leader_nodes = [nid for nid, state in states.items() if state == "leader"]
            print(f"@ {waited:>2}s | Leaders found: {leader_nodes}")
            if len(leader_nodes) == 1:
                print(f"! Step 2  : Leader = {leader_nodes[0]}")
                return
            waited += interval
        raise AssertionError(f"^Step 2 FAILED: Expected 1 leader, found {len(leader_nodes)} → {leader_nodes}")

    def _3_valid_roles(self, max_wait=1200, interval=1):
        waited = 0
        while waited <= max_wait:
            self.ns.go(interval)
            states, _ = self._get_node_states()
            invalid_nodes = [
                (nid, state) for nid, state in states.items()
                if state != "leader" and state not in ["router", "child"]
            ]
            print(f"@ {waited:>2}s | Invalids: {invalid_nodes}")
            if not invalid_nodes:
                print("! Step 3")
                return
            waited += interval
        raise AssertionError(f"^Step 3 FAILED: Invalid roles → {invalid_nodes}")

    def _4_rloc16_stability(self, delay=5, max_wait=1200, interval=1):
        waited = 0
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
            # changed = [(nid, first[nid], second[nid]) for nid in first if first[nid] != second[nid]]
            changed = [(nid, first[nid], second.get(nid, "missing")) for nid in first if
                       nid not in second or first[nid] != second[nid]]
            print(f"@ {waited:>2}s | Changed: {changed}")
            if not changed:
                print("! Step 4")
                return
            waited += interval
        raise AssertionError(f"^Step 4 FAILED: RLOC16 changed → {changed}")

    def _5_ipv6_address_stability(self, delay=5, max_wait=1200, interval=1):
        waited = 0
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
            print(f"@ {waited:>2}s | Changed: {changed}")
            if not changed:
                print("! Step 5")
                return
            waited += interval
        raise AssertionError(f"^Step 5 FAILED: IPv6 addresses changed → {changed}")

    def _6_state_stability(self, delay=5, max_wait=1200, interval=1):
        waited = 0
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
            print(f"@ {waited:>2}s | Changed: {changed}")
            if not changed:
                print("! Step 6")
                return
            waited += interval
        raise AssertionError(f"^Step 6 FAILED: State changed → {changed}")

    def _7_routing_message_silence(self, delay=5, max_wait=1200, interval=1):
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
            print(f"@ {waited:>2}s | DIO/DAO changed: {changed}")
            if not changed:
                print("! Step 7")
                return
            waited += interval
        raise AssertionError(f"^Step 7 FAILED: DIO/DAO increase → {changed}")