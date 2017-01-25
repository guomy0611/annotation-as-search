#!/usr/bin/env bash

# Takes the port as its only argument. Default is 8080.

HOST='127.0.0.1'
PORT=${1:-8080}

PYTHON=python3

SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")
SERVER_DIR="$SCRIPT_DIR/../annotation-helper/"
CLIENT_DIR="$SCRIPT_DIR"

SERVER_LOG='/tmp/annotation.log'

start_server() {
    local host="$1"
    local port="$2"

    "$PYTHON" "$SERVER_DIR/server.py"\
        -H "$host"\
        -p "$port"\
        --loglevel DEBUG\
        --logfile "$SERVER_LOG"\
        </dev/null 1>/dev/null 2>/dev/null
}

start_client() {
    local host="$1"
    local port="$2"
    "$PYTHON" "$CLIENT_DIR/cli-client.py"\
        -H "$host"\
        -p "$port"\
        -f "$CLIENT_DIR/../test/badender_lurch.conll09"
}

start_server "$HOST" "$PORT" &

# Wait for server to start.
sleep 3
start_client "$HOST" "$PORT"
