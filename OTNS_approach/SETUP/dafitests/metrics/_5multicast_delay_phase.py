# metrics/_5multicast_delay_phase.py

from OTNS_approach.SETUP.dafitests.otns.cli.OTNS import now
import time

class MulticastDelayPhase:
    def __init__(self, ns):
        self.ns = ns
        self.send_timestamp = None
        self.reception_times = {}  # {node_id: timestamp}

    def run(self):
        print("\n🚀 Starting Multicast Delay Phase (Steps 14-16)...\n")
        self._14_multicast_trigger()
        self._15_multicast_reception_logging()
        self._16_compute_mpd()
        print("\n✅ Multicast Delay Phase completed successfully!\n")
        return True

    def _14_multicast_trigger(self):
        print("\n📍 Step 14: Multicast Trigger (Moderate Flooding)\n")

        nodes = list(self.ns.nodes().keys())
        if not nodes:
            raise RuntimeError("No nodes available for multicast trigger.")

        multicast_address = "ff03::1"
        payload = "mcast-trigger"
        self.send_timestamp = time.time()  # Mark start time

        # Start CoAP listeners
        for nid in nodes:
            self.ns.node_cmd(nid, "coap start")
            self.ns.node_cmd(nid, "coap resource multicast-test")
        self.ns.go(1)

        print("⏳ Sending multicast flooding (5 times)...")
        for repeat in range(5):
            for nid in nodes:
                role = self.ns.node_cmd(nid, "state")[0].strip()
                if role in ["leader", "router"]:
                    self.ns.node_cmd(nid, f'coap post {multicast_address} multicast-test con {payload}')
                    print(f"🚀 Multicast sent by Node {nid} at {time.time():.6f}s (repeat {repeat})")
            self.ns.go(2)
            time.sleep(0.5)

        print("\n✅ Step 14: Multicast flooding completed.\n")

    def _15_multicast_reception_logging(self, timeout=30):
        print("\n📍 Step 15: Reception Logging\n")

        nodes = list(self.ns.nodes().keys())
        start_time = time.time()
        waited = 0

        print("⏳ Monitoring CoAP receptions...")

        while waited <= timeout:
            logs = self.ns.coaps()

            for msg in logs:
                src = msg.get("src")
                dst = msg.get("dst")
                uri = msg.get("uri")
                payload = msg.get("payload", "")

                if uri == "/multicast-test" and "mcast-trigger" in payload:
                    if dst not in self.reception_times:
                        self.reception_times[dst] = time.time()
                        print(f"✅ Node {dst} received multicast at {self.reception_times[dst]:.6f}s")

            if waited >= timeout:
                break

            self.ns.go(1)
            time.sleep(0.5)
            waited = time.time() - start_time

        if not self.reception_times:
            print("⚠️ No multicast receptions detected among nodes.")
        else:
            print("\n✅ Step 15: Some nodes received multicast!\n")

    def _16_compute_mpd(self):
        print("\n📍 Step 16: Compute MPD\n")

        if self.send_timestamp is None:
            raise RuntimeError("No multicast send timestamp recorded.")

        if not self.reception_times:
            print("⚠️ Step 16: No nodes received multicast. Cannot compute MPD.")
            return

        delays = {}
        for nid, recv_time in self.reception_times.items():
            delay = recv_time - self.send_timestamp
            delays[nid] = delay

        max_delay = max(delays.values())
        min_delay = min(delays.values())
        avg_delay = sum(delays.values()) / len(delays)

        print("Multicast Delay Results (seconds):")
        for nid, d in delays.items():
            print(f"Node {nid}: {d:.6f}s")

        print("\n🔎 MPD Analysis:")
        print(f"• Max Delay = {max_delay:.6f} seconds")
        print(f"• Min Delay = {min_delay:.6f} seconds")
        print(f"• Average Delay = {avg_delay:.6f} seconds")

        print("\n✅ Step 16: MPD computed successfully!\n")
