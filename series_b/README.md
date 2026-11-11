# Series B: plain vs TLS by message size, 7 Nov 2026

The controlled comparison. Each run starts a fresh server on E1 and three clients on the Mac; each client uploads
a random 5 x N `float16` matrix for 5 rounds and the server returns the mean (the `MatricesAveraging` exchange).
Plain and TLS runs of four sizes (N = 50, 1,000, 10,000, 100,000, i.e. about 0.6 kB to 1 MB per message) are
run in random order within one session, so that time-varying network conditions affect both transports alike.

## Files

| File | Purpose |
|---|---|
| `server_exp.py` | experiment server, copied to `~/fl_journal_runs/` on E1; logs `ROUND_START`/`ROUND_END` with timestamps. Environment: `TLS` (0/1), `ROUNDS` (5), `ROUND_TIMEOUT` (60 s) |
| `client_exp.py` | experiment client, `python client_exp.py <id>`; environment `COLS` (N) and `TLS`; trusts `../flower_apps/NNVertical/certificates/ca.crt` |
| `make_plan.py` | writes the run order: `reps` blocks, each holding the 8 (size, transport) cells once, shuffled with a fixed seed |
| `plan_main.txt`, `plan_test.txt` | the 80-run plan (10 blocks, seed 2026) and the 2 test runs |
| `run_exp.sh` | runs a plan: per run, `tcpdump` (headers only), `ss` every 0.5 s and the server on E1; the clients and `netstat` every 0.2 s on the Mac; then fetches the server files |
| `analyse_exp.py` | labels each run from its server log and writes `runs.csv` and `cells.csv` (completion rate with a Wilson 95 % interval, median round time, minimum RTT) |
| `results/<series>/` | `results.txt` (one line per run, written by `run_exp.sh`), `runs.csv`, `cells.csv`. The per-run folders with the raw recordings are not in the repository |

`run_exp.sh` labels a run STALLED when no client log has grown for 120 s, after 600 s in total, or when a client
logged `UNAVAILABLE`. `analyse_exp.py` then labels each run, from the server log:

| Label | Meaning |
|---|---|
| `completed` | all 5 rounds ended with 3 results and no failures |
| `deadline` | the server finished, but the round deadline ended at least one round with failures |
| `stalled` | the server never finished (it was stopped by `run_exp.sh`) |
| `invalid` | no server log: the SSH session that starts the server failed, so the run did not happen |

## Reproduce

```bash
python3 make_plan.py plan_main.txt 10 2026
SSH_KEY=~/.ssh/ids_rsa_server PY=python3 caffeinate -i ./run_exp.sh main plan_main.txt   # about 2 h
python3 analyse_exp.py main
```

`SSH_KEY` is the key for `ubuntu@115.146.84.72`; `PY` is a Python with Flower 1.31.0 on the Mac. On the server,
Flower is expected in `~/FL_Nectar_Comm/flwr_env_1_31_0/` and the certificates for `TLS=1` in
`~/FL_Nectar_Comm/NNVertical/certificates/`. `caffeinate` keeps a Mac awake; leave it out elsewhere.
`analyse_exp.py` needs the per-run folders, so it can only be rerun where the raw recordings are.

## Outcome (main series)

80 runs. 13 are `invalid` and excluded. `results.txt` labels some of them "completed"; use `runs.csv`, which
labels runs from the server log. Of the valid runs, plain gRPC completed 12 of 34 and TLS 33 of 33.
