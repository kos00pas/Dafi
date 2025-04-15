#!/bin/bash

echo "[INFO] Starting OpenThread POSIX CLI node: $NODE_NAME"

exec /app/openthread/build/posix/src/posix/ot-cli 'spinel+hdlc+forkpty:///app/openthread/build/simulation/examples/apps/ncp/ot-rcp?forkpty-arg=1'

