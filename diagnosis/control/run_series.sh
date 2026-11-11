#!/bin/bash
# Repeats the NNVertical run against Melbourne until one stalls (or N runs pass).
# Server side: fresh tcpdump + ss log + server log per run in /tmp/fldiag_${SERIES:-series}/runN.
# Mac side: netstat send/recv queue snapshots every 0.2s + client logs per run.
HERE="$(cd "$(dirname "$0")" && pwd)"
K=${SSH_KEY:-$HOME/.ssh/ids_rsa_server}
SRV=ubuntu@115.146.84.72
OUT=${OUT:-"$HERE/../runs/${SERIES:-series}"}
APP=${APP:-"$HERE/../clients/plain"}
SRVDIR=${SRVDIR:-FL_Nectar_Comm/NNVertical}   # relative to the server's home directory
PY=${PY:-python3}   # Python with flwr 1.31.0 on this machine
N=${1:-20}
mkdir -p "$OUT"
rssh() { ssh -i "$K" -o BatchMode=yes -o ConnectTimeout=15 $SRV "$@" </dev/null; }

for i in $(seq 1 $N); do
  R=$OUT/run$i; mkdir -p "$R"
  rssh "D=/tmp/fldiag_${SERIES:-series}/run$i; mkdir -p \$D
    sudo -n setsid timeout 600 tcpdump -i eth0 -s 96 -U -w \$D/fl5010.pcap 'tcp port 5010' >\$D/tcpdump.err 2>&1 </dev/null &
    setsid bash -c 'end=\$((SECONDS+600)); while [ \$SECONDS -lt \$end ]; do echo \"### \$(date +%T.%N)\"; ss -tinmo \"sport = :5010\"; sleep 0.5; done' >\$D/ss.log 2>&1 </dev/null &
    cd ~/$SRVDIR
    PYTHONUNBUFFERED=1 setsid timeout 600 ~/FL_Nectar_Comm/flwr_env_1_31_0/bin/python server.py >\$D/server.log 2>&1 </dev/null &
    sleep 4" >/dev/null 2>&1

  ( while true; do echo "### $(date +%T.%N)"; netstat -an -p tcp | grep "115.146.84.72.5010"; sleep 0.2; done ) >"$R/sendq.log" 2>&1 &
  MON=$!
  cd "$APP"
  for c in client_V client_H_1 client_H_2; do
    PYTHONUNBUFFERED=1 "$PY" $c.py >"$R/$c.log" 2>&1 &
    sleep 1
  done

  status=completed
  for t in $(seq 1 60); do
    sleep 2
    [ "$(pgrep -f 'client_(V|H_1|H_2).py' | wc -l | tr -d ' ')" = 0 ] && break
    if [ $t -eq 60 ]; then status=STALLED; fi
  done
  grep -q "UNAVAILABLE" "$R"/client_*.log && status=STALLED
  if [ $status = STALLED ]; then sleep 40; fi   # keep observing the stalled state

  kill $MON 2>/dev/null
  pkill -f 'client_(V|H_1|H_2).py' 2>/dev/null
  rssh "pkill -f 'flwr_env_1_31_0/bin/python [s]erver.py'; sudo -n pkill -f '[t]cpdump -i eth0 -s 96'; pkill -f '[s]s -tinmo'" >/dev/null 2>&1
  echo "run $i: $status"
  [ $status = STALLED ] && stalls=$((stalls+1))
  [ $status = STALLED ] && [ -z "$KEEP_GOING" ] && break
  sleep 3
done
echo "TOTAL: ${stalls:-0} stalled out of $i"
