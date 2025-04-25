# metrics/topology_convergence_phase.py
max_wait=1200
class TopologyConvergencePhase:
    def __init__(self, ns):
        self.ns = ns
        self.steps = [
            ("Step 8: Neighbor Table Stability", self._8_neighbor_table_stability),
            ("Step 9: Router Table Stability", self._9_router_table_stability),
            # ("Step 10: Prefix & Route Propagation", self._10_prefix_route_stability),
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

    def _8_neighbor_table_stability(self, delay=5, interval=2):
        waited = 0
        TOLERANCE_LQI = 5
        TOLERANCE_RSSI = 5

        def parse_table(raw_table):
            neighbors = {}
            for line in raw_table:
                if "|" in line and "Role" not in line and "+" not in line:
                    parts = line.split("|")
                    mac = parts[9].strip()
                    neighbors[mac] = {
                        "role": parts[1].strip(),
                        "rloc16": parts[2].strip(),
                        "R": parts[6].strip(),
                        "D": parts[7].strip(),
                        "N": parts[8].strip(),
                        "lqi": int(parts[3].strip()),
                        "rssi": int(parts[4].strip()),
                        "version": parts[10].strip()
                    }
            return neighbors

        def capture():
            result = {}
            for nid, state in self._get_node_states()[0].items():
                if state not in ["leader", "router"]:
                    continue
                table = self.ns.node_cmd(nid, "neighbor table")
                result[nid] = parse_table(table)
            return result

        def compare_neighbors(prev, curr):
            changes = {}
            for nid in prev:
                if nid not in curr:
                    changes[nid] = "Node disappeared"
                    continue
                node_changes = []
                prev_neighbors = prev[nid]
                curr_neighbors = curr[nid]
                for mac in prev_neighbors:
                    if mac not in curr_neighbors:
                        node_changes.append(f"Missing neighbor {mac}")
                        continue
                    p = prev_neighbors[mac]
                    c = curr_neighbors[mac]
                    for key in ["role", "rloc16", "R", "D", "N", "version"]:
                        if p[key] != c[key]:
                            node_changes.append(f"{mac}: {key} changed {p[key]} → {c[key]}")
                    if abs(p["lqi"] - c["lqi"]) > TOLERANCE_LQI:
                        node_changes.append(f"{mac}: LQI changed {p['lqi']} → {c['lqi']}")
                    if abs(p["rssi"] - c["rssi"]) > TOLERANCE_RSSI:
                        node_changes.append(f"{mac}: RSSI changed {p['rssi']} → {c['rssi']}")
                if node_changes:
                    changes[nid] = node_changes
            return changes

        while waited <= max_wait:
            first = capture()
            self.ns.go(delay)
            second = capture()
            changed = compare_neighbors(first, second)
            print(f"@ {waited:>2}s | Changes: {changed}")
            if not changed:
                print("! Step 8 ✅ Neighbor Table is stable.")
                return
            waited += interval

        raise AssertionError(f"^Step 8 FAILED: Neighbor changes → {changed}")

    def _9_router_table_stability(self, delay=5,  interval=2):
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

    def _10_prefix_route_stability(self, delay=5, interval=2):
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

    def _11_end_to_end_ping(self,  interval=2):
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