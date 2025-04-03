
# start :
```
 docker run --name codelab_otsim_ctnr -it --rm    --sysctl net.ipv6.conf.all.disable_ipv6=0  --cap-add=net_admin openthread/environment bash
```
# start new wsl window :
 
```
wt.exe wsl -d Ubuntu-22.04 -- bash -c "docker run --name codelab_otsim_ctnr -it --rm --sysctl net.ipv6.conf.all.disable_ipv6=0 --cap-add=net_admin openthread/environment bash"
```
# first sh 
```
  #!/bin/bash
  
  for INSTANCE_NUMBER in {1..3}; do
    wt.exe wsl -d Ubuntu-22.04 -- bash -c "
      docker run -it --rm \
        --sysctl net.ipv6.conf.all.disable_ipv6=0 \
        --cap-add=net_admin \
        openthread/environment bash -c '/openthread/build/examples/apps/cli/ot-cli-ftd $INSTANCE_NUMBER && bash'"
  done
```

# tmux 
```
#!/bin/bash

tmux kill-session -t ot_nodes 2>/dev/null

tmux new-session -d -s ot_nodes

for i in {1..5}; do
CMD="docker run -it --rm \
  --sysctl net.ipv6.conf.all.disable_ipv6=0 \
  --cap-add=NET_ADMIN \
  -v $(pwd)/node_files_PASHIOU:/node_files_PASHIOU \
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

```
# tmux 
```
Ctrl + b, then release and then ← or → 
```
# tmux + echo.sh + ftd
```
#!/bin/bash

FTD_num=4

tmux kill-session -t ot_nodes_ftd 2>/dev/null

tmux new-session -d -s ot_nodes_ftd

for i in $(seq 1 $FTD_num); do
CMD="docker run -it --rm \
  --sysctl net.ipv6.conf.all.disable_ipv6=0 \
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
```


# set keys 

## networkkey <>

Length: 16 bytes (128 bits)
Format: Hexadecimal (0–9, a–f)

`baddecafcafebeddabdabdab52840fdfd`
`00000000000000000000000000000000`
## commissioner joiner add * <>

Length: 6–32 characters
Format: Uppercase letters and digits

`KOFKOPO4UTI3NK8ATWDEUT1ERAN`
`A0000000000000000000000000000000`

# next part 
```bash
#!/bin/bash

FTD_num=2

tmux kill-session -t ot_nodes_ftd 2>/dev/null

tmux new-session -d -s ot_nodes_ftd

for i in $(seq 1 $FTD_num); do
CMD="docker run -it --rm \
  --sysctl net.ipv6.conf.all.disable_ipv6=0 \
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

tmux select-pane -t 0
tmux send-keys -t ot_nodes_ftd "factoryreset" C-m
tmux send-keys -t ot_nodes_ftd "dataset init new" C-m
tmux send-keys -t ot_nodes_ftd "dataset networkname BASELINE" C-m
#tmux send-keys -t ot_nodes_ftd "dataset channel 1" C-m # there is a problem when you specify that
#tmux send-keys -t ot_nodes_ftd "dataset extpanid 0010010010010010" C-m # there is a problem when you specify that
tmux send-keys -t ot_nodes_ftd "dataset panid 0x0001" C-m
tmux send-keys -t ot_nodes_ftd "dataset networkkey 00000000000000000000000000000001" C-m
sleep 1
tmux send-keys -t ot_nodes_ftd "dataset commit active" C-m
sleep 1
tmux send-keys -t ot_nodes_ftd "dataset" C-m
tmux send-keys -t ot_nodes_ftd "ifconfig up" C-m
#tmux send-keys -t ot_nodes_ftd "mode rsdn" C-m

tmux send-keys -t ot_nodes_ftd "thread start" C-m
sleep 10
tmux send-keys -t ot_nodes_ftd "state" C-m

tmux send-keys -t ot_nodes_ftd "commissioner start" C-m
sleep 1
tmux send-keys -t ot_nodes_ftd "commissioner joiner add * 0000000000000001" C-m

sleep 10
tmux send-keys -t ot_nodes_ftd "state" C-m





for i in $(seq 2 $FTD_num); do
  pane_id=$(($i - 1))  # match pane to FTD id
  tmux select-pane -t $pane_id
  tmux send-keys -t ot_nodes_ftd "factoryreset" C-m
  tmux send-keys -t ot_nodes_ftd "ifconfig up" C-m
  sleep 1
  tmux send-keys -t ot_nodes_ftd "eui64" C-m  # <- just to generate if missing
  tmux send-keys -t ot_nodes_ftd "joiner start 0000000000000001" C-m
tmux send-keys -t ot_nodes_ftd "ipaddr" C-m

done




sleep 10

for i in $(seq 1 $FTD_num); do
  pane_id=$(($i - 1))
  tmux select-pane -t $pane_id
  tmux send-keys -t ot_nodes_ftd "state" C-m
done
```