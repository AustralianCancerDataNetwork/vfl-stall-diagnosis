#!/bin/bash
# Runs the journal experiments against the Melbourne server (E1), one fresh server + 3 Mac clients per run.
# Usage: run_exp.sh <series> <plan file>; each plan line: <label> <cols> <tls 0|1>
# Server side, per run (~/fl_journal_runs/out/<series>/<label>/): tcpdump (snaplen 96), ss -tinmo every 0.5 s,
#   server log. Only processes started here are stopped (by PID file).
# Mac side, per run (results/<series>/<label>/): client logs, netstat queues every 0.2 s, and the server files.
# A run is STALLED when no client log grows for 120 s, or after 600 s in total.
set -u
SERIES=$1; PLAN=$2
HERE="$(cd "$(dirname "$0")" && pwd)"
K=${SSH_KEY:-$HOME/.ssh/ids_rsa_server}   # SSH key for the server
SRV=ubuntu@115.146.84.72
PY=${PY:-python3}   # Python with flwr 1.31.0 on this machine
SPY='~/FL_Nectar_Comm/flwr_env_1_31_0/bin/python'
OUT="$HERE/results/$SERIES"
rssh() { ssh -i "$K" -o BatchMode=yes -o ConnectTimeout=15 $SRV "$@" </dev/null; }

mkdir -p "$OUT"
rssh "mkdir -p ~/fl_journal_runs" && scp -q -i "$K" "$HERE/server_exp.py" $SRV:fl_journal_runs/

while read -r L COLS TLS; do
  [ -z "$L" ] && continue
  R="$OUT/$L"; mkdir -p "$R"
  D="fl_journal_runs/out/$SERIES/$L"
  rssh "mkdir -p ~/$D && cd ~/$D
    sudo -n setsid timeout 900 tcpdump -i eth0 -s 96 -U -w fl5010.pcap 'tcp port 5010' >tcpdump.err 2>&1 </dev/null & echo \$! >tcpdump.pid
    setsid timeout 900 bash -c 'while true; do echo \"### \$(date -u +%T.%N)\"; ss -tinmo \"sport = :5010\"; sleep 0.5; done' >ss.log 2>&1 </dev/null & echo \$! >ss.pid
    cd ~/fl_journal_runs
    TLS=$TLS ROUNDS=5 ROUND_TIMEOUT=60 PYTHONUNBUFFERED=1 setsid timeout 900 $SPY server_exp.py >~/$D/server.log 2>&1 </dev/null & echo \$! >~/$D/server.pid
    sleep 4"

  ( while true; do echo "### $(date -u +%T.%N)"; netstat -an -p tcp | grep "115.146.84.72.5010"; sleep 0.2; done ) >"$R/sendq.log" 2>&1 </dev/null &
  MON=$!
  PIDS=()
  T0=$(date +%s)
  for c in client_1 client_2 client_3; do
    COLS=$COLS TLS=$TLS PYTHONUNBUFFERED=1 "$PY" "$HERE/client_exp.py" $c >"$R/$c.log" 2>&1 </dev/null &
    PIDS+=($!)
    sleep 1
  done

  status=completed; last=$(date +%s); prev=""
  while true; do
    sleep 2
    alive=0; for p in "${PIDS[@]}"; do kill -0 $p 2>/dev/null && alive=$((alive+1)); done
    [ $alive = 0 ] && break
    size=$(cat "$R"/client_*.log | wc -c)
    [ "$size" != "$prev" ] && { prev=$size; last=$(date +%s); }
    now=$(date +%s)
    if [ $((now-last)) -ge 120 ] || [ $((now-T0)) -ge 600 ]; then status=STALLED; break; fi
  done
  grep -q "UNAVAILABLE" "$R"/client_*.log && status=STALLED
  [ $status = STALLED ] && sleep 20   # keep recording the stalled state
  DUR=$(( $(date +%s) - T0 ))

  kill "${PIDS[@]}" 2>/dev/null; kill $MON 2>/dev/null; wait $MON 2>/dev/null
  rssh "cd ~/$D; kill \$(cat server.pid) \$(cat ss.pid) 2>/dev/null; sudo -n kill \$(cat tcpdump.pid) 2>/dev/null; sleep 1"
  scp -q -i "$K" "$SRV:$D/server.log" "$SRV:$D/ss.log" "$SRV:$D/fl5010.pcap" "$SRV:$D/tcpdump.err" "$R/"
  echo "$(date -u +%FT%TZ) $L cols=$COLS tls=$TLS $status ${DUR}s" | tee -a "$OUT/results.txt"
  sleep 3
done < "$PLAN"
