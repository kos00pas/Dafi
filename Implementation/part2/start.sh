#!/bin/bash

tmux kill-session -t ot_nodes 2>/dev/null

tmux new-session -d -s ot_nodes

for i in 1 2 3; do
CMD="docker run -it --rm \
  --sysctl net.ipv6.conf.all.disable_ipv6=0 \
  --cap-add=NET_ADMIN \
  -v $(pwd)/node_files:/node_files \
  openthread/environment \
  bash -c '/openthread/build/examples/apps/cli/ot-cli-ftd $i; exec bash'"


  if [ $i -eq 1 ]; then
    tmux send-keys -t ot_nodes "$CMD" C-m
  else
    tmux split-window -t ot_nodes
    tmux select-layout -t ot_nodes tiled
    tmux send-keys -t ot_nodes "$CMD" C-m
  fi
done

tmux attach -t ot_nodes
