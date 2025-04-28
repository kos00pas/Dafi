import subprocess
import threading
import time

# Start Node 1
node1 = subprocess.Popen(
    ['/mnt/c/Users/kos00/OneDrive - University of Cyprus/PhD/PhD_Lessons/IoT project/Last_Part/src/openthread/build/simulation/examples/apps/cli/ot-cli-ftd', '3'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

# Start Node 2
node2 = subprocess.Popen(
    ['/mnt/c/Users/kos00/OneDrive - University of Cyprus/PhD/PhD_Lessons/IoT project/Last_Part/src/openthread/build/simulation/examples/apps/cli/ot-cli-ftd', '4'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

def read_output(name, process):
    while True:
        line = process.stdout.readline()
        if line:
            print(f"[{name}] {line.strip()}")
            if "coap request from" in line:
                print(f"🎯 CoAP Request received by {name}: {line.strip()}")
        else:
            break

# Reader threads for each node
threading.Thread(target=read_output, args=("Node1", node1), daemon=True).start()
threading.Thread(target=read_output, args=("Node2", node2), daemon=True).start()

def send_command(process, command):
    try:
        if process.poll() is None:  # Check if still alive
            print(f"⚡ Sending command: {command}")
            process.stdin.write(command + '\n')
            process.stdin.flush()
        else:
            print(f"⚠️  Cannot send '{command}' - Process already exited.")
    except BrokenPipeError:
        print(f"❌ Broken pipe when sending: {command}")


# Small wait
time.sleep(1)

# Setup common parameters
network_name = "MyTestNet"
panid = "0x1234"
channel = "15"
network_key = "00112233445566778899aabbccddeeff"  # 16 bytes in hex

# Start Node 1
send_command(node1, "factoryreset")
time.sleep(1)

send_command(node1, f"dataset networkname {network_name}")
send_command(node1, f"dataset panid {panid}")
send_command(node1, f"dataset channel {channel}")
send_command(node1, f"dataset networkkey {network_key}")
send_command(node1, "dataset commit active")
send_command(node1, "ifconfig up")
send_command(node1, "thread start")

time.sleep(80)  # <<< less is enough here (20s)

send_command(node1, "state")

# Start Node 2
send_command(node2, "factoryreset")
time.sleep(3)

send_command(node2, f"dataset networkname {network_name}")
send_command(node2, f"dataset panid {panid}")
send_command(node2, f"dataset channel {channel}")
send_command(node2, f"dataset networkkey {network_key}")
send_command(node2, "dataset commit active")
send_command(node2, "ifconfig up")
send_command(node2, "thread start")

time.sleep(100)  # <<< less is enough

send_command(node2, "state")

# Start CoAP server on Node 1
send_command(node1, "coap start")
send_command(node1, "coap resource test")

# Start CoAP client on Node 2
send_command(node2, "coap start")
time.sleep(50)  # <<< less is enough
#
# # ----
# # Assume you manually read Node 1 address for now:
# node1_address = "fd21:42ef:7711:fdfa:62ed:5e4c:a909:f16c"
# # ----
#
# # Send CoAP POST from Node 2 to Node 1
# send_command(node2, f"coap post {node1_address} test HelloWorld")
#
#
# Keep program alive
send_command(node1, "state")
send_command(node2, "state")
# Keep program alive
send_command(node1, "ipaddr")
send_command(node2, "ipaddr")

# Keep program alive
send_command(node1, "router table")
send_command(node2, "router table")
# Keep program alive
send_command(node1, "neighbor table")
send_command(node2, "neighbor table")


#
# while True:
#     time.sleep(1)
