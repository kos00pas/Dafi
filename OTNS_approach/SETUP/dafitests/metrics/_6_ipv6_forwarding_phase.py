import time

class IPv6ForwardingPhase:
    def __init__(self, ns, coap_results_step17):
        self.ns = ns
        self.coap_results = coap_results_step17  # dictionary {(src, dst): success}
        self.hop_counts = {}  # {(src, dst): hop_count}
        self.latencies = {}   # {(src, dst): latency_seconds}

    def run(self):
        print("\n\U0001f357 Starting IPv6 Packet Forwarding Efficiency Phase (Step 18)...\n")
        self._collect_hop_counts()
        self._calculate_latency_per_hop()
        self._report_results()
        print("\n✅ IPv6 Packet Forwarding Efficiency Phase completed successfully!\n")
        return True

    def _collect_hop_counts(self):
        print("\n🔎 Collecting hop counts for successfully delivered CoAP packets...")

        for (src, dst), delivered in self.coap_results.items():
            if not delivered:
                continue

            try:
                # Start from src, trace the path towards dst
                visited = set()
                current = src
                hops = 0

                dst_rloc16 = self.ns.get_rloc16(dst)

                while current != dst:
                    if current in visited:
                        print(f"⚠️ Loop detected in path from {src} to {dst}")
                        hops = -1
                        break

                    visited.add(current)

                    route_table = self.ns.node_cmd(current, "route")
                    next_hop = self._find_next_hop(route_table, dst_rloc16)

                    if next_hop is None:
                        print(f"⚠️ No route from Node {current} to Node {dst}")
                        hops = -1
                        break

                    current = next_hop
                    hops += 1

                if hops > 0:
                    self.hop_counts[(src, dst)] = hops
                    print(f"• Path {src} ➔ {dst}: {hops} hops")

            except Exception as e:
                print(f"⚠️ Error tracing route {src} ➔ {dst}: {e}")

    def _find_next_hop(self, route_table, dst_rloc16):
        for line in route_table:
            if f"{dst_rloc16:04x}" in line:
                parts = line.split('|')
                if len(parts) >= 4:
                    next_hop_rloc = parts[3].strip()
                    for nid, nodeinfo in self.ns.nodes().items():
                        try:
                            if self.ns.get_rloc16(nid) == int(next_hop_rloc, 16):
                                return nid
                        except:
                            continue
        return None

    def _calculate_latency_per_hop(self):
        print("\n⏱️ Estimating Latency per Hop... (simulated)")

        for (src, dst) in self.hop_counts:
            send_time = time.time() - 1.0  # Mock: assume CoAP sent 1 second ago
            recv_time = time.time()        # Mock: assume CoAP received now
            latency_total = recv_time - send_time

            hops = self.hop_counts[(src, dst)]

            if hops > 0:
                latency_per_hop = latency_total / hops
                self.latencies[(src, dst)] = latency_per_hop
                print(f"• {src} ➔ {dst}: {latency_per_hop:.6f} sec/hop over {hops} hops")

    def _report_results(self):
        print("\n📊 Final IPv6 Forwarding Efficiency Report:")

        for (src, dst), hops in self.hop_counts.items():
            latency = self.latencies.get((src, dst), None)
            if latency:
                print(f"• {src} ➔ {dst}: {hops} hops, {latency:.6f} sec/hop")
            else:
                print(f"• {src} ➔ {dst}: {hops} hops, latency unknown")

        if not self.hop_counts:
            raise AssertionError("^Step 18 FAILED: No successful hop counts traced.")
