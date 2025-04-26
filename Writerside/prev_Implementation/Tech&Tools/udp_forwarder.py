import socket
import threading

# Configuration
FORWARD_MAP = {
    9001: ('fd42:1337::3', 9002),  # node1 → node2
    9002: ('fd42:1337::2', 9001),  # node2 → node1
}

def forward(local_port, target_addr, target_port):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind(('::', local_port))
    print(f"Forwarding from port {local_port} to [{target_addr}]:{target_port}")

    while True:
        data, addr = sock.recvfrom(2048)
        sock.sendto(data, (target_addr, target_port))

# Start a thread per forwarder
for listen_port, (target_ip, target_port) in FORWARD_MAP.items():
    threading.Thread(target=forward, args=(listen_port, target_ip, target_port), daemon=True).start()

# Keep the main thread alive
input("Forwarders running. Press Enter to quit...\n")
