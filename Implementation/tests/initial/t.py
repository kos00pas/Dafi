from otns import OTNS
import logging

logging.basicConfig(level=logging.INFO)

otns = OTNS(otns_path="/home/otns/go/bin/otns")

# Set full path to your built ot-cli-ftd
cli_path = "/home/otns/otns/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"

node_id = otns.add("router", executable=cli_path)
from time import sleep
sleep(10)

print(f"Router added with ID: {node_id}")