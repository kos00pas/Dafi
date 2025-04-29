# metrics/_5multicast_delay_phase.py
from datetime import datetime

from OTNS_approach.SETUP.dafitests.otns.cli.OTNS import now
import time

class MulticastDelayPhase:
    def __init__(self, ns ,result_file):
        self.ns = ns
        self.result_file = result_file
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
        self.result_file.write("\n========= [ 5.  Multicast Propagation Delay (MPD) ] =========\n")
        self.result_file.write("Step 14 Multicast Trigger\n")
        self.result_file.flush()
        print("\n📍 Step 14: Multicast Trigger (Moderate Flooding)\n")

        from OTNS_approach.SETUP.dafitests.otns.cli.OTNS import now  # use simulation clock
        start_time = datetime.now()

        nodes = list(self.ns.nodes().keys())
        if not nodes:
            raise RuntimeError("No nodes available for multicast trigger.")

        multicast_address = "ff02::1"
        self.send_timestamp = now()
        print(f"🕐 Recorded simulation send timestamp: {self.send_timestamp}s")

        # Step 1: Start CoAP and multicast-test resource
        print("⚙️ Starting CoAP server and multicast-test resource on all nodes...")
        for nid in nodes:
            self.ns.node_cmd(nid, "coap start")
            self.ns.node_cmd(nid, "coap resource multicast-test")

        # Step 2: Allow MLR registration to settle
        print("⏳ Waiting 3s simulation time for MLR to settle...")
        self.ns.go(3)
        time.sleep(2)

        # ✅ Step 3: Clear logs so we only track multicast CoAP for this flood
        self.ns.coap_recv_logs.clear()

        # Step 4: Multicast Flooding
        print("\n🚀 Sending multicast flooding (5 times)...")
        for repeat in range(5):
            for nid in nodes:
                role = self.ns.node_cmd(nid, "state")[0].strip()
                if role in ["leader", "router"]:
                    payload = f"mcast-trigger-{repeat}"
                    self.ns.node_cmd(nid, f'coap post {multicast_address} multicast-test con {payload}')
                    print(f"📡 Multicast sent by Node {nid} at simulation t={now()}s (repeat {repeat})")
            self.ns.go(2)
            time.sleep(0.5)

        # Step 5: After flooding, scan captured logs for CoAP receptions
        for logline in self.ns.coap_recv_logs:
            if "Node<" in logline and "coap=recv" in logline and "multicast-test" in logline:
                try:
                    start = logline.index("Node<") + len("Node<")
                    end = logline.index(">", start)
                    nid = int(logline[start:end])
                    if nid not in self.reception_times:
                        self.reception_times[nid] = now()
                        print(f"✅ Node {nid} received multicast at simulation time {self.reception_times[nid]:.6f}s")
                except Exception:
                    continue

        print("\n✅ Step 14: Multicast flooding completed.\n")
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.result_file.write(f"\tDone: {duration:.6f}s\n--------------------------------------------\n")
        self.result_file.write("")
        self.result_file.flush()

    def _15_multicast_reception_logging(self):
        print("\n📍 Step 15: Multicast Reception Logging (Inlined in Step 14)\n")
        self.result_file.write("Step 15 Multicast Reception Logging\n")
        self.result_file.flush()

        start_time = datetime.now()

        if not self.reception_times:
            print("⚠️ Step 15: No multicast receptions recorded during Step 14.")
        else:
            print(f"✅ Step 15: {len(self.reception_times)} node(s) recorded multicast reception during Step 14.")

        duration = (datetime.now() - start_time).total_seconds()
        self.result_file.write(f"\tDone: {duration:.6f}s\n--------------------------------------------\n")
        self.result_file.write("")
        self.result_file.flush()


    def _16_compute_mpd(self):
        self.result_file.write("Step 16 Compute MPD\n")
        self.result_file.flush()
        print("\n📍 Step 16: Compute MPD\n")
        start_time = datetime.now()

        if self.send_timestamp is None:
            raise RuntimeError("No multicast send timestamp recorded.")

        if not self.reception_times:
            print("⚠️ Step 16: No nodes received multicast. Cannot compute MPD.")
            duration = (datetime.now() - start_time).total_seconds()
            self.result_file.write(f"\tDone: {duration:.6f}s")
            self.result_file.write("")
            self.result_file.flush()
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
        duration = (datetime.now() - start_time).total_seconds()
        self.result_file.write(f"\tDone: {duration:.6f}s\n--------------------------------------------\n")
        self.result_file.write("")
        self.result_file.flush()

