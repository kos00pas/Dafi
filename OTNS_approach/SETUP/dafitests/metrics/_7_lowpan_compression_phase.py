# metrics/_7_lowpan_compression_phase.py

import pyshark

class LowpanCompressionPhase:
    def __init__(self, ns, pcap_file="capture.pcap"):
        self.ns = ns
        self.pcap_file = pcap_file
        print("Step 19! Starting 6LoWPAN Compression Efficiency Phase...")

    def run(self, coap_pairs):
        print("\n🚞 Step 19: Analyzing 6LoWPAN Header Compression from PCAP...\n")
        capture = pyshark.FileCapture(self.pcap_file, display_filter="coap")

        results = {}

        for packet in capture:
            try:
                frame_len = int(packet.length)
                src_mac = packet["wpan"].src64.replace(":", "").lower()
                dst_mac = packet["wpan"].dst64.replace(":", "").lower()

                ipv6_header_size = 40  # standard IPv6 header size
                udp_header_size = 8    # standard UDP header size
                uncompressed_size = ipv6_header_size + udp_header_size

                if hasattr(packet, "lowpan"):
                    compressed_hdr_size = int(packet.lowpan.length)
                else:
                    compressed_hdr_size = uncompressed_size  # fallback

                payload_len = int(packet["udp"].length) if hasattr(packet, "udp") else 0

                compression_ratio = compressed_hdr_size / uncompressed_size

                key = (src_mac, dst_mac)

                if key not in results:
                    results[key] = []

                results[key].append({
                    "frame_size": frame_len,
                    "compressed_hdr_size": compressed_hdr_size,
                    "payload_len": payload_len,
                    "compression_ratio": compression_ratio
                })

            except Exception as e:
                print(f"⚠️ Error processing packet: {e}")
                continue

        capture.close()

        self._analyze_results(results, coap_pairs)

    def _analyze_results(self, results, coap_pairs):
        print("\n📋 6LoWPAN Compression Summary per Node Pair:")

        for (src, dst) in coap_pairs:
            try:
                src_mac = self.ns.node_cmd(src, "extaddr")[0].strip().lower()
                dst_mac = self.ns.node_cmd(dst, "extaddr")[0].strip().lower()
                key = (src_mac, dst_mac)

                if key not in results:
                    print(f"• {src} ➔ {dst}: No CoAP packets captured.")
                    continue

                compressed_sizes = [entry["compressed_hdr_size"] for entry in results[key]]
                compression_ratios = [entry["compression_ratio"] for entry in results[key]]

                avg_compressed_size = sum(compressed_sizes) / len(compressed_sizes)
                avg_compression_ratio = sum(compression_ratios) / len(compression_ratios)

                print(f"• {src} ➔ {dst}: Avg Compressed Header = {avg_compressed_size:.2f} bytes | Compression Ratio = {avg_compression_ratio:.2f}")

            except Exception as e:
                print(f"⚠️ Error summarizing for {src} ➔ {dst}: {e}")

        print("\n✅ Step 19 Complete: 6LoWPAN Compression Efficiency Analysis Finished.\n")
