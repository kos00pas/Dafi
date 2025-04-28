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
        print("\n🛰️ Analyzing IPv6 Forwarding Efficiency — Node Pairs:\n")
        MAX_HOPS = 50
        for (src, dst), delivered in results.items():
            status = "✅ Delivered" if delivered else "❌ Failed"
            print(f"• {src} ➔ {dst}: {status}")

            queue = [(src, 0)]  # (node_id, hops)
            dst_rloc16 = self.ns.node_cmd(dst, "rloc16")[0].strip()
            dst_router_rloc16 = f"{int(dst_rloc16, 16) & 0xFC00:04x}"
            success = False

            while queue:
                current_src, hops = queue.pop(0)
                if hops >= MAX_HOPS:
                    continue

                try:
                    routing_table = self.ns.node_cmd(current_src, "router table")
                    print(f"  📜 Routing Table for Node {current_src}:")
                    for entry in routing_table:
                        print(f"    {entry}")

                    print(
                        f"  🎯 Searching for destination RLOC16 {dst_rloc16} in routing table of Node {current_src}...")

                    found = False
                    for entry in routing_table:
                        if dst_rloc16.lower() in entry.lower():
                            found = True
                            print(f"    ✅ Found destination RLOC16 {dst_rloc16} in routing table entry!")
                            success = True
                            break

                    if found:
                        break

                    for entry in routing_table:
                        if dst_router_rloc16 in entry.lower():
                            print(f"    ✅ Found parent router RLOC16 {dst_router_rloc16} in routing table entry!")
                            success = True
                            break

                    if success:
                        break

                    neighbor_table = self.ns.node_cmd(current_src, "neighbor table")
                    print(f"  👥 Neighbor Table for Source Node {current_src}:")
                    for neighbor_entry in neighbor_table:
                        print(f"    {neighbor_entry}")
                        parts = neighbor_entry.split()
                        if len(parts) > 1:
                            neighbor_rloc16 = parts[1].lower()
                            next_hop_node_id = None
                            for node_id, node in self.ns.nodes().items():
                                try:
                                    node_rloc16 = self.ns.node_cmd(node_id, "rloc16")[0].strip().lower()
                                    if node_rloc16 == neighbor_rloc16:
                                        next_hop_node_id = node_id
                                        break
                                except:
                                    continue

                            if next_hop_node_id is not None:
                                queue.append((next_hop_node_id, hops + 1))

                except Exception as e:
                    print(f"⚠️ Failed to retrieve information for Node {current_src}: {e}")
                    continue

            if not success:
                print(f"    ❌ Failed to find destination RLOC16 {dst_rloc16} within {MAX_HOPS} hops.")

        print("\n✅ Finished listing analyzed node pairs with multi-hop forwarding analysis if needed.\n")

    # def _analyze_ipv6_forwarding_efficiency(self, results):
    #     print("\n🛰️ Analyzing IPv6 Forwarding Efficiency — Node Pairs:\n")
    #     MAX_HOPS = 5
    #     for (src, dst), delivered in results.items():
    #         status = "✅ Delivered" if delivered else "❌ Failed"
    #         print(f"• {src} ➔ {dst}: {status}")
    #
    #         current_src = src
    #         hops = 0
    #         success = False
    #
    #         while hops < MAX_HOPS:
    #             try:
    #                 routing_table = self.ns.node_cmd(current_src, "router table")
    #                 print(f"  📜 Routing Table for Node {current_src}:")
    #                 for entry in routing_table:
    #                     print(f"    {entry}")
    #
    #                 dst_rloc16 = self.ns.node_cmd(dst, "rloc16")[0].strip()
    #                 print(
    #                     f"  🎯 Searching for destination RLOC16 {dst_rloc16} in routing table of Node {current_src}...")
    #
    #                 found = False
    #                 for entry in routing_table:
    #                     if dst_rloc16.lower() in entry.lower():
    #                         found = True
    #                         print(f"    ✅ Found destination RLOC16 {dst_rloc16} in routing table entry!")
    #                         success = True
    #                         break
    #
    #                 if found:
    #                     break
    #
    #                 # Try to find parent router RLOC16
    #                 dst_router_rloc16 = f"{int(dst_rloc16, 16) & 0xFC00:04x}"
    #                 for entry in routing_table:
    #                     if dst_router_rloc16 in entry.lower():
    #                         print(f"    ✅ Found parent router RLOC16 {dst_router_rloc16} in routing table entry!")
    #                         success = True
    #                         break
    #
    #                 if success:
    #                     break
    #
    #                 # If not found, move to next hop neighbor
    #                 neighbor_table = self.ns.node_cmd(current_src, "neighbor table")
    #                 print(f"  👥 Neighbor Table for Source Node {current_src}:")
    #                 next_hop = None
    #                 for neighbor_entry in neighbor_table:
    #                     print(f"    {neighbor_entry}")
    #                     if dst_router_rloc16 in neighbor_entry.lower():
    #                         next_hop = neighbor_entry.split()[1]  # Assuming RLOC16 is the second field
    #                         break
    #
    #                 if next_hop is None:
    #                     print(f"    ❌ No neighbor towards destination found from Node {current_src}.")
    #                     break
    #
    #                 # Find the node ID for next hop
    #                 next_hop_node_id = None
    #                 for node_id, node in self.ns.nodes().items():
    #                     try:
    #                         node_rloc16 = self.ns.node_cmd(node_id, "rloc16")[0].strip().lower()
    #                         if node_rloc16 == next_hop.lower():
    #                             next_hop_node_id = node_id
    #                             break
    #                     except:
    #                         continue
    #
    #                 if next_hop_node_id is None:
    #                     print(f"    ❌ Could not resolve next hop node ID from RLOC16 {next_hop}.")
    #                     break
    #
    #                 print(f"    🔁 Moving to next hop Node {next_hop_node_id}...")
    #                 current_src = next_hop_node_id
    #                 hops += 1
    #
    #             except Exception as e:
    #                 print(f"⚠️ Failed to retrieve information for Node {current_src}: {e}")
    #                 break
    #
    #         if not success:
    #             print(f"    ❌ Failed to find destination RLOC16 {dst_rloc16} within {MAX_HOPS} hops.")
    #
    #     print("\n✅ Finished listing analyzed node pairs with multi-hop forwarding analysis if needed.\n")
    # def _analyze_ipv6_forwarding_efficiency(self, results):
    #     print("\n🛰️ Analyzing IPv6 Forwarding Efficiency — Node Pairs:\n")
    #     for (src, dst), delivered in results.items():
    #         status = "✅ Delivered" if delivered else "❌ Failed"
    #         print(f"• {src} ➔ {dst}: {status}")
    #
    #         # Fetch and print the routing table of the source node
    #         try:
    #             routing_table = self.ns.node_cmd(src, "router table")
    #             print(f"  📜 Routing Table for Node {src}:")
    #             for entry in routing_table:
    #                 print(f"    {entry}")
    #
    #             # Get RLOC16 of the destination node
    #             dst_rloc16 = self.ns.node_cmd(dst, "rloc16")[0].strip()
    #             print(f"  🎯 Searching for destination RLOC16 {dst_rloc16} in routing table...")
    #
    #             found = False
    #             for entry in routing_table:
    #                 if dst_rloc16.lower() in entry.lower():
    #                     found = True
    #                     print(f"    ✅ Found destination RLOC16 {dst_rloc16} in routing table entry!")
    #                     break
    #
    #             if not found:
    #                 print(f"    ❌ Destination RLOC16 {dst_rloc16} NOT found in routing table.")
    #
    #                 # Fetch and search neighbor table of the source node
    #                 try:
    #                     neighbor_table = self.ns.node_cmd(src, "neighbor table")
    #                     print(f"  👥 Neighbor Table for Source Node {src}:")
    #                     dst_rloc16_found_in_neighbors = False
    #                     for neighbor_entry in neighbor_table:
    #                         print(f"    {neighbor_entry}")
    #                         if dst_rloc16.lower() in neighbor_entry.lower():
    #                             dst_rloc16_found_in_neighbors = True
    #                     if dst_rloc16_found_in_neighbors:
    #                         print(f"    ✅ Destination RLOC16 {dst_rloc16} found in source's neighbor table!{src}->{dst}")
    #                     else:
    #                         print(f"    ❌ Destination RLOC16-second-time {dst_rloc16} NOT found in source's neighbor table.")
    #                 except Exception as e:
    #                     print(f"⚠️ Failed to retrieve neighbor table for Source Node {src}: {e}")
    #
    #         except Exception as e:
    #             print(f"⚠️ Failed to retrieve routing table or RLOC16 for Node {src} ➔ {dst}: {e}")
    #
    #     print("\n✅ Finished listing analyzed node pairs and their routing tables and neighbor tables if needed.\n")

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

        for l in leader:
            for r in routers:
                pairs.append((l, r))
        count_LR = len(pairs)

        for l in leader:
            for c in children:
                pairs.append((l, c))
        count_LC = len(pairs) - count_LR

        MAX_PAIRS = 100
        initial_target = int(len(nodes) * (len(nodes) - 1) * 0.3)
        budget = min(initial_target, MAX_PAIRS)
        remaining_budget = max(0, budget - len(pairs))

        rr_candidates = [(r1, r2) for r1 in routers for r2 in routers if r1 != r2]
        rc_candidates = [(r, c) for r in routers for c in children]

        random.shuffle(rr_candidates)
        random.shuffle(rc_candidates)

        rr_target = remaining_budget * 3 // 4
        rc_target = remaining_budget - rr_target

        pairs += rr_candidates[:rr_target]
        pairs += rc_candidates[:rc_target]

        if len(pairs) > MAX_PAIRS:
            pairs = random.sample(pairs, MAX_PAIRS)

        return pairs

    def _send_coap_messages(self, pairs):
        results = {}
        for src, dst in pairs:
            try:
                dst_mleid = self.ns.node_cmd(dst, "ipaddr mleid")[0]
                payload = f"echo-{src}-to-{dst}"
                self.ns.node_cmd(src, f'coap put {dst_mleid} test-resource con {payload}')
                self.ns.go(2)
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
        forwarding_success_rate = (delivered / sent) * 100

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
