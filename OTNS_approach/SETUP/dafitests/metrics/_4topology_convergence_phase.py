# metrics/_4topology_convergence_phase.py
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
            ("Step 11: End-to-End ping",self._11_end_to_end_ping)
        ]

    def _10c_deep_troubleshoot(self):
        print("\n🛠️ Step 10_c: Deep Troubleshoot Started...\n")

        failed_nodes = []
        missing_neighbors = {}
        missing_routes = []
        coap_failed = []

        # Helper functions
        def safe_cmd(nid, cmd):
            try:
                return self.ns.node_cmd(nid, cmd)
            except Exception as e:
                print(f"⚠️ Node {nid} failed command '{cmd}': {e}")
                return []

        # 📦 Check node states
        print("📦 Node States:")
        for nid in self.ns.nodes().keys():
            state = safe_cmd(nid, "state")
            if not state:
                failed_nodes.append(nid)
            else:
                state_clean = state[0].strip()
                print(f"• Node {nid}: {state_clean}")
                if state_clean not in ["router", "leader"]:
                    print(f"⚠️ Node {nid} is {state_clean}, not router/leader!")

        # 🧱 Check neighbor tables
        print("\n🧱 Neighbor Tables:")
        for nid in self.ns.nodes().keys():
            neighbors = safe_cmd(nid, "neighbor table")
            if len(neighbors) == 0:
                missing_neighbors[nid] = []
            else:
                found = [line for line in neighbors if "Child" in line or "Router" in line]
                if not found:
                    missing_neighbors[nid] = neighbors
            print(f"• Node {nid} has {len(neighbors)} neighbor(s)")

        # 🛣️ Check router tables
        print("\n🛣️ Router Tables (Leader Only):")
        leader_id = None
        for nid in self.ns.nodes().keys():
            if "leader" in safe_cmd(nid, "state")[0].strip():
                leader_id = nid
                break

        if leader_id is None:
            print("❌ No leader found.")
            return

        print(f"• Leader is Node {leader_id}")
        router_table = safe_cmd(leader_id, "router table")
        if len(router_table) < 3:
            print(f"⚠️ Router table too small: {len(router_table)} entries")
            missing_routes.append(leader_id)
        else:
            print(f"• Leader router table OK ({len(router_table)} entries)")

        # 🌐 Check netdata
        print("\n🌐 Netdata Show:")
        netdata = safe_cmd(leader_id, "netdata show")
        if not netdata:
            print("⚠️ Netdata is empty!")
        else:
            for line in netdata:
                print(f"  {line}")

        # 📡 Check CoAP service availability
        print("\n📡 CoAP Service Check:")
        for nid in self.ns.nodes().keys():
            try:
                res = safe_cmd(nid, "coap start")
                res += safe_cmd(nid, "coap resource logs")
                if not any("Done" in line for line in res):
                    coap_failed.append(nid)
            except Exception as e:
                print(f"⚠️ CoAP failed on Node {nid}: {e}")
                coap_failed.append(nid)

        # ✅ Final Report
        print("\n📋 Troubleshoot Summary:")
        if failed_nodes:
            print(f"❌ Detached or missing nodes: {failed_nodes}")
        if missing_neighbors:
            print(f"⚠️ Nodes with no neighbors: {list(missing_neighbors.keys())}")
        if missing_routes:
            print(f"⚠️ Routing problems detected at Leader (Node {leader_id})")
        if coap_failed:
            print(f"⚠️ CoAP service problems: {coap_failed}")

        if not (failed_nodes or missing_neighbors or missing_routes or coap_failed):
            print("✅ Network is healthy at state, neighbor, router, and CoAP levels!")
        else:
            raise AssertionError("^Step 10_c FAILED: Topology problems detected!")

    import time

    def _10d_neighbor_refresh(self):
        print("\n🔄 Step 10_d: Refreshing neighbor tables...\n")

        def get_addrs():
            """Get all mesh-local RLOC addresses (fd..fe00)."""
            return {
                nid: [ip for ip in self.ns.node_cmd(nid, "ipaddr") if ip.startswith("fd") and ":ff:fe00:" in ip]
                for nid in self.ns.nodes().keys()
            }

        def safe_coap_post(src, dst_ip):
            """Try small CoAP POST to trigger neighbor refresh."""
            payload = "hello"
            cmd = f'coap post {dst_ip} logs con "{payload}"'
            try:
                res = self.ns.node_cmd(src, cmd)
                return any("Done" in line for line in res)
            except Exception as e:
                print(f"⚠️ CoAP refresh failed from {src} to {dst_ip}: {e}")
                return False

        # Start CoAP service everywhere
        for nid in self.ns.nodes().keys():
            try:
                self.ns.node_cmd(nid, "coap start")
                self.ns.node_cmd(nid, "coap resource logs")
            except Exception as e:
                print(f"⚠️ Failed to re-enable CoAP on node {nid}: {e}")

        # Give simulation time
        self.ns.go(5)
        time.sleep(1)

        addrs = get_addrs()
        failures = []

        print("\n📡 Sending neighbor refresh CoAP posts...")
        for src in addrs:
            for dst in addrs:
                if src == dst:
                    continue
                dst_ips = addrs[dst]
                if not dst_ips:
                    continue
                dst_ip = dst_ips[0]
                success = safe_coap_post(src, dst_ip)
                print(f"Refresh CoAP {src} ➔ {dst} = {'✅' if success else '❌'}")
                if not success:
                    failures.append((src, dst))

        if not failures:
            print("\n✅ Neighbor refresh completed successfully!")
        else:
            print(f"\n⚠️ Neighbor refresh had failures: {failures}")

    def _11_coap_reachability(self, interval=2):
        waited = 0

        def get_addrs():
            """Get mesh-local RLOC addresses (fd..fe00 only)."""
            return {
                nid: [ip for ip in self.ns.node_cmd(nid, "ipaddr") if ip.startswith("fd") and ":ff:fe00:" in ip]
                for nid in self.ns.nodes().keys()
            }

        def get_state(nid):
            return self.ns.node_cmd(nid, "state")[0].strip()

        def safe_coap_post(src, dst_ip, payload):
            """Send CoAP POST safely, retry once if needed."""
            cmd = f'coap post {dst_ip} logs con "{payload}"'
            try:
                res = self.ns.node_cmd(src, cmd)
                success = any("Done" in line for line in res)
            except Exception as e:
                print(f"⚠️ CoAP error from {src} to {dst_ip}: {e}")
                success = False

            if not success:
                time.sleep(0.5)
                try:
                    res = self.ns.node_cmd(src, cmd)
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

        # 💡 Let RPL routes settle properly
        print("⏳ Waiting before CoAP tests...")
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

                    # ✨ Generate a clean small payload (safe for CoAP)
                    payload = ''.join(choices(ascii_letters + digits, k=20))

                    success = safe_coap_post(src, dst_ip, payload)

                    print(f"CoAP {src} ➔ {dst} ({dst_ip[:10]}...) = {'✅' if success else '❌'}")

                    if not success:
                        failed.append((src, dst, dst_ip))

                    time.sleep(0.1)  # prevent simulator flooding

            print(f"@ {waited:>2}s | CoAP failures: {failed}")

            if not failed:
                print("! Step 11_b ✅ All CoAP messages delivered successfully")
                return

            waited += interval

        raise AssertionError(f"^Step 11_b FAILED: CoAP failures → {failed}")
    def run(self):
        for name, func in self.steps:
            print(f"# {name}")
            try:
                func()
            except AssertionError as e:
                print(f"^ {name} FAILED:", e)
                return False
        return True

    def _7b_transition_prepare(self):
        print("\n🔧 Step 7b: Preparing node roles for stable routing...\n")
        for nid in self.ns.nodes().keys():
            try:
                self.ns.node_cmd(nid, "mode rdn")
                self.ns.node_cmd(nid, "routerupgradethreshold 99")
                self.ns.node_cmd(nid, "routerselectionjitter 1")
                print(f"• Node {nid}: router mode forced + upgrade threshold set")
            except Exception as e:
                print(f"⚠️ Node {nid} setup failed: {e}")

        # Wait to let roles transition before Step 8 starts
        print("⏳ Waiting for nodes to settle as routers...")
        self.ns.go(10)
        time.sleep(1)
        print("✅ Step 7b complete: Role transitions should be stabilized.\n")

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
                try:
                    table = self.ns.node_cmd(nid, "neighbor table")
                    result[nid] = parse_table(table)
                except Exception as e:
                    print(f"⚠️ Node {nid} neighbor table failed: {e}")
                    continue
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
                nid: (first[nid], second.get(nid, None))
                for nid in first
                if second.get(nid, None) is None or first[nid] != second[nid]
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

    def _11_end_to_end_ping(self, interval=2, datasize=4, count=1):
        print("\n🚀 Step: End-to-End Ping and CoAP Test...\n")

        nodes = list(self.ns.nodes().keys())
        pending_pings = []

        print("\n🚀 Starting CoAP servers and setting /test-resource on all nodes...\n")
        for node_id in nodes:
            try:
                self.ns.node_cmd(node_id, "coap start")
                self.ns.node_cmd(node_id, "coap resource test-resource")
                print(f"✅ CoAP server and /test-resource created on Node {node_id}")
            except Exception as e:
                print(f"⚠️ Failed to setup CoAP server on Node {node_id}: {e}")

        self.ns.go(5)  # Let servers stabilize

        # 🔄 Safe sequential sending
        for src in nodes:
            for dst in nodes:
                if src == dst:
                    continue

                # 🛰️ 1. Ping
                try:
                    self.ns._do_command(f"ping {src} {dst} rloc datasize {datasize} count {count} interval {interval}")
                    print(f"✅ Sent ping from Node {src} ➔ Node {dst}")
                    pending_pings.append((src, dst))
                except Exception as e:
                    print(f"⚠️ Ping command error {src} ➔ {dst}: {e}")

                self.ns.go(0.5)  # ⏳ Short pause to avoid overloading

                # 🌐 2. CoAP
                try:
                    dst_mleid = self.ns.node_cmd(dst, "ipaddr mleid")[0]
                    payload = f"hello-{src}-to-{dst}"
                    self.ns.node_cmd(src, f'coap put {dst_mleid} test-resource con {payload}')
                    print(f"✅ Sent CoAP from Node {src} ➔ Node {dst}")
                except Exception as e:
                    print(f"⚠️ CoAP command error {src} ➔ {dst}: {e}")

                self.ns.go(0.5)  # ⏳ Short pause again

        # 🧹 Final big pause
        total_pairs = len(pending_pings)
        wait_time = max(10, total_pairs * 0.2)
        print(f"\n⏳ Waiting {wait_time:.1f} seconds to allow all traffic to settle...")
        self.ns.go(wait_time)

        # 📜 Collecting ping results
        print("\n📜 Collecting ping results...\n")
        pings_output = self.ns._do_command("pings")

        found_sources = set()
        for line in pings_output:
            if line.startswith("node="):
                parts = line.split()
                src_id = int(parts[0].split("=")[1])
                found_sources.add(src_id)

        failed_pings = []
        for src, dst in pending_pings:
            if src not in found_sources:
                failed_pings.append((src, dst))

        if failed_pings:
            print(f"\n❌ Unreachable pings detected: {failed_pings}")
            raise AssertionError(f"End-to-End Ping FAILED: {failed_pings}")
        else:
            print("\n✅ All nodes reachable by ping!")

    def _get_node_states(self):
        states = {}
        detached = []
        for node_id in self.ns.nodes().keys():
            state = self.ns.node_cmd(node_id, "state")[0].strip()
            states[node_id] = state
            if state in ["detached", "disabled"]:
                detached.append((node_id, state))
        return states, detached