# NumbersAveraging

The smallest Flower exchange: in each round every client sends one number and the server returns the average.
Used to check that the Flower setup and the network path work at all, before sending anything large.

| File | Role |
|---|---|
| `server.py` | custom strategy; binds `0.0.0.0:5010`; 100 rounds |
| `client_1.py`, `client_2.py`, `client_3.py` | identical clients apart from their ID; connect to `127.0.0.1:5010` |

```bash
python server.py
python client_1.py   # and client_2.py, client_3.py in two more terminals
```

The server waits for all three clients before the first round. The order in which Flower calls the strategy
and client methods is described in [`../FLOWER_CALL_FLOW.md`](../FLOWER_CALL_FLOW.md).
