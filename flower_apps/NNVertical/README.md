# NNVertical: vertical federated learning with a neural network

A neural network (features → 5 → 5 → 1, sigmoid activations) trained across three clients that hold different
features of the same samples. The first layer is split across the clients; the active client holds the upper
layers and the label. Clients talk only to the server; anything one client sends to another goes through it.

| Client | Holds | Sends |
|---|---|---|
| `client_H_1` (passive) | some input features, its part of W1 | Z1 = W1 X (its share of the first layer) |
| `client_H_2` (passive) | other input features, its part of W1 | Z1 |
| `client_V` (active) | the remaining features, its part of W1, the upper layers W2, W3, and the label | Z1, and dZ1 (the gradient for the first layer) |

The server sums the three Z1 shares, applies the sigmoid to get A1, sends A1 to `client_V`, and relays `client_V`'s
dZ1 to the passive clients. One training iteration takes two Flower rounds, so 100 rounds = 50 iterations.

## Files

| Path | Contents |
|---|---|
| `server.py` | custom `FedAvg` strategy that sums, activates and relays; binds `149.118.67.128:8080` (E2). The E1 copy that ran in the diagnosis is `../../diagnosis/server/server.py` |
| `client_V.py`, `client_H_1.py`, `client_H_2.py` | the clients; connect to `115.146.84.72:5010` (E1) over plain gRPC |
| `datasets/banknote/` | the UCI banknote authentication data, split by column into `data_H_1.csv`, `data_H_2.csv`, `data_V.csv` (rows aligned; `data_V` holds the label) |
| `results/banknote/` | `client_V` writes `training_metrics.csv` and the loss and accuracy plots here |
| `certificates/` | the public CA certificate (`ca.crt`), the server certificate (`server.pem`) and its OpenSSL config (`server.cnf`) |

The dataset is chosen by `folder = "banknote"` at the top of each client. Another dataset needs the same
three-file split with aligned rows.

## Running

Set `server_address` in `server.py` and in each client, then, from this folder:

```bash
python server.py
python client_V.py      # and client_H_1.py, client_H_2.py in two more terminals
```

## TLS

The private keys are not in the repository. Make your own CA and server certificate (edit `server.cnf` to your
server's name and IP first):

```bash
cd certificates
openssl req -x509 -newkey rsa:4096 -nodes -keyout ca.key -out ca.crt -days 365 -subj "/CN=FL test CA"
openssl req -newkey rsa:4096 -nodes -keyout server.key -out server.csr -config server.cnf
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.pem -days 365 \
  -extensions v3_req -extfile server.cnf
```

Then pass `certificates=(ca.crt, server.pem, server.key)` (as bytes) to `start_server`, as
`../../series_b/server_exp.py` does, and uncomment the `root_certificates=` line in each client.

## Message flow, first four rounds

**Round 1.** The server sends dZ1 (zeros) to the passive clients and nothing to `client_V`. All three clients
send Z1. The server sums the Z1 shares and computes A1 = sigmoid(sum).

**Round 2.** The server sends A1 to `client_V`, which runs the upper layers, computes the loss and gradients,
updates W2 and W3, and sends dZ1 to the server.

**Round 3.** The server relays dZ1 to the passive clients, which update their W1. All three clients send a new
Z1; the server sums them and computes A1.

**Round 4.** As round 2.

The order in which Flower calls the strategy and client methods is described in
[`../FLOWER_CALL_FLOW.md`](../FLOWER_CALL_FLOW.md).
