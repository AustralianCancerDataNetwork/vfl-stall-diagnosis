# MatricesAveraging

Each client sends a random 5 x N `float16` matrix in every round, and the server returns the element-wise mean.
It sends a message of a chosen size through the same Flower/gRPC path as the VFL code, so stalls can be tested
by size without the VFL logic. A 5 x N `float16` matrix is about 10N + 128 bytes on the wire.

| File | Role |
|---|---|
| `server.py` | custom strategy; binds `115.146.84.72:5010` (E1); 100 rounds, `round_timeout=120` |
| `client_1.py`, `client_2.py`, `client_3.py` | identical clients apart from their ID; `MATRIX_SHAPE = (5, 100000)`; connect to `149.118.67.128:8080` (E2) |

Set `SERVER` in the clients to the server's address, and `MATRIX_SHAPE` to the size you want to test. Then:

```bash
python server.py
python client_1.py   # and client_2.py, client_3.py in two more terminals
```

The paper's controlled size comparison uses an instrumented copy of this app with optional TLS and timestamped
rounds: see [`../../series_b/`](../../series_b/).
