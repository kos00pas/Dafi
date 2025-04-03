
# start :
 docker run --name codelab_otsim_ctnr -it --rm    --sysctl net.ipv6.conf.all.disable_ipv6=0  --cap-add=net_admin openthread/environment bash

# start new wsl window :
 
wt.exe wsl -d Ubuntu-22.04 -- bash -c "docker run --name codelab_otsim_ctnr -it --rm --sysctl net.ipv6.conf.all.disable_ipv6=0 --cap-add=net_admin openthread/environment bash"

# first sh 
#!/bin/bash

for INSTANCE_NUMBER in {1..3}; do
  wt.exe wsl -d Ubuntu-22.04 -- bash -c "
    docker run -it --rm \
      --sysctl net.ipv6.conf.all.disable_ipv6=0 \
      --cap-add=net_admin \
      openthread/environment bash -c '/openthread/build/examples/apps/cli/ot-cli-ftd $INSTANCE_NUMBER && bash'"
done

# tmux 
#!/bin/bash

tmux kill-session -t ot_nodes 2>/dev/null

tmux new-session -d -s ot_nodes

for i in 1 2 3; do
  CMD="docker run -it --rm \
    --sysctl net.ipv6.conf.all.disable_ipv6=0 \
    --cap-add=NET_ADMIN \
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



