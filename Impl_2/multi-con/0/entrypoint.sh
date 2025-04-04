#!/bin/bash

PIPE_PATH=$1

# Create the pipe file if it doesn't exist
if [[ ! -p "$PIPE_PATH" ]]; then
    mkfifo "$PIPE_PATH"
fi