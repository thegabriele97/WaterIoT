#!/bin/sh

node-red -u .&
PID=$!

sleep 5
ipaddress= $(ifconfig eth0 | grep 'inet ' | cut -d" " -f10)
curl -X POST $ipaddress:1880/flows -H "Content-Type: application/json" --data "@flows.json"

# reattach to background process's stdout
cd /proc/$PID/fd
tail -f 0 2

# if tail is killed
kill $PID
