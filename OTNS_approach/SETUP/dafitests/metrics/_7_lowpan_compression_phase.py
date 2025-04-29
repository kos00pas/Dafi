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

import pyshark
import statistics
class LowpanCompressionPhase:
    def __init__(self, ns, pcap_file="./lowpan.pcap"):
        self.ns = ns
        self.pcap_file = pcap_file
        self.global_role_pair_compression = {}  # <-- only here!
        self.role_pair_compression = {}

        print("Step 19! Starting 6LoWPAN Compression Efficiency Phase...")

    def run(self, role_batches):



        # Initialize lists for metrics
        compressed_header_sizes = []
        compression_efficiencies = []
        compression_ratios = []

        cap = pyshark.FileCapture('./current.pcap', use_json=True, include_raw=True)

        for packet in cap:
            if '6LOWPAN' in packet and 'IPV6' in packet and 'UDP' in packet:

                ipv6_header_size = 40
                udp_header_size = 8
                original_header_size = ipv6_header_size + udp_header_size

                try:
                    udp_length = int(packet.udp.length)
                    udp_payload_size = udp_length - udp_header_size
                    total_frame_length = int(packet.length)

                    # Step 1: Get raw packet
                    raw_bytes = bytes.fromhex(packet.get_raw_packet().hex())

                    # Step 2: Estimate MAC header end
                    mac_end_offset = 21  # Typical for non-secured 802.15.4

                    # Step 3: Estimate UDP payload size (end of compressed header)
                    compressed_header_size = total_frame_length - mac_end_offset - udp_payload_size
                    compressed_header_size = max(compressed_header_size, 0)

                except Exception as e:
                    print(f"Error parsing raw bytes: {e}")
                    continue

                # Step 4: Efficiency calculation
                if original_header_size > 0:
                    compression_efficiency = (original_header_size - compressed_header_size) / original_header_size
                    compression_ratio = compressed_header_size / original_header_size
                else:
                    compression_efficiency = 0
                    compression_ratio = 0

                compressed_header_sizes.append(compressed_header_size)
                compression_efficiencies.append(compression_efficiency)
                compression_ratios.append(compression_ratio)

                # Print per-packet info
                # print(f"Packet number: {packet.number}")
                # print(f"Total frame length: {total_frame_length} bytes")
                # print(f"UDP payload size: {udp_payload_size} bytes")
                # print(f"Compressed header size: {compressed_header_size} bytes")
                # print(f"Compression Efficiency: {compression_efficiency * 100:.2f}%")
                # print(f"Compression Ratio: {compression_ratio * 100:.2f}%")

                # 6LoWPAN header field insights
                try:
                    cid = packet['6LOWPAN'].context_identifier_extension
                    # print(f"CID (Context Identifier Extension): {cid}")
                except AttributeError: pass
                    # print("CID: Not present")

                try:
                    src_mode = packet['6LOWPAN'].source_address_mode
                    dst_mode = packet['6LOWPAN'].destination_address_mode
                    # print(f"Source Address Compression Mode: {src_mode}")
                    # print(f"Destination Address Compression Mode: {dst_mode}")
                except AttributeError: pass
                    # print("Address compression modes: Not available")

                try:
                    port_mode = packet['6LOWPAN'].udp_ports
                    # print(f"UDP Port Compression Mode: {port_mode}")
                except AttributeError: pass
                    # print("UDP Port Compression: Not available")

                # print('---')

        cap.close()

        # Summary
        if compressed_header_sizes:
            print("\n=== Summary (Mean Values) ===")
            print(f"Average Compressed Header Size: {statistics.mean(compressed_header_sizes):.2f} bytes")
            print(f"Average Compression Efficiency: {statistics.mean(compression_efficiencies) * 100:.2f}%")
            print(f"Average Compression Ratio: {statistics.mean(compression_ratios) * 100:.2f}%")
        else:
            print("No valid packets found to calculate averages.")



    # def run(self, role_batches):
    #     print(f"🔵 LowpanCompressionPhase: Running for {sum(len(v) for v in role_batches.values())} node pairs.")
    #     # 🧹 FLASH current.pcap
    #     try:
    #         open("current.pcap", "wb").close()
    #         print("🧹 Flashed current.pcap — now clean and empty.")
    #     except Exception as e:
    #         print(f"⚠️ Failed to flash current.pcap: {e}")
    #     time.sleep(4)
    #     for role_pair, node_pairs in role_batches.items():
    #         if not node_pairs:
    #             continue
    #         src_role, dst_role = role_pair
    #         print(f"\n🔵 Role {src_role.upper()} ➔ {dst_role.upper()} : {len(node_pairs)} pairs")
    #
    #         for src, dst in node_pairs:
    #             send_time = time.time()
    #             print(f"• Sending from Node {src} ({src_role}) ➔ Node {dst} ({dst_role}) at {send_time:.6f}s")
    #
    #             packet = self.find_packet_for_pair("current.pcap", src, dst)
    #
    #             if packet:
    #                 print(f"🔎 Packet Length: {len(packet)} bytes")
    #                 # (you could also inspect more fields here)
    #
    #     print("\n✅ Finished listing all node pairs and timestamps.\n")
    #
    # def find_packet_for_pair(self, pcap_file, src, dst):
    #     packets = rdpcap(pcap_file)
    #
    #     for idx, pkt in enumerate(packets):
    #         if not pkt.haslayer(Dot15d4Data):
    #             continue  # Only check 802.15.4 packets
    #
    #         try:
    #             payload = bytes(pkt.payload.payload)
    #
    #             if len(payload) < 10:
    #                 continue
    #
    #             payload_str = ''.join(chr(b) for b in payload if 32 <= b <= 126)
    #
    #             if f"coap-{src}-to-{dst}" in payload_str:
    #                 print(f"✅ Found matching packet {idx} for {src} ➔ {dst}")
    #                 return pkt  # 🧠 Return the full packet
    #
    #         except Exception as e:
    #             print(f"⚠️ Error parsing packet {idx}: {e}")
    #             continue
    #
    #     print(f"❌ No matching packet found for {src} ➔ {dst}")
    #     return None
    #
    #
    #


    #     print("\n🚞 Step 19: Analyzing 6LoWPAN Header Compression from PCAP...\n")
    #     print(coap_pairs)
    #
    #     # Only one big communication at start
    #     self._start_coap_communication(coap_pairs)
    #
    #     role_batches = self.split_coap_pairs_by_role_pairs(coap_pairs)
    #
    #     for role_pair, pairs in role_batches.items():
    #         if not pairs:
    #             continue  # Skip empty
    #
    #         src_role, dst_role = role_pair
    #         print(f"\n🔵 Analyzing Experiment: {src_role.upper()} ➔ {dst_role.upper()} with {len(pairs)} pairs\n")
    #
    #         print("\n⏳ Waiting a few seconds to allow PCAP to flush...\n")
    #         self.ns.go(10)
    #         time.sleep(2)
    #
    #         # 🛠️ Analyze the original current.pcap, but pass allowed pairs
    #         self.pcap_file = "current.pcap"
    #         self._analyze_pcap_with_scapy(role_pair=role_pair, allowed_pairs=pairs)
    #
    #         self._print_summary()
    #
    #         print(f"\n✅ Finished Experiment: {src_role.upper()} ➔ {dst_role.upper()}\n")
    #         print("=" * 60)
    #
    #     # 🛠️ After all role-pair analyses
    #     self._print_final_summary()
    #
    # def _print_final_summary(self):
    #     print("\n📋 📊 FINAL COMPRESSION SUMMARY ACROSS ALL ROLE-PAIRS 📊 📋\n")
    #
    #     if not self.global_role_pair_compression:
    #         print("⚠️ No global compression data collected.\n")
    #         return
    #
    #     print(f"{'SOURCE ➔ DESTINATION':<25} | {'#PACKETS':<10} | {'AVG COMPRESSION RATIO':<20}")
    #     print("-" * 65)
    #     for role_pair, ratios in sorted(self.global_role_pair_compression.items()):
    #         src_role, dst_role = role_pair
    #         num_packets = len(ratios)
    #         avg_compression = sum(ratios) / num_packets if num_packets > 0 else 0
    #         print(f"{src_role.upper()} ➔ {dst_role.upper():<15} | {num_packets:<10} | {avg_compression:.2f}")
    #     print("-" * 65)
    #     print("✅ Final compression analysis completed.\n")
    #
    # def _print_summary(self):
    #     print("\n📋 Final Summary Report:")
    #
    #     # General file-based results
    #     print("\n📝 6LoWPAN General Packet Analysis (Frame, Compression, Payload):\n")
    #     try:
    #         with open("lowpan_packets.txt", "r") as f:
    #             lines = f.readlines()
    #             # for line in lines:
    #             #     print(line.strip())  # <-- Keep commented if too much output
    #     except Exception as e:
    #         print(f"⚠️ Could not read lowpan_packets.txt: {e}")
    #
    #     print("\n📝 Compression Analysis by Role-Pairs:\n")
    #
    #     if not hasattr(self, "role_pair_compression") or not self.role_pair_compression:
    #         print("⚠️ No role-pair compression data collected.\n")
    #     else:
    #         print(f"{'SOURCE ➔ DESTINATION':<25} | {'#PACKETS':<10} | {'AVG COMPRESSION RATIO':<20}")
    #         print("-" * 65)
    #         for role_pair, ratios in sorted(self.role_pair_compression.items()):
    #             src_role, dst_role = role_pair
    #             num_packets = len(ratios)
    #             avg_compression = sum(ratios) / num_packets if num_packets > 0 else 0
    #             print(f"{src_role.upper()} ➔ {dst_role.upper():<15} | {num_packets:<10} | {avg_compression:.2f}")
    #         print("-" * 65)
    #         print("✅ End of Compression Summary.\n")
    #
    # def _start_coap_communication(self, coap_pairs):
    #     print("\n⚡ Starting strong CoAP communication between node pairs...\n")
    #
    #     # --- Step 1: Map Node ID ➔ Role
    #     self.node_roles = {}
    #     for node_id in self.ns.nodes().keys():
    #         try:
    #             role = self.ns.node_cmd(node_id, "state")[0].strip()
    #             self.node_roles[node_id] = role
    #             print(f"• Node {node_id}: Role = {role}")
    #         except Exception as e:
    #             print(f"⚠️ Failed to get role for Node {node_id}: {e}")
    #
    #     self.coap_role_pairs = []
    #
    #     # --- Step 2: Start CoAP servers
    #     for nid in self.ns.nodes().keys():
    #         try:
    #             self.ns.node_cmd(nid, "coap start")
    #             self.ns.node_cmd(nid, "coap resource test-resource")
    #             print(f"✅ CoAP server started on Node {nid}")
    #         except Exception as e:
    #             print(f"⚠️ Failed to start CoAP server on Node {nid}: {e}")
    #
    #     self.ns.go(5)  # let servers stabilize
    #
    #     # --- Step 3: Send CoAP messages and build role pairs
    #     for src, dst in coap_pairs:
    #         if src == dst:
    #             continue
    #
    #         try:
    #             dst_mleid = self.ns.node_cmd(dst, "ipaddr mleid")[0]
    #             payload = f"coap-{src}-to-{dst}"
    #
    #             cmd = f'coap put {dst_mleid} test-resource con {payload}'
    #             print(f"Sending CoAP payload: coap-{src}-to-{dst}")
    #
    #             res = self.ns.node_cmd(src, cmd)
    #             print(f"✅ CoAP put from Node {src} ➔ Node {dst}")
    #
    #             src_role = self.node_roles.get(src, "unknown")
    #             dst_role = self.node_roles.get(dst, "unknown")
    #             self.coap_role_pairs.append((src, dst, src_role, dst_role))
    #
    #         except Exception as e:
    #             print(f"⚠️ CoAP send error {src} ➔ {dst}: {e}")
    #         self.ns.go(0.5)  # short simulation pause
    #
    #     # --- Final wait after sending
    #     total_pairs = len(coap_pairs)
    #     wait_time = max(10, total_pairs * 0.2)
    #     print(f"\n⏳ Waiting {wait_time:.1f} simulated seconds to flush CoAP traffic...")
    #     self.ns.go(wait_time)
    #
    # def _analyze_pcap_with_scapy(self, role_pair=None, allowed_pairs=None):
    #     print("\n🔍 Advanced Analysis: Parsing 802.15.4 + 6LoWPAN IPHC using Scapy...\n")
    #
    #     packets = rdpcap(self.pcap_file)
    #
    #     mac_overhead = 15
    #     packet_counter = 0
    #     coap_detected_counter = 0
    #     compression_ratios = []
    #     stats = {
    #         "cid_used": 0,
    #         "source_address_elided": 0,
    #         "dest_address_elided": 0,
    #         "udp_header_compressed": 0,
    #     }
    #
    #     with open("lowpan_packets.txt", "w") as f:
    #         for idx, pkt in enumerate(packets):
    #             if not pkt.haslayer(Dot15d4Data):
    #                 continue
    #
    #             frame_size = len(pkt)
    #             full_bytes = bytes(pkt.payload.payload)
    #             skip_header_bytes = 20
    #             if len(full_bytes) <= skip_header_bytes:
    #                 continue
    #
    #             payload = full_bytes[skip_header_bytes:]
    #             payload_size = len(payload)
    #
    #             iphc_info = self._parse_iphc_fields(payload)
    #
    #             if iphc_info:
    #                 compressed_hdr_size = 2
    #                 iphc_summary = f"TF={iphc_info['tf']} NH={iphc_info['nh']} HLIM={iphc_info['hlim']} SAM={iphc_info['sam']} DAM={iphc_info['dam']}"
    #                 self._update_compression_statistics(stats, iphc_info)
    #             else:
    #                 compressed_hdr_size = max(0, frame_size - mac_overhead - payload_size)
    #                 iphc_summary = "N/A"
    #
    #             compression_ratio = self._calculate_compression_ratio(compressed_hdr_size)
    #             packet_counter += 1
    #
    #             result_line = (f"• Packet {packet_counter}: Frame={frame_size}B, "
    #                            f"CompHeader={compressed_hdr_size}B, "
    #                            f"Payload={payload_size}B, "
    #                            f"CompressionRatio={compression_ratio:.2f}, "
    #                            f"IPHC={iphc_summary}")
    #
    #             payload_hex = " ".join(f"{b:02x}" for b in payload)
    #
    #             f.write(result_line + "\n")
    #             f.write(f"Payload Hex: {payload_hex}\n\n")
    #
    #             # ====== NEW FILTERING BASED ON role_pair and allowed_pairs ======
    #             try:
    #                 payload_str = ''.join(chr(b) for b in payload if 32 <= b <= 126)
    #
    #                 if "coap-" in payload_str:
    #                     parts = payload_str.split("-")
    #                     src_id = int(parts[1])
    #                     dst_id = int(parts[3])
    #
    #                     # 🛠️ NEW FILTER:
    #                     if allowed_pairs and (src_id, dst_id) not in allowed_pairs:
    #                         continue  # skip this packet, it's not for current role batch
    #
    #                     src_role = self.node_roles.get(src_id, "unknown")
    #                     dst_role = self.node_roles.get(dst_id, "unknown")
    #                     current_role_pair = (src_role, dst_role)
    #
    #                     if current_role_pair != role_pair:
    #                         continue  # skip if role does not match
    #
    #                     if current_role_pair not in self.role_pair_compression:
    #                         self.role_pair_compression[current_role_pair] = []
    #
    #                     self.role_pair_compression[current_role_pair].append(compression_ratio)
    #                     coap_detected_counter += 1
    #
    #                     print(f"✅ Detected CoAP Packet: src={src_id}({src_role}) ➔ dst={dst_id}({dst_role}) "
    #                           f"CompressionRatio={compression_ratio:.2f}")
    #
    #             except Exception as e:
    #                 print(f"⚠️ Skip packet {packet_counter} if parsing CoAP payload fails")
    #                 pass
    #
    #     if packet_counter == 0:
    #         print("❌ No 6LoWPAN IPHC packets detected!")
    #     else:
    #         avg_ratio = sum(compression_ratios) / len(compression_ratios)
    #         print("\n===== 6LoWPAN General Packet Summary =====\n")
    #         print(f"✅ Successfully parsed {packet_counter} packets!")
    #         print(f"✅ Average Compression Ratio: {avg_ratio:.2f}")
    #         print(f"✅ CID usage: {stats['cid_used']} packets")
    #         print(f"✅ Source Address Elided: {stats['source_address_elided']} packets")
    #         print(f"✅ Destination Address Elided: {stats['dest_address_elided']} packets")
    #         print(f"✅ UDP Header Compressed: {stats['udp_header_compressed']} packets")
    #         print(f"✅ CoAP Packets Detected: {coap_detected_counter}")
    #         print("===== End of 6LoWPAN Summary =====\n")
    #
    #         if self.role_pair_compression:
    #             print("\n===== Compression by Role-Pair =====\n")
    #             for role_pair, ratios in self.role_pair_compression.items():
    #                 avg_role_ratio = sum(ratios) / len(ratios)
    #                 print(f"{role_pair[0]} ➔ {role_pair[1]}: "
    #                       f"{len(ratios)} packets, "
    #                       f"Avg Compression Ratio = {avg_role_ratio:.2f}")
    #             print("\n===== End of Role-Pair Summary =====\n")
    #
    #     if self.role_pair_compression:
    #         for role_pair, ratios in self.role_pair_compression.items():
    #             if role_pair not in self.global_role_pair_compression:
    #                 self.global_role_pair_compression[role_pair] = []
    #             self.global_role_pair_compression[role_pair].extend(ratios)
    #
    # def _analyze_lowpan_udp(self):
    #     print("\n🔍 Deep Analysis: Extracting UDP/CoAP packets from lowpan.pcap...\n")
    #
    #     packets = rdpcap(self.pcap_file)
    #
    #     packet_counter = 0
    #     coap_packet_counter = 0
    #     coap_results = []
    #
    #     with open("lowpan_udp_coap_packets.txt", "w") as f:
    #         for idx, pkt in enumerate(packets):
    #             if not pkt.haslayer(Dot15d4Data):
    #                 continue  # Only analyze Data frames
    #
    #             payload = bytes(pkt.payload.payload)
    #             if len(payload) < 10:
    #                 continue
    #
    #             udp_start = 2
    #             if len(payload) < udp_start + 8:
    #                 continue
    #
    #             try:
    #                 source_port = int.from_bytes(payload[udp_start:udp_start + 2], byteorder='big')
    #                 dest_port = int.from_bytes(payload[udp_start + 2:udp_start + 4], byteorder='big')
    #                 udp_length = int.from_bytes(payload[udp_start + 4:udp_start + 6], byteorder='big')
    #
    #                 if dest_port == 5683:
    #                     coap_payload = payload[udp_start + 8:]
    #                     coap_packet_counter += 1
    #
    #                     coap_line = (f"• CoAP Packet {coap_packet_counter}: SrcPort={source_port}, "
    #                                  f"DstPort={dest_port}, UDP Length={udp_length}, "
    #                                  f"Payload (hex): {' '.join(f'{b:02x}' for b in coap_payload)}")
    #
    #                     f.write(coap_line + "\n\n")
    #                     coap_results.append(coap_line)
    #
    #                 packet_counter += 1
    #
    #             except Exception as e:
    #                 print(f"⚠️ Parsing error at packet {idx + 1}: {e}")
    #                 continue
    #
    #     if coap_packet_counter == 0:
    #         print("❌ No CoAP packets (port 5683) detected!")
    #     else:
    #         print("\n===== CoAP Packet Summary =====\n")
    #         # for line in coap_results:
    #         #     print(line)
    #         print(f"\n✅ Successfully extracted {coap_packet_counter} CoAP packets!\n")
    #         print("===== End of CoAP Summary =====\n")
    #
    # # ---------------------------------------------------------
    # def _parse_iphc_fields(self, packet_bytes):
    #     """Parse 6LoWPAN IPHC header fields."""
    #     if len(packet_bytes) < 2:
    #         return None
    #
    #     first_byte = packet_bytes[0]
    #     second_byte = packet_bytes[1]
    #
    #     dispatch = (first_byte & 0b11100000) >> 5
    #     if dispatch != 0b011:
    #         return None  # Not IPHC
    #
    #     tf = (first_byte & 0b00011000) >> 3
    #     nh = (first_byte & 0b00000100) >> 2
    #     hlim = (first_byte & 0b00000011)
    #
    #     cid = (second_byte & 0b10000000) >> 7
    #     sac = (second_byte & 0b01000000) >> 6
    #     sam = (second_byte & 0b00110000) >> 4
    #     m = (second_byte & 0b00001000) >> 3
    #     dac = (second_byte & 0b00000100) >> 2
    #     dam = (second_byte & 0b00000011)
    #
    #     return {
    #         "tf": tf,
    #         "nh": nh,
    #         "hlim": hlim,
    #         "cid": cid,
    #         "sac": sac,
    #         "sam": sam,
    #         "m": m,
    #         "dac": dac,
    #         "dam": dam,
    #     }
    # def _calculate_compression_ratio(self, compressed_hdr_size):
    #     """Calculate compression ratio based on standard uncompressed IPv6+UDP header (48 bytes)."""
    #     uncompressed_size = 48.0  # IPv6 (40B) + UDP (8B)
    #     return compressed_hdr_size / uncompressed_size
    #
    # def _update_compression_statistics(self, stats, iphc_info):
    #     """Update statistics based on parsed IPHC fields."""
    #     if iphc_info['cid'] == 1:
    #         stats['cid_used'] += 1
    #     if iphc_info['sam'] == 3:
    #         stats['source_address_elided'] += 1
    #     if iphc_info['dam'] == 3:
    #         stats['dest_address_elided'] += 1
    #     if iphc_info['nh'] == 1:
    #         stats['udp_header_compressed'] += 1
    #
    # def split_coap_pairs_by_role_pairs(self, coap_pairs):
    #     """
    #     Splits the original coap_pairs into 7 groups based on (src_role ➔ dst_role).
    #     """
    #
    #     # Mapping from (src_role, dst_role) -> list of (src_id, dst_id)
    #     role_pair_batches = {
    #         ('leader', 'router'): [],
    #         ('leader', 'child'): [],
    #         ('router', 'router'): [],
    #         ('router', 'child'): [],
    #         ('router', 'leader'): [],
    #         ('child', 'router'): [],
    #         ('child', 'leader'): [],
    #     }
    #
    #     for src, dst in coap_pairs:
    #         src_role = self.node_roles.get(src, "unknown")
    #         dst_role = self.node_roles.get(dst, "unknown")
    #         role_pair = (src_role, dst_role)
    #
    #         if role_pair in role_pair_batches:
    #             role_pair_batches[role_pair].append((src, dst))
    #         else:
    #             print(f"⚠️ Unknown role pair ({src_role} ➔ {dst_role}), skipping src={src} dst={dst}")
    #
    #     return role_pair_batches
    #
    # # def _dump_all_packets_to_txt(self):
    # #     print("\n🔍 Dumping all packets from lowpan.pcap to lowpan_packets.txt...\n")
    # #
    # #     capture = pyshark.FileCapture(self.pcap_file)
    # #
    # #     try:
    # #         with open("lowpan_packets.txt", "w") as f:
    # #             for idx, packet in enumerate(capture):
    # #                 f.write(f"--- Packet {idx + 1} ---\n")
    # #                 f.write(str(packet))
    # #                 f.write("\n\n")
    # #         print("✅ All packets dumped to lowpan_packets.txt successfully!")
    # #     except Exception as e:
    # #         print(f"⚠️ Failed to dump packets: {e}")
    # #     finally:
    # #         capture.close()
    #
    # # def _print_first_packet(self):
    # #
    # #
    # #     print("\n🔍 Opening PCAP and printing first packet (no filter)...\n")
    # #     capture = pyshark.FileCapture(self.pcap_file)  # NO display_filter here!
    # #
    # #     try:
    # #         packet = next(iter(capture))
    # #         print("📦 Full Packet Content:")
    # #         print(packet)
    # #     except StopIteration:
    # #         print("❌ No packets found in PCAP.")
    # #     finally:
    # #         capture.close()


