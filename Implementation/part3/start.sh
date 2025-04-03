#!/bin/bash

FTD_num=2
docker rm -f $(docker ps -aq) 2>/dev/null
fuser -k 9001/udp 9002/udp 2>/dev/null

tmux kill-session -t ot_nodes_ftd 2>/dev/null

tmux new-session -d -s ot_nodes_ftd

# Create custom Docker network if not exists
docker network inspect ot-net >/dev/null 2>&1 || \
docker network create ot-net


for i in $(seq 1 $FTD_num); do
  CMD="docker run -it --rm \
    --network ot-net \
    --name ot-node-$i \
    --sysctl net.ipv6.conf.all.disable_ipv6=0 \
    --sysctl net.ipv6.conf.all.forwarding=1 \
    --cap-add=NET_ADMIN \
    -v $(pwd)/node_files_PASHIOU:/node_files_PASHIOU \
    openthread/environment"



  if [ $i -eq 1 ]; then
    tmux send-keys -t ot_nodes_ftd "$CMD" C-m
  else
    tmux split-window -t ot_nodes_ftd
    tmux select-layout -t ot_nodes_ftd tiled
    tmux send-keys -t ot_nodes_ftd "$CMD" C-m
  fi
done

tmux attach -t ot_nodes_ftd

sleep 0.2

for i in $(seq 0 $(($FTD_num - 1))); do

  pane_id=$(($i + 1))  # Map FTD id to pane index
  tmux select-pane -t $i
  tmux send-keys -t ot_nodes_ftd "./node_files_PASHIOU/echo.sh $pane_id" C-m
done



sleep 0.2

for i in $(seq 1 $FTD_num); do
  pane_id=$(($i - 1))  # Map FTD id to pane index
  tmux select-pane -t $pane_id
  tmux send-keys -t ot_nodes_ftd "/openthread/build/examples/apps/cli/ot-cli-ftd $i" C-m
done

#fortheleader
sleep 1
#tmux send-keys -t $pane_id "ping ot-node-1" C-m

tmux select-pane -t 0
tmux send-keys -t ot_nodes_ftd "factoryreset" C-m
sleep 0.1
tmux send-keys -t ot_nodes_ftd "dataset init new" C-m
sleep 0.1
tmux send-keys -t ot_nodes_ftd "dataset networkname BASELINE" C-m
#tmux send-keys -t ot_nodes_ftd "dataset channel 1" C-m # there is a problem when you specify that
#tmux send-keys -t ot_nodes_ftd "dataset extpanid 0010010010010010" C-m # there is a problem when you specify that
tmux send-keys -t ot_nodes_ftd "dataset panid 0x0001" C-m
sleep 0.1
tmux send-keys -t ot_nodes_ftd "dataset networkkey 00000000000000000000000000000001" C-m
sleep 0.1
tmux send-keys -t ot_nodes_ftd "dataset commit active" C-m
sleep 0.1
tmux send-keys -t ot_nodes_ftd "dataset" C-m
sleep 0.1
tmux send-keys -t ot_nodes_ftd "ifconfig up" C-m
#tmux send-keys -t ot_nodes_ftd "mode rsdn" C-m

tmux send-keys -t ot_nodes_ftd "thread start" C-m
sleep 10
tmux send-keys -t ot_nodes_ftd "state" C-m
sleep 0.1
tmux send-keys -t ot_nodes_ftd "commissioner start" C-m
sleep 10
tmux send-keys -t ot_nodes_ftd "commissioner joiner add * 0000000000000001 300" C-m

sleep 15
tmux send-keys -t ot_nodes_ftd "state" C-m
sleep 1




for i in $(seq 2 $FTD_num); do
  pane_id=$(($i - 1))  # match pane to FTD id
  tmux select-pane -t $pane_id
  tmux send-keys -t ot_nodes_ftd "factoryreset" C-m
  tmux send-keys -t ot_nodes_ftd "panid 0xffff" C-m
  tmux send-keys -t ot_nodes_ftd "ifconfig up" C-m

  sleep 1
  tmux send-keys -t ot_nodes_ftd "eui64" C-m  # <- just to generate if missing
  sleep 1

  tmux send-keys -t ot_nodes_ftd "joiner start 0000000000000001" C-m
  tmux send-keys -t ot_nodes_ftd "ipaddr" C-m

done




sleep 10

for i in $(seq 1 $FTD_num); do
  pane_id=$(($i - 1))
  tmux select-pane -t $pane_id
  tmux send-keys -t ot_nodes_ftd "state" C-m
done