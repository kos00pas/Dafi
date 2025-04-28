#!/bin/bash

# Paths
NODE1_BIN="/mnt/c/Users/kos00/OneDrive - University of Cyprus/PhD/PhD_Lessons/IoT project/Last_Part/src/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"
NODE2_BIN="/mnt/c/Users/kos00/OneDrive - University of Cyprus/PhD/PhD_Lessons/IoT project/Last_Part/src/openthread/build/simulation/examples/apps/cli/ot-cli-ftd"

# Node IDs
NODE1_ID=3
NODE2_ID=4

# Common Network Settings
NETWORK_NAME="MyTestNet"
PANID="0x1234"
CHANNEL="15"
NETWORK_KEY="00112233445566778899aabbccddeeff"

# Session name
SESSION="openthread_simulation"

# Clean up any previous session
tmux kill-session -t $SESSION 2>/dev/null

# Start a new detached session
tmux new-session -d -s $SESSION

# Split the window into two vertical panes
tmux split-window -h

# Launch Node 1 in left pane
tmux send-keys -t $SESSION:0.0 "$NODE1_BIN $NODE1_ID" C-m
sleep 1

# Launch Node 2 in right pane
tmux send-keys -t $SESSION:0.1 "$NODE2_BIN $NODE2_ID" C-m
sleep 1

# --- Setup Node 1 ---
tmux send-keys -t $SESSION:0.0 "factoryreset" C-m
sleep 1
tmux send-keys -t $SESSION:0.0 "dataset networkname $NETWORK_NAME" C-m
tmux send-keys -t $SESSION:0.0 "dataset panid $PANID" C-m
tmux send-keys -t $SESSION:0.0 "dataset channel $CHANNEL" C-m
tmux send-keys -t $SESSION:0.0 "dataset networkkey $NETWORK_KEY" C-m
tmux send-keys -t $SESSION:0.0 "dataset commit active" C-m
sleep 1
tmux send-keys -t $SESSION:0.0 "ifconfig up" C-m
tmux send-keys -t $SESSION:0.0 "thread start" C-m
sleep 5
tmux send-keys -t $SESSION:0.0 "state" C-m

# --- Setup Node 2 ---
tmux send-keys -t $SESSION:0.1 "factoryreset" C-m
sleep 3
tmux send-keys -t $SESSION:0.1 "dataset networkname $NETWORK_NAME" C-m
tmux send-keys -t $SESSION:0.1 "dataset panid $PANID" C-m
tmux send-keys -t $SESSION:0.1 "dataset channel $CHANNEL" C-m
tmux send-keys -t $SESSION:0.1 "dataset networkkey $NETWORK_KEY" C-m
tmux send-keys -t $SESSION:0.1 "dataset commit active" C-m
sleep 1
tmux send-keys -t $SESSION:0.1 "ifconfig up" C-m
tmux send-keys -t $SESSION:0.1 "thread start" C-m
sleep 5
tmux send-keys -t $SESSION:0.1 "state" C-m

# --- Setup CoAP ---
tmux send-keys -t $SESSION:0.0 "coap start" C-m
tmux send-keys -t $SESSION:0.0 "coap resource test" C-m

tmux send-keys -t $SESSION:0.1 "coap start" C-m
sleep 5

# --- You still need to manually send the CoAP POST ---
echo ""
echo "🌟 Nodes are started and configured."
echo "👉 Now manually find Node1 IP with 'ipaddr' and send CoAP POST from Node2."
echo ""

# Attach to the tmux session
tmux attach -t $SESSION
