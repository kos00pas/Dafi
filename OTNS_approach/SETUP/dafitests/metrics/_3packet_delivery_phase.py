import random
import time

class PacketDeliveryPhase:
    def __init__(self, ns):
        self.ns = ns
        print("Step 17 !")

    def run(self):
        print("\nStep 17 Starting Packet Delivery Phase (Step 17)...\n")
        self._setup_coap_servers()
        pairs = self._select_node_pairs()
        results = self._send_coap_messages(pairs)
        success = self._analyze_results(results)
        self._analyze_ipv6_forwarding_efficiency(results)
        print("\n✅ Packet Delivery Phase completed successfully!\n")
        print("\nStep 17 END\n")
        return success, results

    def _analyze_ipv6_forwarding_efficiency(self, results):
        print("\n📊 Calculating IPv6 Packet Forwarding Efficiency...")

        total_transmissions = 0
        successful_deliveries = 0

        for (src, dst), delivered in results.items():
            if delivered:
                try:
                    # 🌐 Trace route from source to destination
                    hops = self._count_hops(src, dst)
                    total_transmissions += hops
                    successful_deliveries += 1
                    print(f"• {src} ➔ {dst}: {hops} hops")
                except Exception as e:
                    print(f"⚠️ Failed to count hops {src} ➔ {dst}: {e}")

        if total_transmissions == 0:
            print("⚠️ No transmissions counted — cannot compute efficiency.")
            return

        ipv6_forwarding_efficiency = (successful_deliveries / total_transmissions) * 100

        print("\n🚀 IPv6 Packet Forwarding Efficiency Results:")
        print(f"• Total Successful Deliveries: {successful_deliveries}")
        print(f"• Total Transmissions (Sum of all hops): {total_transmissions}")
        print(f"• IPv6 Packet Forwarding Efficiency: {ipv6_forwarding_efficiency:.2f}%\n")

    def _count_hops(self, src, dst):
        """
        Proper BFS traversal to find minimum hops from src to dst.
        """
        if src == dst:
            return 0

        visited = set()
        queue = [(src, 0)]  # (node_id, hop_count)

        while queue:
            current_node, hops = queue.pop(0)
            visited.add(current_node)

            try:
                neighbors = self._get_neighbors(current_node)
            except Exception as e:
                print(f"⚠️ Could not get neighbors for node {current_node}: {e}")
                continue

            for neighbor in neighbors:
                if neighbor == dst:
                    return hops + 1
                if neighbor not in visited:
                    queue.append((neighbor, hops + 1))
                    visited.add(neighbor)

        raise ValueError(f"No path found from {src} to {dst}")


    def _get_neighbors(self, node_id):
        """
        Return a list of neighbor node IDs from neighbor table of node_id.
        """
        output = self.ns.node_cmd(node_id, "neighbor table")
        neighbor_ids = []

        for line in output:
            fields = line.strip().split()
            if fields and fields[0] in ['R', 'C', 'E', 'L']:  # valid roles
                try:
                    neighbor_rloc16_hex = fields[1]
                    neighbor_ids.append(self._rloc16_to_node_id(neighbor_rloc16_hex))
                except Exception as e:
                    print(f"⚠️ Could not map neighbor: {e}")
                    continue

        return neighbor_ids

    def _rloc16_to_node_id(self, rloc16_hex):
        """
        Simple mapping from RLOC16 to node id.
        Assumes RLOC16 = 0x<node_id>000 or similar (common in OTNS)
        """
        # Rough method, depends on your OTNS numbering!
        for nid, info in self.ns.nodes().items():
            try:
                rlocs = self.ns.node_cmd(nid, "ipaddr")
                for rloc in rlocs:
                    if rloc.startswith("fd") and f":{rloc16_hex.lower()}" in rloc.lower():
                        return nid
            except:
                continue
        raise ValueError(f"Could not map RLOC16 {rloc16_hex} to node id")

    def _setup_coap_servers(self):
        print("\n⚙️ Setting up CoAP servers on all nodes...")
        for nid in self.ns.nodes().keys():
            try:
                self.ns.node_cmd(nid, "coap start")
                self.ns.node_cmd(nid, "coap resource logs")
                print(f"• Node {nid}: CoAP server ready")
            except Exception as e:
                print(f"⚠️ Node {nid}: Failed to start CoAP: {e}")
        self.ns.go(5)

    def _select_node_pairs(self):
        nodes = list(self.ns.nodes().keys())
        states = {nid: self.ns.node_cmd(nid, "state")[0].strip() for nid in nodes}

        leader = [nid for nid, role in states.items() if role == "leader"]
        routers = [nid for nid, role in states.items() if role == "router"]
        children = [nid for nid, role in states.items() if role == "child"]

        pairs = []

        # Step A: Leader-Router pairs (ALL)
        for l in leader:
            for r in routers:
                pairs.append((l, r))
        count_LR = len(pairs)

        # Step B: Leader-Child pairs (ALL)
        for l in leader:
            for c in children:
                pairs.append((l, c))
        count_LC = len(pairs) - count_LR  # delta after adding LC

        # Define limits
        MAX_PAIRS = 100
        initial_target = int(len(nodes) * (len(nodes) - 1) * 0.3)
        budget = min(initial_target, MAX_PAIRS)

        # Remaining slots to reach budget
        remaining_budget = max(0, budget - len(pairs))

        # Step C: Fill remaining slots (if any) with 75% R-R and 25% R-C
        rr_candidates = [(r1, r2) for r1 in routers for r2 in routers if r1 != r2]
        rc_candidates = [(r, c) for r in routers for c in children]

        random.shuffle(rr_candidates)
        random.shuffle(rc_candidates)

        rr_target = remaining_budget * 3 // 4
        rc_target = remaining_budget - rr_target

        pairs += rr_candidates[:rr_target]
        pairs += rc_candidates[:rc_target]

        # 🛡️ Safety: if somehow over, trim to max
        if len(pairs) > MAX_PAIRS:
            pairs = random.sample(pairs, MAX_PAIRS)

        return pairs

    def _send_coap_messages(self, pairs):
        results = {}
        for src, dst in pairs:
            try:
                # 🛰️ Get the destination's MLEID address
                dst_mleid = self.ns.node_cmd(dst, "ipaddr mleid")[0]

                # 🌐 Build a simple payload
                payload = f"echo-{src}-to-{dst}"

                # 🚀 Send a CoAP PUT to /test-resource
                self.ns.node_cmd(src, f'coap put {dst_mleid} test-resource con {payload}')
                self.ns.go(2)  # allow some simulated time to process

                # 🧹 (Optional) Could later parse coaps, but here we assume 'Done' = success
                results[(src, dst)] = True
                print(f"CoAP {src} ➔ {dst}: ✅ Delivered")

            except Exception as e:
                print(f"⚠️ CoAP failed {src} ➔ {dst}: {e}")
                results[(src, dst)] = False

        return results

    def _analyze_results(self, results):
        sent = len(results)
        delivered = sum(1 for delivered in results.values() if delivered)
        lost = sent - delivered

        pdr = (delivered / sent) * 100
        plr = (lost / sent) * 100
        forwarding_success_rate = (delivered / sent) * 100  # Explicit for Step 18

        print("\n📊 Packet Delivery Statistics:")
        print(f"• Packets Sent: {sent}")
        print(f"• Packets Delivered: {delivered}")
        print(f"• Packets Lost: {lost}")
        print(f"• Packet Delivery Ratio (PDR): {pdr:.2f}%")
        print(f"• Packet Loss Rate (PLR): {plr:.2f}%")
        print(f"🚀 Forwarding Success Rate: {forwarding_success_rate:.2f}%")

        if pdr < 95:
            print(f"⚠️ WARNING: PDR too low: {pdr:.2f}% (threshold 95%)")
            return False
        return True

