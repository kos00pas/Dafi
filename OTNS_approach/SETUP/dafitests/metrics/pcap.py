from scapy.all import rdpcap
from scapy.layers.dot15d4 import Dot15d4, Dot15d4Data

def parse_lowpan_iphc(packet_bytes):
    """Very basic 6LoWPAN IPHC parsing."""
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

def analyze_pcap(filepath):
    packets = rdpcap(filepath)

    for idx, pkt in enumerate(packets):
        if not pkt.haslayer(Dot15d4Data):
            continue  # Only analyze Data frames

        # Access payload after MAC header
        payload = bytes(pkt.payload.payload)

        if len(payload) < 2:
            continue

        iphc_info = parse_lowpan_iphc(payload)
        if iphc_info:
            print(f"• Packet {idx + 1}: {iphc_info}")

# Example usage
analyze_pcap("../lowpan.pcap")
