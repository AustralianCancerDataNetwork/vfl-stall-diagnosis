#!/bin/bash
# Runs the NNVertical Flower server with header-only capture and TCP state logging on port 5010.
D=/tmp/fldiag
rm -rf "$D"; mkdir -p "$D"
LIMIT=2400
sudo -n timeout $LIMIT tcpdump -i eth0 -s 96 -U -w "$D/fl5010.pcap" 'tcp port 5010' >"$D/tcpdump.err" 2>&1 &
(
  end=$((SECONDS+LIMIT))
  while [ $SECONDS -lt $end ]; do
    echo "### $(date +%T.%N)"
    ss -tinmo 'sport = :5010'
    sleep 2
  done
) >"$D/ss.log" 2>&1 &
cd ~/FL_Nectar_Comm/NNVertical
PYTHONUNBUFFERED=1 timeout $LIMIT ~/FL_Nectar_Comm/flwr_env_1_31_0/bin/python server.py >"$D/server.log" 2>&1 &
echo $! >"$D/server.pid"
