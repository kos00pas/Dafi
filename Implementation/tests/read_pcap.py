import pyshark

cap = pyshark.FileCapture('_4topologyConverge/current.pcap', use_json=True)

for i, pkt in enumerate(cap):
    print(pkt)
    print(pkt.pretty_print())  # like tshark -V
    # if i >= 4:
    #     break
