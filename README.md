# Silent message stalls in deployed vertical federated learning: code

Code for the paper *Silent Message Stalls in Deployed Vertical Federated Learning: Diagnosis and Mitigation*
(in preparation).

A vertical federated learning (VFL) system built on Flower 1.31.0 / gRPC stalled without any error when its
server ran on a Nectar Research Cloud VM in Melbourne (E1): clients sent a reply, their TCP stack reported it as
delivered, and the server never received it. This repository holds the Flower code that showed the problem, the
scripts that recorded each run on both ends (packet captures, socket state, client queues), the controlled
plain-vs-TLS experiment, and the scripts that turn the recordings into the paper's tables and figures.

## Layout

| Folder | What it is | Paper |
|---|---|---|
| [`flower_apps/`](flower_apps/) | the Flower applications: two simple exchanges, a chunked exchange, and the VFL neural network (`NNVertical`) | the deployed workload; the chunking mitigation |
| [`diagnosis/`](diagnosis/) | the October 2026 diagnostic series on E1: control scripts, the server and client copies that ran, the server-side recorder | stall rates, client location, ECN, plain vs TLS |
| [`series_b/`](series_b/) | the controlled series B: 80 plain/TLS runs of 5 x N matrices in random order, and its analysis | completion by message size, deadline behaviour, minimum RTT |
| [`paper_figures/`](paper_figures/) | builds the pgfplots data behind the figures from the raw recordings | all data-driven figures |

Each folder has its own README.

## Setup

Python 3.11 and the packages in `requirements.txt` (Flower 1.31.0):

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

The recording scripts also need, on the server, `tcpdump`, `ss` (iproute2) and passwordless `sudo` for
`tcpdump`; on the client machine, `ssh`, `scp` and `netstat`. `paper_figures/make_data.py` needs `tcpdump` to read
the captures.

## Environments

| Name | Where | Role |
|---|---|---|
| E1 | Nectar Research Cloud, Melbourne, `115.146.84.72`, TCP 5010 | the server where plain gRPC stalls and TLS does not |
| E2 | Oracle Cloud, Sydney, `149.118.67.128:8080` | a second server with no stalls (VM no longer running) |
| home | a Mac on a home network in Canberra | clients for most runs |
| QLD VMs | three Nectar VMs in Brisbane (`203.101.224.177`, `.165`, `203.101.231.85`) | clients for the `qld` series |

Addresses are hard-coded in the scripts as they were when the runs were made. To run against your own server,
change the `server_address` / `SERVER` lines and `SRV=` in the shell scripts.

## What differs from the code as run

The files are the ones that produced the paper's data. The only edits are:

- absolute paths on the authors' machine were replaced by relative paths or environment variables
  (`SSH_KEY`, `KEY_DIR`, `PY`, `OUT`, `APP`, `VFL_DATA`); each README lists them;
- `series_b/client_exp.py` and `paper_figures/make_data.py` point to this repository's folder layout.

## Not included

- **Private keys.** `flower_apps/NNVertical/certificates/` holds only the public CA and server certificates. Make
  your own CA and server key to run with TLS (see that folder's section in the `NNVertical` README).
- **Raw recordings** (packet captures, `ss` and `netstat` logs, client and server logs). The summary tables
  (`series_b/results/*/runs.csv`, `cells.csv`) and the figure data (`paper_figures/data/`) are included.
- **Datasets** other than `banknote` (the only one used in the paper).

## Citation

To be added when the paper is published.
