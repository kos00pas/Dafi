# metrics/topology_convergence_phase.py
max_wait=1200
import time
from random import choices
from string import ascii_letters, digits

class TopologyConvergencePhase:
    def __init__(self, ns):
        self.ns = ns
        self.steps = [
            ("Step 8: Neighbor Table Stability", self._8_neighbor_table_stability),
            ("Step 9: Router Table Stability", self._9_router_table_stability),
            ("Step 10: Prefix & Route Propagation", self._10_prefix_route_stability),
            # ("Step 10_b: Topology Troubleshoot", self._10b_topology_troubleshoot),
            # ("Step 11: End-to-End Reachability", self._11_end_to_end_ping),
            # ("Step 11_b: CoAP Reachability", self._11_coap_reachability)
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

    def _10b_topology_troubleshoot(self):
        print("\n🔍 Step 10_b: Running automatic topology diagnostics...\n")

        def get_state(nid):
            return self.ns.node_cmd(nid, "state")[0].strip()

        def get_neighbors(nid):
            try:
                return self.ns.node_cmd(nid, "neighbor table")
            except Exception:
                return []

        def get_router_table(nid):
            try:
                return self.ns.node_cmd(nid, "router table")
            except Exception:
                return []

        def get_netdata(nid):
            try:
                return self.ns.node_cmd(nid, "netdata show")
            except Exception:
                return []

        failed_nodes = []
        leader_id = None

        print("📦 Checking node states...")
        for nid in self.ns.nodes().keys():
            state = get_state(nid)
            print(f"• Node {nid}: {state}")
            if state == "leader":
                leader_id = nid
            if state == "detached":
                failed_nodes.append(nid)

        if leader_id is None:
            raise RuntimeError("❌ No leader found in the network!")

        print(f"\n🧭 Leader is node {leader_id}\n")

        print("🧱 Checking router table of the leader...")
        router_table = get_router_table(leader_id)
        for line in router_table:
            print(f"  {line}")
        if len(router_table) < 5:
            print("⚠️ Router table seems short — some routes may be missing.")

        print("\n🔍 Checking neighbor tables...")
        for nid in self.ns.nodes().keys():
            neighbors = get_neighbors(nid)
            print(f"\n• Node {nid} neighbors:")
            for line in neighbors:
                print(f"   {line}")
            if len(neighbors) == 0:
                print("⚠️ Node has no visible neighbors.")

        print("\n🌐 Verifying netdata on the leader...")
        netdata = get_netdata(leader_id)
        for line in netdata:
            print(f"  {line}")
        if not any("prefix" in line.lower() for line in netdata):
            print("⚠️ No prefix registered in netdata!")

        if failed_nodes:
            raise AssertionError(f"^Step 10_b FAILED: Detached nodes → {failed_nodes}")
        else:
            print(
                "\n✅ Step 10_b: Topology health check passed — all nodes are attached and reachable at routing level.")

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

        import time

        def capture():
            result = {}
            for nid, state in self._get_node_states()[0].items():
                if state not in ["leader", "router"]:
                    continue
                if nid % 10 != 0:  # only sample 10% of routers
                    continue
                table = self.ns.node_cmd(nid, "neighbor table")
                result[nid] = parse_table(table)
                time.sleep(0.2)  # wait 200ms after each neighbor table
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



    def _11_end_to_end_ping(self, interval=2):
        waited = 0

        def get_addrs():
            """Get all mesh-local addresses (only fd..fe00 ones)."""
            return {
                nid: [ip for ip in self.ns.node_cmd(nid, "ipaddr") if ip.startswith("fd") and ":ff:fe00:" in ip]
                for nid in self.ns.nodes().keys()
            }

        def get_state(nid):
            return self.ns.node_cmd(nid, "state")[0].strip()

        def safe_ping(src, dst_ip):
            """Ping once, retry once with sleep if first fails."""
            try:
                res = self.ns.node_cmd(src, f"ping {dst_ip}")
                success = any("bytes from" in line for line in res)
            except Exception as e:
                print(f"⚠️ Ping error from {src} to {dst_ip}: {e}")
                success = False

            if not success:
                time.sleep(0.5)  # Wait before retrying
                try:
                    res = self.ns.node_cmd(src, f"ping {dst_ip}")
                    success = any("bytes from" in line for line in res)
                except Exception as e:
                    print(f"⚠️ Retry ping error from {src} to {dst_ip}: {e}")
                    success = False

            return success

        # 🌟 Important: slow down simulation slightly
        print("⚙️ Setting simulation speed to safer value...")
        self.ns.speed = 100000  # Safer simulation speed

        # 💡 Give time for network to stabilize
        print("⏳ Waiting for RPL routes to settle before pinging...")
        self.ns.go(10)
        time.sleep(2)

        while waited <= 1200:
            addrs = get_addrs()
            failed = []

            for src in addrs:
                src_state = get_state(src)
                for dst in addrs:
                    if src == dst:
                        continue
                    dst_state = get_state(dst)

                    # Skip child -> child pinging (optional)
                    if src_state == "child" and dst_state == "child":
                        continue

                    # Pick RLOC address (fd..fe00:xxxx)
                    dst_ips = addrs[dst]
                    if not dst_ips:
                        continue  # No valid address

                    dst_ip = dst_ips[0]
                    success = safe_ping(src, dst_ip)

                    print(f"ping {src} ➔ {dst} ({dst_ip[:10]}...) = {'✅' if success else '❌'}")

                    if not success:
                        failed.append((src, dst, dst_ip))

                    time.sleep(0.1)  # ⏳ Slow down between pings

            print(f"@ {waited:>2}s | Ping failures: {failed}")

            if not failed:
                print("! Step 11 ✅ All mesh-local addresses reachable")
                return

            waited += interval

        raise AssertionError(f"^Step 11 FAILED: Ping failures → {failed}")



    def _11_coap_reachability(self, interval=2):
        waited = 0

        def get_addrs():
            """Get mesh-local RLOC addresses (fd..fe00) only."""
            return {
                nid: [ip for ip in self.ns.node_cmd(nid, "ipaddr") if ip.startswith("fd") and ":ff:fe00:" in ip]
                for nid in self.ns.nodes().keys()
            }

        def get_state(nid):
            return self.ns.node_cmd(nid, "state")[0].strip()

        def safe_coap_post(src, dst_ip, payload):
            """Send CoAP POST, retry once if needed."""
            try:
                res = self.ns.node_cmd(src, f'coap post coap://[{dst_ip}]/logs con {payload}')
                success = any("Done" in line for line in res)
            except Exception as e:
                print(f"⚠️ CoAP error from {src} to {dst_ip}: {e}")
                success = False

            if not success:
                time.sleep(0.5)
                try:
                    res = self.ns.node_cmd(src, f'coap post coap://[{dst_ip}]/logs con {payload}')
                    success = any("Done" in line for line in res)
                except Exception as e:
                    print(f"⚠️ Retry CoAP error from {src} to {dst_ip}: {e}")
                    success = False

            return success

        # 🌟 Start CoAP service on all nodes
        print("⚙️ Enabling CoAP service on all nodes...")
        for node in self.ns.nodes().keys():
            try:
                self.ns.node_cmd(node, "coap start")
                self.ns.node_cmd(node, "coap resource logs")
            except Exception as e:
                print(f"⚠️ Failed to start CoAP on node {node}: {e}")

        # 💡 Give time to stabilize
        print("⏳ Waiting before starting CoAP tests...")
        self.ns.go(10)
        time.sleep(2)

        while waited <= 1200:
            addrs = get_addrs()
            failed = []

            for src in addrs:
                src_state = get_state(src)
                for dst in addrs:
                    if src == dst:
                        continue
                    dst_state = get_state(dst)

                    if src_state == "child" and dst_state == "child":
                        continue

                    dst_ips = addrs[dst]
                    if not dst_ips:
                        continue

                    dst_ip = dst_ips[0]

                    # 🔥 Generate a random 20-char payload
                    payload = ''.join(choices(ascii_letters + digits, k=20))

                    success = safe_coap_post(src, dst_ip, payload)

                    print(f"CoAP {src} ➔ {dst} ({dst_ip[:10]}...) = {'✅' if success else '❌'}")

                    if not success:
                        failed.append((src, dst, dst_ip))

                    time.sleep(0.1)  # slow down between CoAP posts

            print(f"@ {waited:>2}s | CoAP failures: {failed}")

            if not failed:
                print("! Step 11_b ✅ All CoAP messages delivered")
                return

            waited += interval

        raise AssertionError(f"^Step 11_b FAILED: CoAP failures → {failed}")

    def _get_node_states(self):
        states = {}
        detached = []
        for node_id in self.ns.nodes().keys():
            state = self.ns.node_cmd(node_id, "state")[0].strip()
            states[node_id] = state
            if state in ["detached", "disabled"]:
                detached.append((node_id, state))
        return states, detached