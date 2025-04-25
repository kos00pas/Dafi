# metrics/topology_convergence_phase.py

class TopologyConvergencePhase:
    def __init__(self, ns):
        self.ns = ns
        self.steps = [
            ("Step 8: Neighbor Table Stability", self._8_neighbor_table_stability),
            ("Step 9: Router Table Stability", self._9_router_table_stability),
            ("Step 10: Prefix & Route Propagation", self._10_prefix_route_stability),
            # ("Step 11: End-to-End Reachability", self._11_end_to_end_ping)
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

    def _8_neighbor_table_stability(self, delay=5, max_wait=120, interval=2):
        waited = 0

        def clean_neighbor_table(raw_table):
            cleaned = []
            for line in raw_table:
                if "|" in line and "Role" not in line and "+" not in line:
                    parts = line.split("|")
                    # Keep only Role, RLOC16, R, D, N, Extended MAC, Version
                    cleaned.append("|".join([
                        parts[1].strip(),  # Role
                        parts[2].strip(),  # RLOC16
                        parts[6].strip(),  # R
                        parts[7].strip(),  # D
                        parts[8].strip(),  # N
                        parts[9].strip(),  # Extended MAC
                        parts[10].strip()  # Version
                    ]))
            return cleaned

        def capture():
            return {
                nid: clean_neighbor_table(self.ns.node_cmd(nid, "neighbor table"))
                for nid, state in self._get_node_states()[0].items()
                if state in ["leader", "router"]
            }

        while waited <= max_wait:
            first = capture()
            self.ns.go(delay)
            second = capture()
            changed = {
                nid: (first[nid], second[nid])
                for nid in first if first[nid] != second[nid]
            }
            print(f"@ {waited:>2}s | Changed: {changed}")
            if not changed:
                print("! Step 8")
                return
            waited += interval
        raise AssertionError(f"^Step 8 FAILED: Neighbor tables changed → {changed}")

    def _9_router_table_stability(self, delay=5, max_wait=120, interval=2):
        waited = 0

        def clean_router_table(raw_table):
            cleaned = []
            for line in raw_table:
                if "|" in line and "RLOC16" not in line and "+" not in line:
                    parts = line.split("|")
                    # Keep only Router ID, RLOC16, Next Hop, Extended MAC (ignore LQI and Age)
                    cleaned.append("|".join([
                        parts[1].strip(),  # Router ID
                        parts[2].strip(),  # RLOC16
                        parts[3].strip(),  # Next Hop
                        parts[8].strip()  # Extended MAC (or Version, depending on format)
                    ]))
            return cleaned

        def capture():
            return {
                nid: clean_router_table(self.ns.node_cmd(nid, "router table"))
                for nid, state in self._get_node_states()[0].items()
                if state in ["leader", "router"]
            }

        while waited <= max_wait:
            first = capture()
            self.ns.go(delay)
            second = capture()
            changed = {
                nid: (first[nid], second[nid])
                for nid in first if first[nid] != second[nid]
            }
            print(f"@ {waited:>2}s | Changed: {changed}")
            if not changed:
                print("! Step 9")
                return
            waited += interval

        raise AssertionError(f"^Step 9 FAILED: Router tables changed → {changed}")

    def _10_prefix_route_stability(self, delay=5, max_wait=120, interval=2):
        waited = 0
        def capture():
            return {
                nid: self.ns.node_cmd(nid, "netdata show")
                for nid, state in self._get_node_states()[0].items()
                if state in ["leader", "router"]
            }
        while waited <= max_wait:
            first = capture()
            self.ns.go(delay)
            second = capture()
            changed = {
                nid: (first[nid], second[nid])
                for nid in first if first[nid] != second[nid]
            }
            print(f"@ {waited:>2}s | Changed: {changed}")
            if not changed:
                print("! Step 10")
                return
            waited += interval
        raise AssertionError(f"^Step 10 FAILED: Prefix/Route tables changed → {changed}")

    def _11_end_to_end_ping(self, max_wait=300, interval=2):
        waited = 0

        def get_addrs():
            return {
                nid: [ip for ip in self.ns.node_cmd(nid, "ipaddr") if ip.startswith("fd")]
                for nid in self.ns.nodes().keys()
            }

        def get_state(nid):
            return self.ns.node_cmd(nid, "state")[0].strip()

        while waited <= max_wait:
            addrs = get_addrs()
            failed = []

            for src in addrs:
                src_state = get_state(src)
                for dst in addrs:
                    if src == dst:
                        continue
                    dst_state = get_state(dst)

                    # Optional: Skip child -> child pings
                    if src_state == "child" and dst_state == "child":
                        continue

                    for ip in addrs[dst]:
                        res = self.ns.node_cmd(src, f"ping {ip}")
                        success = any("bytes from" in line for line in res)
                        print(f"ping {src} ➔ {dst} ({ip[:10]}...) = {'✅' if success else '❌'}")

                        if not success:
                            failed.append((src, dst, ip))

            print(f"@ {waited:>2}s | Ping failures: {failed}")

            if not failed:
                print("! Step 11: All mesh-local addresses reachable ✅")
                return

            waited += interval

        raise AssertionError(f"^Step 11 FAILED: Ping failures → {failed}")

    def _get_node_states(self):
        states = {}
        detached = []
        for node_id in self.ns.nodes().keys():
            state = self.ns.node_cmd(node_id, "state")[0].strip()
            states[node_id] = state
            if state in ["detached", "disabled"]:
                detached.append((node_id, state))
        return states, detached