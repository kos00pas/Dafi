from otns_original import OTNS
from time import sleep
import logging

logging.basicConfig(level=logging.INFO)

otns = OTNS(otns_path="/home/otns/go/bin/otns")
otns.speed = 1000000  # full-speed simulation

otns.web()

ot_cli = "/home/otns/src/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"

leader_id = otns.add("router", executable=ot_cli)

# Simulate CLI commands for the leader
# otns.node_cmd(leader_id, "factoryreset")
# sleep(0.1)
otns.node_cmd(leader_id, "dataset init new")
sleep(0.1)
otns.node_cmd(leader_id, "dataset networkname BASELINE")
otns.node_cmd(leader_id, "dataset panid 0x0001")
otns.node_cmd(leader_id, "dataset networkkey 00000000000000000000000000000001")
otns.node_cmd(leader_id, "dataset commit active")
otns.node_cmd(leader_id, "ifconfig up")
otns.node_cmd(leader_id, "thread start")

# Wait for node to become leader
for attempt in range(30):  # try for up to 30 seconds
    state = otns.node_cmd(leader_id, "state")[0]
    print(f"Waiting for leader... (state: {state})")
    if state == "leader":
        break
    sleep(1)
else:
    raise RuntimeError("Node never became leader")

print(f"Leader state: {state}")



# Start commissioner and allow joiners
# otns.node_cmd(leader_id, "commissioner start")
# sleep(2)
# otns.node_cmd(leader_id, "commissioner joiner add * 0000000000000001 300")

# Run the simulation for 100 simulated seconds
otns.go(100)