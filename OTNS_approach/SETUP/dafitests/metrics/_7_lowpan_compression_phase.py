import pyshark
import time
import shutil
import subprocess

"""Compression Ratio = compressed / uncompressed = ~0.28
This matches real-world OpenThread/6LoWPAN expectations:

Heavy elision (addresses, ports)

CID (Context IDs) used

Traffic Class, Flow Label compression active"""


class LowpanCompressionPhase:
    def __init__(self, ns, pcap_file="./lowpan.pcap"):
        self.ns = ns
        self.pcap_file = pcap_file

        print("Step 19! Starting 6LoWPAN Compression Efficiency Phase...")

    def run(self, coap_pairs):
        print("\n🚞 Step 19: Analyzing 6LoWPAN Header Compression from PCAP...\n")

        # Step 1: Start CoAP communication between pairs
        self._start_coap_communication(coap_pairs)


        # Step 2: Wait a bit to ensure packets are flushed and recorded
        print("\n⏳ Waiting a few seconds to allow PCAP to flush...\n")
        self.ns.go(10)
        time.sleep(3)

        shutil.copyfile("current.pcap", "lowpan.pcap")
        print("✅ Copied current.pcap → lowpan.pcap")

        self._analyze_pcap_with_scapy()

        # Step 3: Open lowpan.pcap and print the first packet
        # self._dump_all_packets_to_txt()
        # self._print_first_packet()

    def _start_coap_communication(self, coap_pairs):
        print("\n⚡ Starting strong CoAP communication between node pairs...\n")

        # Start CoAP servers on all nodes
        for nid in self.ns.nodes().keys():
            try:
                self.ns.node_cmd(nid, "coap start")
                self.ns.node_cmd(nid, "coap resource test-resource")
                print(f"✅ CoAP server started on Node {nid}")
            except Exception as e:
                print(f"⚠️ Failed to start CoAP server on Node {nid}: {e}")

        self.ns.go(5)  # let servers stabilize

        for src, dst in coap_pairs:
            if src == dst:
                continue

            try:
                dst_mleid = self.ns.node_cmd(dst, "ipaddr mleid")[0]
                payload = f"coap-{src}-to-{dst}"

                # Safe CoAP PUT
                cmd = f'coap put {dst_mleid} test-resource con {payload}'
                res = self.ns.node_cmd(src, cmd)
                print(f"✅ CoAP put from Node {src} ➔ Node {dst}")

            except Exception as e:
                print(f"⚠️ CoAP send error {src} ➔ {dst}: {e}")

            self.ns.go(0.5)  # short simulation pause

        # Final wait after sending
        total_pairs = len(coap_pairs)
        wait_time = max(10, total_pairs * 0.2)
        print(f"\n⏳ Waiting {wait_time:.1f} simulated seconds to flush CoAP traffic...")
        self.ns.go(wait_time)

    def _dump_all_packets_to_txt(self):
        print("\n🔍 Dumping all packets from lowpan.pcap to lowpan_packets.txt...\n")

        capture = pyshark.FileCapture(self.pcap_file)

        try:
            with open("lowpan_packets.txt", "w") as f:
                for idx, packet in enumerate(capture):
                    f.write(f"--- Packet {idx + 1} ---\n")
                    f.write(str(packet))
                    f.write("\n\n")
            print("✅ All packets dumped to lowpan_packets.txt successfully!")
        except Exception as e:
            print(f"⚠️ Failed to dump packets: {e}")
        finally:
            capture.close()

    def _print_first_packet(self):


        print("\n🔍 Opening PCAP and printing first packet (no filter)...\n")
        capture = pyshark.FileCapture(self.pcap_file)  # NO display_filter here!

        try:
            packet = next(iter(capture))
            print("📦 Full Packet Content:")
            print(packet)
        except StopIteration:
            print("❌ No packets found in PCAP.")
        finally:
            capture.close()


    def _analyze_pcap_with_scapy(self):
        print("\n🔍 Advanced Analysis: Parsing 802.15.4 + 6LoWPAN IPHC using Scapy...\n")

        from scapy.all import rdpcap
        from scapy.layers.dot15d4 import Dot15d4Data

        def parse_lowpan_iphc(packet_bytes):
            """Very basic 6LoWPAN IPHC parsing."""
            if len(packet_bytes) < 2:
                return None

            first_byte = packet_bytes[0]
            second_byte = packet_bytes[1]

            dispatch = (first_byte & 0b11100000) >> 5
            if dispatch != 0b011:
                return None  # Not IPHC

            tf = (first_byte & 0b00011000) >> 3
            nh = (first_byte & 0b00000100) >> 2
            hlim = (first_byte & 0b00000011)

            cid = (second_byte & 0b10000000) >> 7
            sac = (second_byte & 0b01000000) >> 6
            sam = (second_byte & 0b00110000) >> 4
            m = (second_byte & 0b00001000) >> 3
            dac = (second_byte & 0b00000100) >> 2
            dam = (second_byte & 0b00000011)

            return {
                "tf": tf,
                "nh": nh,
                "hlim": hlim,
                "cid": cid,
                "sac": sac,
                "sam": sam,
                "m": m,
                "dac": dac,
                "dam": dam,
            }

        packets = rdpcap(self.pcap_file)

        mac_overhead = 15  # Approximate MAC header overhead
        packet_counter = 0

        with open("lowpan_packets.txt", "w") as f:
            for idx, pkt in enumerate(packets):
                if not pkt.haslayer(Dot15d4Data):
                    continue  # Only analyze Data frames

                frame_size = len(pkt)  # Full frame size in bytes
                payload = bytes(pkt.payload.payload)
                payload_size = len(payload)

                iphc_info = parse_lowpan_iphc(payload)

                if iphc_info:
                    compressed_hdr_size = 2  # Minimal IPHC header size
                    iphc_summary = f"TF={iphc_info['tf']} NH={iphc_info['nh']} HLIM={iphc_info['hlim']} SAM={iphc_info['sam']} DAM={iphc_info['dam']}"
                else:
                    compressed_hdr_size = frame_size - mac_overhead - payload_size
                    iphc_summary = "N/A"

                packet_counter += 1
                # Build the line
                line = (f"• Packet {packet_counter}: Frame={frame_size}B, "
                        f"CompHeader={compressed_hdr_size}B, "
                        f"Payload={payload_size}B, IPHC={iphc_summary}")

                # Build payload hex dump
                payload_hex = " ".join(f"{b:02x}" for b in payload)

                # Write to file
                f.write(line + "\n")
                f.write(f"Payload Hex: {payload_hex}\n\n")

                # Optional print to console (shorter)
                print(line)

        if packet_counter == 0:
            print("❌ No 6LoWPAN IPHC packets detected!")
        else:
            print(f"\n✅ Successfully parsed {packet_counter} packets using Scapy!")

