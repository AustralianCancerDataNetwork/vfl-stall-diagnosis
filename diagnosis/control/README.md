# Control scripts

Run on the client-side machine (a Mac). Each script drives a whole series over SSH: per run it starts the
recorders and a fresh Flower server on E1, starts the clients, waits, labels the run, and stops everything.

| Script | Clients | Labels a run STALLED when |
|---|---|---|
| `run_series.sh [N]` | all three on this machine, from `APP` | the clients have not finished after 120 s, or a client logged `UNAVAILABLE` |
| `run_series_qld.sh <label> [N]` | one on each QLD VM, from `~/fldiag_clients/` there, each under `timeout 120` | a client exited non-zero or logged `UNAVAILABLE` |

`run_series.sh` stops at the first stall unless `KEEP_GOING=1`, and keeps recording for 40 s after a stall.
`run_series_qld.sh` always runs all N.

## Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `SSH_KEY` | `~/.ssh/ids_rsa_server` | key for `ubuntu@115.146.84.72` (`run_series.sh`) |
| `KEY_DIR` | `~/.ssh` | folder with `ids_rsa_server` and `ids_rsa_client_1`..`_3` for the VMs (`run_series_qld.sh`) |
| `SERIES` | `series` | series name (`run_series.sh`; `run_series_qld.sh` takes it as the first argument) |
| `OUT` | `../runs/<series>` | where this machine's logs go |
| `APP` | `../clients/plain` | folder of client copies to run (`run_series.sh`) |
| `SRVDIR` | `FL_Nectar_Comm/NNVertical` | server folder, relative to the server's home, holding `server.py` |
| `PY` | `python3` | Python with Flower 1.31.0 on this machine (`run_series.sh`) |
| `KEEP_GOING` | unset | `1`: do not stop at the first stall (`run_series.sh`) |

The server side expects Flower in `~/FL_Nectar_Comm/flwr_env_1_31_0/` and passwordless `sudo` for `tcpdump`
and `pkill`. The QLD VMs expect the client files and `datasets/banknote/` in `~/fldiag_clients/`.

The commands typed on the server (start `tcpdump`, the `ss` loop and the server; stop them) are inside the
`rssh "..."` blocks.
