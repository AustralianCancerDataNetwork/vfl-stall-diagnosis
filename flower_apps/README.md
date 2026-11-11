# Flower applications

Flower 1.31.0 implementations, from a minimal exchange up to vertical FL. Each folder has one `server.py` and
three clients. Run the server, then each client in its own terminal, from inside the folder:

```bash
python server.py        # on the server
python client_1.py      # one terminal per client (client_V.py, client_H_1.py, client_H_2.py for NNVertical)
```

| Folder | What it exchanges | Role in the paper |
|---|---|---|
| [`NumbersAveraging/`](NumbersAveraging/) | each client sends one number; the server returns the average | sanity check of the Flower setup |
| [`MatricesAveraging/`](MatricesAveraging/) | each client sends a random 5 x N float16 matrix; the server returns the element-wise mean | transmission by message size; `../series_b/` is a copy of it with TLS and logging |
| [`MatricesAveraging_chunks/`](MatricesAveraging_chunks/) | the same matrix split column-wise into chunks, one chunk per Flower round, reassembled at the server | the chunking mitigation |
| [`NNVertical/`](NNVertical/) | the VFL neural network: passive clients upload Z1, the active client uploads Z1 and dZ1, the server sums and relays | the deployed VFL workload |

[`FLOWER_CALL_FLOW.md`](FLOWER_CALL_FLOW.md) is a reference for the order in which Flower calls the strategy and
client methods, shared by the three averaging apps.

## Addresses as left in the files

Check the addresses before running: they differ between files.

| Folder | Server binds | Clients connect to | Other |
|---|---|---|---|
| `NumbersAveraging` | `0.0.0.0:5010` | `127.0.0.1:5010` (local) | 100 rounds |
| `MatricesAveraging` | `115.146.84.72:5010` (E1) | `149.118.67.128:8080` (E2) | 100 rounds, `round_timeout=120`; clients 5 x 100,000 |
| `MatricesAveraging_chunks` | `115.146.84.72:5010` (E1) | `115.146.84.72:5010` (E1) | see its README: client and server `NUM_CHUNKS` must match |
| `NNVertical` | `149.118.67.128:8080` (E2) | `115.146.84.72:5010` (E1), plain gRPC | 100 rounds = 50 training iterations |

For a first local test, set the server to `0.0.0.0:5010` and the clients to `127.0.0.1:5010`.
