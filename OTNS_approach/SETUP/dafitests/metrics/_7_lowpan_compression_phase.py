import pyshark
import statistics

class LowpanCompressionPhase:
    def __init__(self, pcap_file, coap_pairs_step17):
        self.pcap_file = pcap_file
        self.coap_pairs = coap_pairs_step17
        self.header_sizes = []  # list of compressed IPv6+UDP header sizes
        self.results = {}  # {(src, dst): compression ratio}

    def run(self):
        print("\n🚞 Starting 6LoWPAN Compression Efficiency Phase (Step 19)...\n")
        self._capture_lowpan_headers()
        self._analyze_compression()
        self._report_summary()
        print("\n✅ 6LoWPAN Compression Efficiency Phase completed successfully!\n")
        return True

    def _capture_lowpan_headers(self):
        print("\n🔎 Parsing PCAP file for 6LoWPAN CoAP packets...")

        capture = pyshark.FileCapture(
            self.pcap_file,
            display_filter="lowpan and coap"
        )

        for packet in capture:
            try:
                # Frame info
                frame_len = int(packet.length)

                # 6LoWPAN compressed size for headers
                if hasattr(packet, 'lowpan'):  # if lowpan field exists
                    lowpan_header_size = int(packet.lowpan.get_field('header_length'), 16)

                    # Assume payload length = frame_len - header_size
                    payload_len = frame_len - lowpan_header_size

                    self.header_sizes.append(lowpan_header_size)
                    print(f"Packet: Header={lowpan_header_size}B, Frame={frame_len}B, Payload~={payload_len}B")

            except Exception as e:
                print(f"⚠️ Skipped packet: {e}")

        capture.close()

    def _analyze_compression(self):
        print("\n📊 Calculating Compression Ratios...")

        for header_size in self.header_sizes:
            uncompressed_size = 48  # IPv6 (40) + UDP (8)
            compression_ratio = header_size / uncompressed_size
            self.results.setdefault('compression_ratios', []).append(compression_ratio)

    def _report_summary(self):
        if not self.results.get('compression_ratios'):
            print("⚠️ No valid 6LoWPAN CoAP packets found.")
            return

        ratios = self.results['compression_ratios']

        avg_ratio = statistics.mean(ratios)
        min_ratio = min(ratios)
        max_ratio = max(ratios)

        print("\n🔎 6LoWPAN Compression Efficiency Summary:")
        print(f"• Average Compression Ratio: {avg_ratio:.2f}")
        print(f"• Minimum Compression Ratio: {min_ratio:.2f}")
        print(f"• Maximum Compression Ratio: {max_ratio:.2f}")

        if avg_ratio > 0.6:
            print("⚠️ Warning: Compression ratio seems suboptimal.")

        if avg_ratio <= 0.5:
            print("✅ Excellent compression achieved.")
