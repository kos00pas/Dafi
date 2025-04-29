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

        self._analyze_pcap()

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

    def _analyze_pcap(self):
        print("\n🔍 Advanced Analysis: Parsing Real 6LoWPAN IPHC Headers...\n")

        capture = pyshark.FileCapture(self.pcap_file, use_json=True)

        packet_data = []
        mac_overhead = 15  # Typical MAC header overhead (still used for backup estimation)

        def parse_iphc_header(raw_bytes):
            """Parse the first two bytes of 6LoWPAN IPHC header."""
            if len(raw_bytes) < 2:
                print("⚠️ Not enough bytes for IPHC parsing.")
                return None

            first_byte = raw_bytes[0]
            second_byte = raw_bytes[1]

            dispatch = (first_byte & 0b11100000) >> 5
            if dispatch != 0b011:
                print(f"⚠️ Dispatch value not IPHC (got {bin(dispatch)})")
                return None

            # First Byte
            tf = (first_byte & 0b00011000) >> 3
            nh = (first_byte & 0b00000100) >> 2
            hlim = (first_byte & 0b00000011)

            # Second Byte
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

        for packet in capture:
            try:
                if 'udp' not in packet:
                    continue  # Only care about UDP packets

                frame_size = int(packet.length)  # Full IEEE 802.15.4 frame size

                udp_layer = packet['udp']
                payload_size = int(udp_layer.length) - 8  # Subtract UDP header

                compressed_hdr_size = None
                iphc_fields = None

                # Try parsing the lowpan header if available
                if hasattr(packet, 'lowpan'):
                    try:
                        raw_bytes = bytes.fromhex(packet.lowpan.get_raw_packet().hex())
                        iphc_fields = parse_iphc_header(raw_bytes)
                        compressed_hdr_size = len(raw_bytes)
                    except Exception as e:
                        print(f"⚠️ Failed lowpan raw parsing: {e}")
                if compressed_hdr_size is None:
                    # fallback to estimation
                    compressed_hdr_size = frame_size - payload_size - mac_overhead

                packet_data.append({
                    "frame_size": frame_size,
                    "compressed_hdr_size": compressed_hdr_size,
                    "payload_size": payload_size,
                    "iphc_fields": iphc_fields,
                })

            except Exception as e:
                print(f"⚠️ Packet skipped due to error: {e}")
                continue

        capture.close()

        if not packet_data:
            print("❌ No UDP packets found.")
            return

        # Print all packet information
        print("\n📋 Captured UDP Packets Summary:")
        for idx, pkt in enumerate(packet_data):
            iphc_info = pkt['iphc_fields']
            if iphc_info:
                iphc_summary = f"TF={iphc_info['tf']} NH={iphc_info['nh']} HLIM={iphc_info['hlim']} SAM={iphc_info['sam']} DAM={iphc_info['dam']}"
            else:
                iphc_summary = "N/A"

            print(f"• Packet {idx + 1}: Frame={pkt['frame_size']}B, "
                  f"CompHeader={pkt['compressed_hdr_size']}B, "
                  f"Payload={pkt['payload_size']}B, "
                  f"IPHC={iphc_summary}")

        # Optional: average compression
        avg_compression_ratio = sum(pkt['compressed_hdr_size'] for pkt in packet_data) / (len(packet_data) * 48)
        print(f"\n📊 Average Compression Ratio: {avg_compression_ratio:.2f}")

    def tshark_extract_lowpan_fields(pcap_file):
        tshark_cmd = [
            "tshark",
            "-r", pcap_file,
            "-Y", "lowpan",  # filter only 6LoWPAN packets
            "-T", "fields",
            "-e", "lowpan.iphc.tf",
            "-e", "lowpan.iphc.nh",
            "-e", "lowpan.iphc.hlim",
            "-e", "lowpan.iphc.sam",
            "-e", "lowpan.iphc.dam"
        ]

        try:
            output = subprocess.check_output(tshark_cmd, stderr=subprocess.STDOUT)
            decoded_output = output.decode('utf-8')
            print("✅ TShark output:")
            print(decoded_output)
            return decoded_output

        except subprocess.CalledProcessError as e:
            print("❌ Error calling TShark:", e.output.decode('utf-8'))
            return None
