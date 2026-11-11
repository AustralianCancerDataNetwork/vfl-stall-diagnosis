# MatricesAveraging_chunks

The chunking mitigation. Each client splits its 5 x N `float16` matrix column-wise into `NUM_CHUNKS` pieces and
sends one piece per Flower round. After `NUM_CHUNKS` rounds the server has every piece from every client,
reassembles the matrices and averages them. One full transfer is a *cycle*; the server runs `NUM_CYCLES` cycles,
so `NUM_ROUNDS = NUM_CHUNKS * NUM_CYCLES`. Small chunks keep each gRPC message below the size at which stalls
became likely.

| File | Role |
|---|---|
| `server.py` | binds `115.146.84.72:5010` (E1); `NUM_CHUNKS = 5`, `NUM_CYCLES = 10`, `round_timeout=120`; sets gRPC keepalive (ping every 60 s) |
| `client_1.py`, `client_2.py`, `client_3.py` | `MATRIX_SHAPE = (5, 10000)`, `NUM_CHUNKS = 200` (chunks of 5 x 50); connect to `115.146.84.72:5010` |

**Before running, set `NUM_CHUNKS` to the same value in `server.py` and all three clients.** As left in the files
they differ (server 5, clients 200). The server cannot learn the value from the clients, because it must know
the number of rounds when it starts.

```bash
python server.py
python client_1.py   # and client_2.py, client_3.py in two more terminals
```
