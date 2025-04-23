import pyshark

# Load the .pcap file
cap = pyshark.FileCapture('current.pcap')

# Read packets one by one
for packet in cap:
    print(packet)
