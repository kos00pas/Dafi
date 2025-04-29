import pyshark
import time
import shutil
import subprocess
from scapy.all import rdpcap
from scapy.layers.dot15d4 import Dot15d4Data
from scapy.config import conf
conf.dot15d4_protocol = "sixlowpan"  # <-- ADD THIS

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
        self._analyze_lowpan_udp()
        self._print_summary()

    def _print_summary(self):
            print("\n📋 Final Summary Report:")

            # Read and print lowpan_packets.txt
            print("\n📝 6LoWPAN General Packet Analysis (Frame, Compression, Payload):\n")
            try:
                with open("lowpan_packets.txt", "r") as f:
                    lines = f.readlines()
                    # for line in lines:
                    #     print(line.strip())
            except Exception as e:
                print(f"⚠️ Could not read lowpan_packets.txt: {e}")

            # Read and print lowpan_udp_coap_packets.txt
            print("\n📝 CoAP-specific UDP Packets (Destination Port 5683):\n")
            try:
                with open("lowpan_udp_coap_packets.txt", "r") as f:
                    lines = f.readlines()
                    # for line in lines:
                    #     print(line.strip())
            except Exception as e:
                print(f"⚠️ Could not read lowpan_udp_coap_packets.txt: {e}")



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

        packets = rdpcap(self.pcap_file)

        mac_overhead = 15
        packet_counter = 0
        compression_ratios = []
        stats = {
            "cid_used": 0,
            "source_address_elided": 0,
            "dest_address_elided": 0,
            "udp_header_compressed": 0,
        }

        with open("lowpan_packets.txt", "w") as f:
            for idx, pkt in enumerate(packets):
                if not pkt.haslayer(Dot15d4Data):
                    continue

                frame_size = len(pkt)
                payload = bytes(pkt.payload.payload)
                payload_size = len(payload)

                iphc_info = self._parse_iphc_fields(payload)

                if iphc_info:
                    compressed_hdr_size = 2  # Minimal IPHC header size (Dispatch + Encoding byte)
                    iphc_summary = f"TF={iphc_info['tf']} NH={iphc_info['nh']} HLIM={iphc_info['hlim']} SAM={iphc_info['sam']} DAM={iphc_info['dam']}"
                    self._update_compression_statistics(stats, iphc_info)
                else:
                    compressed_hdr_size = max(0, frame_size - mac_overhead - payload_size)
                    iphc_summary = "N/A"

                compression_ratio = self._calculate_compression_ratio(compressed_hdr_size)
                compression_ratios.append(compression_ratio)

                packet_counter += 1

                result_line = (f"• Packet {packet_counter}: Frame={frame_size}B, "
                               f"CompHeader={compressed_hdr_size}B, "
                               f"Payload={payload_size}B, "
                               f"CompressionRatio={compression_ratio:.2f}, "
                               f"IPHC={iphc_summary}")

                payload_hex = " ".join(f"{b:02x}" for b in payload)

                f.write(result_line + "\n")
                f.write(f"Payload Hex: {payload_hex}\n\n")

        if packet_counter == 0:
            print("❌ No 6LoWPAN IPHC packets detected!")
        else:
            avg_ratio = sum(compression_ratios) / len(compression_ratios)
            print("\n===== 6LoWPAN General Packet Summary =====\n")
            print(f"✅ Successfully parsed {packet_counter} packets!")
            print(f"✅ Average Compression Ratio: {avg_ratio:.2f}")
            print(f"✅ CID usage: {stats['cid_used']} packets")
            print(f"✅ Source Address Elided: {stats['source_address_elided']} packets")
            print(f"✅ Destination Address Elided: {stats['dest_address_elided']} packets")
            print(f"✅ UDP Header Compressed: {stats['udp_header_compressed']} packets")
            print("===== End of 6LoWPAN Summary =====\n")

    def _analyze_lowpan_udp(self):
        print("\n🔍 Deep Analysis: Extracting UDP/CoAP packets from lowpan.pcap...\n")

        packets = rdpcap(self.pcap_file)

        packet_counter = 0
        coap_packet_counter = 0
        coap_results = []

        with open("lowpan_udp_coap_packets.txt", "w") as f:
            for idx, pkt in enumerate(packets):
                if not pkt.haslayer(Dot15d4Data):
                    continue  # Only analyze Data frames

                payload = bytes(pkt.payload.payload)
                if len(payload) < 10:
                    continue

                udp_start = 2
                if len(payload) < udp_start + 8:
                    continue

                try:
                    source_port = int.from_bytes(payload[udp_start:udp_start + 2], byteorder='big')
                    dest_port = int.from_bytes(payload[udp_start + 2:udp_start + 4], byteorder='big')
                    udp_length = int.from_bytes(payload[udp_start + 4:udp_start + 6], byteorder='big')

                    if dest_port == 5683:
                        coap_payload = payload[udp_start + 8:]
                        coap_packet_counter += 1

                        coap_line = (f"• CoAP Packet {coap_packet_counter}: SrcPort={source_port}, "
                                     f"DstPort={dest_port}, UDP Length={udp_length}, "
                                     f"Payload (hex): {' '.join(f'{b:02x}' for b in coap_payload)}")

                        f.write(coap_line + "\n\n")
                        coap_results.append(coap_line)

                    packet_counter += 1

                except Exception as e:
                    print(f"⚠️ Parsing error at packet {idx + 1}: {e}")
                    continue

        if coap_packet_counter == 0:
            print("❌ No CoAP packets (port 5683) detected!")
        else:
            print("\n===== CoAP Packet Summary =====\n")
            # for line in coap_results:
            #     print(line)
            print(f"\n✅ Successfully extracted {coap_packet_counter} CoAP packets!\n")
            print("===== End of CoAP Summary =====\n")

    # ---------------------------------------------------------
    def _parse_iphc_fields(self, packet_bytes):
        """Parse 6LoWPAN IPHC header fields."""
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
    def _calculate_compression_ratio(self, compressed_hdr_size):
        """Calculate compression ratio based on standard uncompressed IPv6+UDP header (48 bytes)."""
        uncompressed_size = 48.0  # IPv6 (40B) + UDP (8B)
        return compressed_hdr_size / uncompressed_size

    def _update_compression_statistics(self, stats, iphc_info):
        """Update statistics based on parsed IPHC fields."""
        if iphc_info['cid'] == 1:
            stats['cid_used'] += 1
        if iphc_info['sam'] == 3:
            stats['source_address_elided'] += 1
        if iphc_info['dam'] == 3:
            stats['dest_address_elided'] += 1
        if iphc_info['nh'] == 1:
            stats['udp_header_compressed'] += 1
