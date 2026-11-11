# Client copies

The NNVertical clients exactly as each series ran them. Each folder has `client_V.py`, `client_H_1.py`,
`client_H_2.py`, a `datasets` link to `../../../flower_apps/NNVertical/datasets`, and an empty
`results/banknote/` for `client_V`'s outputs. Run the clients from inside the folder.

| Folder | Ran on | Differs from `plain/` | Series |
|---|---|---|---|
| `plain/` | Mac | — (the NNVertical clients, plain gRPC to `115.146.84.72:5010`) | `fldiag_run1`, `_run2`, `_series`, `_mac_noecn` |
| `qld/` | QLD VMs | `client_V.py` makes matplotlib optional (not installed on the VMs) | `fldiag_qld` |
| `tls_mac/` | Mac | connect to `flserver.australian-cancer-data.network:5010` over TLS, trusting the public CAs (`certifi`) | `fldiag_tls_smoke`, `fldiag_mac_tls` |
| `tls_qld/` | QLD VMs | `qld/` with the same TLS change | `fldiag_qld_tls` |

`plain/` differs from `../../flower_apps/NNVertical/` only by the commented-out `root_certificates=` line.

To use the QLD copies on other machines, copy the folder (with `datasets/banknote/` as a real folder, not a
link) to `~/fldiag_clients/` on each client VM.
