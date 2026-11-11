# Figure data

`make_data.py` reads the raw recordings and writes the data files behind the paper's pgfplots figures into
`data/`. The files in `data/` are the ones used in the paper.

| File in `data/` | Figure | Built from |
|---|---|---|
| `server_ack.csv`, `server_socket.csv`, `client_sendq.csv` | one stalled connection seen at the server NIC, the server socket and the client | 3 Nov `run2`: pcap, `ss.log`, `sendq.log` (client_H_1) |
| `minrtt.csv` | minimum RTT per connection against the physical bound | `ss.log` of every series |
| `completion.csv` | completion rate by message size, E1 vs E2 and plain vs TLS, with Wilson 95 % intervals | the earlier size campaign on E1 and E2 (20 attempts per size; counts written in `fig_completion`), and series B `runs.csv` |
| `deadline.csv` | what the round deadline did in each stalled series B run | series B `runs.csv`, server and client logs |
| `seqack_plain_*.csv`, `seqack_tls_*.csv` | data and ACKs over time for one 1 MB reply, plain vs TLS | series B pcaps |

## Run

```bash
VFL_DATA=/path/to/raw_data python3 make_data.py
```

It needs `tcpdump` on the `PATH` to read the captures. `VFL_DATA` (default `../raw_data`) must have this layout:

```
raw_data/
├── melbourne_incident/evidence_RITM0996804/server_melbourne/
│   └── fldiag_run1/ fldiag_run2/ fldiag_series/ fldiag_mac_noecn/ fldiag_qld/
│       fldiag_tls_smoke/ fldiag_mac_tls/ fldiag_qld_tls/     (each: fl5010.pcap, ss.log, server.log, or runN/ with these)
└── experiments/
    ├── vfl_nov03_plain_vs_tls/run1 run2 run3 tls1/          (client logs, sendq.log, server/)
    └── matrix_series_B/results/main/                        (runs.csv and one folder per run)
```

The raw recordings are not in this repository (they hold packet headers with the hosts' IP addresses).

The physical RTT bound uses straight-line distances to Melbourne of 467 km (Canberra) and 1,375 km (Brisbane)
and a signal speed in fibre of 2.04 x 10^8 m/s (`RTT_BOUND_MS`).
