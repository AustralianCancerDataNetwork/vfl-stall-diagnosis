# Diagnosis: the October 2026 series on E1

The scripts and code that ran the diagnostic series of 28–29 October 2026 against the NNVertical server on E1
(`115.146.84.72:5010`). Each run starts a fresh Flower server with a packet capture and a socket logger on the
server, starts the three VFL clients, records their send queues, and decides whether the run completed or stalled.

## Layout

| Folder | Runs on | Contents |
|---|---|---|
| [`control/`](control/) | the client-side machine (a Mac) | the two scripts that drive a whole series over SSH |
| [`server/`](server/) | E1 | the Flower server (plain and TLS copies) and the early stand-alone recorder |
| [`clients/`](clients/) | the Mac or the QLD VMs | the exact client copies used in each series |

## Series and results

| Series | Clients | TLS | Stalled | Started with |
|---|---|---|---|---|
| `fldiag_run1`, `fldiag_run2` | Mac | no | 1 of 2 (`run1`) | `server/fldiag_server.sh`, clients from `clients/plain/` by hand |
| `fldiag_series` | Mac | no | 1 of 1 (stops at the first stall) | `control/run_series.sh 20` |
| `fldiag_mac_noecn` | Mac | no (server ECN off) | 8 of 10 | `SERIES=mac_noecn KEEP_GOING=1 control/run_series.sh 10` |
| `fldiag_qld` | QLD VMs | no | 14 of 15 | `control/run_series_qld.sh qld 15` |
| `fldiag_tls_smoke` | Mac | yes | 0 of 1 | `SERIES=tls_smoke APP=clients/tls_mac SRVDIR=fldiag_tls control/run_series.sh 1` |
| `fldiag_mac_tls` | Mac | yes | 0 of 10 | `SERIES=mac_tls KEEP_GOING=1 APP=clients/tls_mac SRVDIR=fldiag_tls control/run_series.sh 10` |
| `fldiag_qld_tls` | QLD VMs | yes | 0 of 15 | `SRVDIR=fldiag_tls control/run_series_qld.sh qld_tls 15` |

Plain gRPC stalled in 24 of 28 runs, TLS in 0 of 26. For `mac_noecn` ECN was switched off on the server first
(`sudo sysctl -w net.ipv4.tcp_ecn=0`). For the TLS series the server folder `~/fldiag_tls/` held
`server/server_tls.py` saved as `server.py`.

## What each run records

On the server, in `/tmp/fldiag_<series>/runN/`:

- `fl5010.pcap`: `tcpdump -i eth0 -s 96 'tcp port 5010'` (headers only, no payload);
- `ss.log`: `ss -tinmo 'sport = :5010'` every 0.5 s (bytes acked and received, retransmissions, queues, RTT);
- `server.log`: the Flower server output.

On the Mac, in `runs/<series>/runN/` (`OUT`): the three client logs and `sendq.log`, the `netstat -an` socket
queues every 0.2 s. For the QLD series each VM keeps its client log and an `ss` log in
`~/fldiag_clients/<series>/runN/`, and the Mac keeps one result line per client.

The control scripts do not copy the server files back; fetch `/tmp/fldiag_<series>/` with `scp` after a series.

## Where this code came from

The originals sat in temporary folders that were later cleared. On 31 Oct 2026 they were rebuilt from the
session record by replaying every change made during the tests, and checked against it:
`clients/plain/client_V.py` matches the printed file byte for byte; the H clients match the recorded sizes
(4,848 bytes); `server/server.py` is the server's own copy as printed; `server/server_tls.py` reproduces the
recorded `diff`. Apart from the path changes listed in the top-level README, nothing has been edited since.
