from scapy.all import rdpcap
from scapy.layers.dot15d4 import Dot15d4Data

def analyze_lowpan_udp(filepath):
    packets = rdpcap(filepath)

    packet_counter = 0
    coap_packet_counter = 0

    with open("../lowpan_packets.txt", "w") as f:
        for idx, pkt in enumerate(packets):
            if not pkt.haslayer(Dot15d4Data):
                continue  # Only analyze Data frames

            payload = bytes(pkt.payload.payload)
            if len(payload) < 10:  # Minimal size for lowpan+UDP headers
                continue

            # Skip first 2 bytes (IPHC compressed Dispatch and Encoding)
            udp_start = 2

            if len(payload) < udp_start + 8:
                continue  # Not enough bytes for UDP header

            try:
                source_port = int.from_bytes(payload[udp_start:udp_start+2], byteorder='big')
                dest_port = int.from_bytes(payload[udp_start+2:udp_start+4], byteorder='big')
                udp_length = int.from_bytes(payload[udp_start+4:udp_start+6], byteorder='big')

                # Check if destination port == 5683 (CoAP)
                if dest_port == 5683:
                    coap_payload = payload[udp_start+8:]

                    f.write(f"• CoAP Packet {coap_packet_counter+1}:\n")
                    f.write(f"   Source Port: {source_port}\n")
                    f.write(f"   Destination Port: {dest_port}\n")
                    f.write(f"   UDP Length: {udp_length}\n")
                    f.write(f"   CoAP Payload (hex): {' '.join(f'{b:02x}' for b in coap_payload)}\n\n")

                    coap_packet_counter += 1

                packet_counter += 1

            except Exception as e:
                print(f"⚠️ Parsing error at packet {idx+1}: {e}")
                continue

    print(f"\n✅ Total packets checked: {packet_counter}")
    print(f"✅ Total CoAP packets (port 5683) found: {coap_packet_counter}")
