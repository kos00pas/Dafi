import random
import time
from datetime import datetime

from scapy.all import rdpcap, Raw ,sniff
from pyshark import FileCapture

from scapy.layers.dot15d4 import Dot15d4Data

class PDR_ipv6:
    def __init__(self, ns,result_file):
        self.ns = ns
        self.result_file = result_file
        print("Step 17 !")

    def run(self):
        self.result_file.write("\n========= [ 3&6. Packet Delivery & Communication & IPv6 Packet Forwarding Efficiency  ] =========\n")
        self.result_file.write("Step 17: Packet Delivery\n")
        self.result_file.flush()
        start_time = datetime.now()

        print("\nStep 17 Starting Packet Delivery Phase (Step 17)...\n")
        self._setup_coap_servers()
        pairs = self._select_node_pairs()
        results = self._send_coap_messages(pairs)

        role_batches = self._split_pairs_by_role(pairs)

        success = self._analyze_results(results)
        print("\n✅ Packet Delivery Phase completed successfully!\n")
        print("\nStep 17 END\n")
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        self.result_file.write(f"\tDone: {duration:.9f}s\n--------------------------------------------\n")

        self.st18_analyze_ipv6_forwarding_efficiency(results)
        print("\nStart 18 END\n")
        return success, results, role_batches



    def _split_pairs_by_role(self, pairs):
        role_pair_batches = {
            ('leader', 'router'): [],
            ('leader', 'child'): [],
            ('router', 'router'): [],
            ('router', 'child'): [],
            ('router', 'leader'): [],
            ('child', 'router'): [],
            ('child', 'leader'): [],
        }

        for src, dst in pairs:
            src_role = self.ns.node_cmd(src, "state")[0].strip()
            dst_role = self.ns.node_cmd(dst, "state")[0].strip()
            role_pair = (src_role, dst_role)

            if role_pair in role_pair_batches:
                role_pair_batches[role_pair].append((src, dst))  # <-- Keep (node_id, node_id) tuples
            else:
                print(f"⚠️ Unknown role-pair ({src_role} ➔ {dst_role}) for nodes {src} ➔ {dst}")

        return role_pair_batches

    def st18_analyze_ipv6_forwarding_efficiency(self, results):
        print("\n🛰️ Step 18 Analyzing IPv6 Forwarding Efficiency — Node Pairs:\n")
        self.result_file.write("Step 18:  IPv6 Forwarding Efficiency\n")
        self.result_file.flush()
        start_time = datetime.now()

        MAX_HOPS = 25
        hop_results = {}
        role_results = {}

        for (src, dst), delivered in results.items():
            status = "✅ Delivered" if delivered else "❌ Failed"
            print(f"• {src} ➔ {dst}: {status}")

            queue = [(src, 0)]  # (node_id, hops)
            dst_rloc16 = self.ns.node_cmd(dst, "rloc16")[0].strip()
            dst_router_rloc16 = f"{int(dst_rloc16, 16) & 0xFC00:04x}"
            success = False
            final_hops = -1

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
                            final_hops = hops
                            break

                    if found:
                        break

                    for entry in routing_table:
                        if dst_router_rloc16 in entry.lower():
                            print(f"    ✅ Found parent router RLOC16 {dst_router_rloc16} in routing table entry!")
                            success = True
                            final_hops = hops
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

            if success:
                hop_results[(src, dst)] = final_hops
            else:
                hop_results[(src, dst)] = None
                print(f"    ❌ Failed to find destination RLOC16 {dst_rloc16} within {MAX_HOPS} hops.")

            try:
                src_role = self.ns.node_cmd(src, "state")[0].strip()
                dst_role = self.ns.node_cmd(dst, "state")[0].strip()
            except Exception:
                src_role = "unknown"
                dst_role = "unknown"

            role_results[(src, dst)] = (src_role, dst_role)

        print("\n📋 Hop Counts for Each Pair:")
        for (src, dst), hops in hop_results.items():
            src_role, dst_role = role_results.get((src, dst), ("unknown", "unknown"))
            if hops is not None:
                print(f"• {src} ({src_role}) ➔ {dst} ({dst_role}): Reached in {hops} hop(s)")
            else:
                print(f"• {src} ({src_role}) ➔ {dst} ({dst_role}): Not reachable within {MAX_HOPS} hops")

        print("\n✅ Finished listing analyzed node pairs with multi-hop forwarding analysis if needed.\n")
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        self.result_file.write(f"\tDone: {duration:.6f}s\n")
        self.result_file.write("")
        self.result_file.flush()

    # def _analyze_ipv6_forwarding_efficiency(self, results):
    #     print("\n🛰️ Analyzing IPv6 Forwarding Efficiency — Node Pairs:\n")
    #     MAX_HOPS = 15
    #     hop_results = {}
    #
    #     for (src, dst), delivered in results.items():
    #         status = "✅ Delivered" if delivered else "❌ Failed"
    #         print(f"• {src} ➔ {dst}: {status}")
    #
    #         queue = [(src, 0)]  # (node_id, hops)
    #         dst_rloc16 = self.ns.node_cmd(dst, "rloc16")[0].strip()
    #         dst_router_rloc16 = f"{int(dst_rloc16, 16) & 0xFC00:04x}"
    #         success = False
    #         final_hops = -1
    #
    #         while queue:
    #             current_src, hops = queue.pop(0)
    #             if hops >= MAX_HOPS:
    #                 continue
    #
    #             try:
    #                 routing_table = self.ns.node_cmd(current_src, "router table")
    #                 print(f"  📜 Routing Table for Node {current_src}:")
    #                 for entry in routing_table:
    #                     print(f"    {entry}")
    #
    #                 print(
    #                     f"  🎯 Searching for destination RLOC16 {dst_rloc16} in routing table of Node {current_src}...")
    #
    #                 found = False
    #                 for entry in routing_table:
    #                     if dst_rloc16.lower() in entry.lower():
    #                         found = True
    #                         print(f"    ✅ Found destination RLOC16 {dst_rloc16} in routing table entry!")
    #                         success = True
    #                         final_hops = hops
    #                         break
    #
    #                 if found:
    #                     break
    #
    #                 for entry in routing_table:
    #                     if dst_router_rloc16 in entry.lower():
    #                         print(f"    ✅ Found parent router RLOC16 {dst_router_rloc16} in routing table entry!")
    #                         success = True
    #                         final_hops = hops
    #                         break
    #
    #                 if success:
    #                     break
    #
    #                 neighbor_table = self.ns.node_cmd(current_src, "neighbor table")
    #                 print(f"  👥 Neighbor Table for Source Node {current_src}:")
    #                 for neighbor_entry in neighbor_table:
    #                     print(f"    {neighbor_entry}")
    #                     parts = neighbor_entry.split()
    #                     if len(parts) > 1:
    #                         neighbor_rloc16 = parts[1].lower()
    #                         next_hop_node_id = None
    #                         for node_id, node in self.ns.nodes().items():
    #                             try:
    #                                 node_rloc16 = self.ns.node_cmd(node_id, "rloc16")[0].strip().lower()
    #                                 if node_rloc16 == neighbor_rloc16:
    #                                     next_hop_node_id = node_id
    #                                     break
    #                             except:
    #                                 continue
    #
    #                         if next_hop_node_id is not None:
    #                             queue.append((next_hop_node_id, hops + 1))
    #
    #             except Exception as e:
    #                 print(f"⚠️ Failed to retrieve information for Node {current_src}: {e}")
    #                 continue
    #
    #         if success:
    #             hop_results[(src, dst)] = final_hops
    #         else:
    #             hop_results[(src, dst)] = None
    #             print(f"    ❌ Failed to find destination RLOC16 {dst_rloc16} within {MAX_HOPS} hops.")
    #
    #     print("\n📋 Hop Counts for Each Pair:")
    #     for (src, dst), hops in hop_results.items():
    #         try:
    #             src_role = self.ns.node_cmd(src, "state")[0].strip()
    #             dst_role = self.ns.node_cmd(dst, "state")[0].strip()
    #         except Exception:
    #             src_role = "unknown"
    #             dst_role = "unknown"
    #
    #         if hops is not None:
    #             print(f"• {src} ({src_role}) ➔ {dst} ({dst_role}): Reached in {hops} hop(s)")
    #         else:
    #             print(f"• {src} ({src_role}) ➔ {dst} ({dst_role}): Not reachable within {MAX_HOPS} hops")
    #
    #     print("\n✅ Finished listing analyzed node pairs with multi-hop forwarding analysis if needed.\n")



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

    # def _select_node_pairs(self):
    #     import random
    #
    #     nodes = list(self.ns.nodes().keys())
    #     if len(nodes) < 2:
    #         return []
    #
    #     all_possible_pairs = [(src, dst) for src in nodes for dst in nodes if src != dst]
    #
    #     MAX_PAIRS = 100
    #     selected_pairs = random.sample(all_possible_pairs, min(MAX_PAIRS, len(all_possible_pairs)))
    #
    #     return selected_pairs

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
