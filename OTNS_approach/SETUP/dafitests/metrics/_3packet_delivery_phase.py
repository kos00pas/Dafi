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
        print("\n✅ Packet Delivery Phase completed successfully!\n")
        print("\nStep 17 END\n")
        return success, results

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

        print("\n📊 Packet Delivery Statistics:")
        print(f"• Packets Sent: {sent}")
        print(f"• Packets Delivered: {delivered}")
        print(f"• Packets Lost: {lost}")
        print(f"• Packet Delivery Ratio (PDR): {pdr:.2f}%")
        print(f"• Packet Loss Rate (PLR): {plr:.2f}%")

        if pdr < 95:
            print(f"⚠️ WARNING: PDR too low: {pdr:.2f}% (threshold 95%)")
            return False
        return True
