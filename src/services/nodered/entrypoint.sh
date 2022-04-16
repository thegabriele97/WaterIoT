#!/bin/sh

node-red -u .&
PID=$!

sleep 5
curl -X POST http://localhost:1880/flows -H "Content-Type: application/json" --data "@flows.json"

# reattach to background process's stdout
cd /proc/$PID/fd
tail -f 0 2

# if tail is killed
kill $PID
