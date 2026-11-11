#!/bin/bash
# Repeats the NNVertical run against Melbourne with the three clients on the QLD VMs.
# Usage: run_series_qld.sh <label> <runs>
# Server side: tcpdump + ss + server log per run in /tmp/fldiag_<label>/runN.
# Client side: client log + ss snapshots per run in ~/fldiag_clients/<label>/runN.
HERE="$(cd "$(dirname "$0")" && pwd)"
KD=${KEY_DIR:-$HOME/.ssh}   # holds ids_rsa_server, ids_rsa_client_1..3
SRV=ubuntu@115.146.84.72
LABEL=${1:-qld}
N=${2:-15}
SRVDIR=${SRVDIR:-FL_Nectar_Comm/NNVertical}   # relative to the server home directory
OUT=${OUT:-"$HERE/../runs/$LABEL"}
mkdir -p "$OUT"
rssh() { ssh -i "$KD/ids_rsa_server" -o BatchMode=yes -o ConnectTimeout=15 $SRV "$@" </dev/null; }
cssh() { local n=$1; shift; ssh -i "$KD/ids_rsa_$n" -o BatchMode=yes -o ConnectTimeout=15 "$@" </dev/null; }
declare -a HOSTS=("client_1 203.101.224.177 client_V" "client_2 203.101.224.165 client_H_1" "client_3 203.101.231.85 client_H_2")
stalls=0

for i in $(seq 1 $N); do
  rssh "D=/tmp/fldiag_$LABEL/run$i; mkdir -p \$D
    sudo -n setsid timeout 300 tcpdump -i eth0 -s 96 -U -w \$D/fl5010.pcap 'tcp port 5010' >\$D/tcpdump.err 2>&1 </dev/null &
    setsid bash -c 'end=\$((SECONDS+300)); while [ \$SECONDS -lt \$end ]; do echo \"### \$(date +%T.%N)\"; ss -tinmo \"sport = :5010\"; sleep 0.5; done' >\$D/ss.log 2>&1 </dev/null &
    cd ~/$SRVDIR
    PYTHONUNBUFFERED=1 setsid timeout 300 ~/FL_Nectar_Comm/flwr_env_1_31_0/bin/python server.py >\$D/server.log 2>&1 </dev/null &
    sleep 4" >/dev/null 2>&1

  pids=()
  for h in "${HOSTS[@]}"; do
    set -- $h; n=$1; ip=$2; c=$3
    cssh $n ubuntu@$ip "D=~/fldiag_clients/$LABEL/run$i; mkdir -p \$D; cd ~/fldiag_clients
      (end=\$((SECONDS+130)); while [ \$SECONDS -lt \$end ]; do echo \"### \$(date +%T.%N)\"; ss -tinmo 'dport = :5010'; sleep 0.2; done) >\$D/ss.log 2>&1 &
      MON=\$!
      PYTHONUNBUFFERED=1 timeout 120 ~/FL_Nectar_Comm/flwr_env_1_31_0/bin/python $c.py >\$D/$c.log 2>&1; rc=\$?
      kill \$MON; echo $c rc=\$rc replies=\$(grep -c 'Sent reply' \$D/$c.log) unavailable=\$(grep -c UNAVAILABLE \$D/$c.log)" >"$OUT/run$i.$c.txt" 2>&1 &
    pids+=($!)
    sleep 1
  done
  wait "${pids[@]}"

  status=completed
  grep -qE "rc=[1-9]|unavailable=[1-9]" "$OUT"/run$i.*.txt && status=STALLED
  [ $status = STALLED ] && stalls=$((stalls+1))
  rssh "pkill -f 'flwr_env_1_31_0/bin/python [s]erver.py'; sudo -n pkill -f '[t]cpdump -i eth0 -s 96'; pkill -f '[s]s -tinmo'" >/dev/null 2>&1
  echo "run $i: $status  $(cat "$OUT"/run$i.*.txt | tr '\n' ' ')"
  sleep 3
done
echo "TOTAL: $stalls stalled out of $N"
