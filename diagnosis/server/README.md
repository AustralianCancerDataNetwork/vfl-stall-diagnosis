# Server files (E1)

| File | What it is | Used for |
|---|---|---|
| `server.py` | `~/FL_Nectar_Comm/NNVertical/server.py` as it was during the tests: the NNVertical server on `115.146.84.72:5010`, plain gRPC, `round_timeout=300` | all plain series |
| `server_tls.py` | the TLS copy (was `~/fldiag_tls/server.py`). It differs from `server.py` only by `certificates=` in `start_server`, loading a Let's Encrypt certificate from `~/flwr_certs/` | all TLS series |
| `fldiag_server.sh` | the early stand-alone recorder: `tcpdump` (headers only), `ss` every 2 s and the Flower server, into `/tmp/fldiag/`, for up to 40 min | `fldiag_run1`, `fldiag_run2` |

`server.py` differs from `../../flower_apps/NNVertical/server.py` in its bind address, `round_timeout=300`,
`fraction_evaluate=0.0`, 5 x 5 placeholder matrices, a 30 s `get_properties` timeout, asking each client for its
name only once, and one extra log line in `aggregate_fit`.

Run `fldiag_server.sh` on the server, then start the clients by hand:

```bash
bash fldiag_server.sh          # writes /tmp/fldiag/{fl5010.pcap, ss.log, server.log, server.pid}
```

For the TLS copy, replace the paths in `server_tls.py` with your own certificate, key and chain.
