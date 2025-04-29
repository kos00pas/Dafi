# from scapy.all import rdpcap
# from scapy.layers.dot15d4 import Dot15d4, Dot15d4Data
#
# def parse_lowpan_iphc(packet_bytes):
#     """Very basic 6LoWPAN IPHC parsing."""
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
#
# def analyze_pcap(filepath):
#     packets = rdpcap(filepath)
#
#     for idx, pkt in enumerate(packets):
#         if not pkt.haslayer(Dot15d4Data):
#             continue  # Only analyze Data frames
#
#         # Access payload after MAC header
#         payload = bytes(pkt.payload.payload)
#
#         if len(payload) < 2:
#             continue
#
#         iphc_info = parse_lowpan_iphc(payload)
#         if iphc_info:
#             print(f"• Packet {idx + 1}: {iphc_info}")
#
# # Example usage
# analyze_pcap("../lowpan.pcap")
from scapy.all import rdpcap

# packets = rdpcap('../current.pcap')
# for pkt in packets:
#     print(pkt.summary())
#


import pyshark
import statistics

# Initialize lists for metrics
compressed_header_sizes = []
compression_efficiencies = []
compression_ratios = []

cap = pyshark.FileCapture('../lowpan.pcap', use_json=True, include_raw=True)

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
        print(f"Packet number: {packet.number}")
        print(f"Total frame length: {total_frame_length} bytes")
        print(f"UDP payload size: {udp_payload_size} bytes")
        print(f"Compressed header size: {compressed_header_size} bytes")
        print(f"Compression Efficiency: {compression_efficiency * 100:.2f}%")
        print(f"Compression Ratio: {compression_ratio * 100:.2f}%")

        # 6LoWPAN header field insights
        try:
            cid = packet['6LOWPAN'].context_identifier_extension
            print(f"CID (Context Identifier Extension): {cid}")
        except AttributeError:
            print("CID: Not present")

        try:
            src_mode = packet['6LOWPAN'].source_address_mode
            dst_mode = packet['6LOWPAN'].destination_address_mode
            print(f"Source Address Compression Mode: {src_mode}")
            print(f"Destination Address Compression Mode: {dst_mode}")
        except AttributeError:
            print("Address compression modes: Not available")

        try:
            port_mode = packet['6LOWPAN'].udp_ports
            print(f"UDP Port Compression Mode: {port_mode}")
        except AttributeError:
            print("UDP Port Compression: Not available")

        print('---')

cap.close()

# Summary
if compressed_header_sizes:
    print("\n=== Summary (Mean Values) ===")
    print(f"Average Compressed Header Size: {statistics.mean(compressed_header_sizes):.2f} bytes")
    print(f"Average Compression Efficiency: {statistics.mean(compression_efficiencies) * 100:.2f}%")
    print(f"Average Compression Ratio: {statistics.mean(compression_ratios) * 100:.2f}%")
else:
    print("No valid packets found to calculate averages.")
