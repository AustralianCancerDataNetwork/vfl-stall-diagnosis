# Flower FL — Communication Flow Reference

A complete reference for the method call sequence between the **Server Strategy** and **Client** in the Flower (flwr) federated learning framework.

---

## Overview

There are two sides:

- **Server Strategy** — your custom class inheriting `fl.server.strategy.Strategy`. Controls the round logic entirely. Never touches data directly.
- **Client** — your custom class inheriting `fl.client.Client` (or `NumPyClient`). Holds local data and model. Responds to server instructions.

All communication between them is over **gRPC**. The server calls strategy methods locally; strategy methods trigger gRPC messages to clients.

---

## Phase 1 — INIT (runs once, before any round)

### 1. `initialize_parameters(client_manager)` — Server Strategy

**Called by:** Flower server, immediately on startup.  
**Purpose:** Provide the initial global model parameters.  
**Returns:** `Parameters` object, or `None`.

```python
def initialize_parameters(self, client_manager):
    # Option A — supply your own starting parameters (recommended for VFL)
    return ndarrays_to_parameters([np.zeros((10,))])

    # Option B — return None, triggering get_parameters() on a client
    return None
```

> **VFL note:** Always return explicit parameters here. If you return `None`, Flower picks whichever client registered first and calls `get_parameters()` on it — non-deterministic on distributed infra like Nectar.

---

### 2. `get_parameters(ins)` — Client *(only if step 1 returns None)*

**Called by:** Server, on the first client that connected.  
**Purpose:** Seed global parameters from a client's local model.  
**Returns:** `GetParametersRes` containing the client's parameters.

```python
def get_parameters(self, ins):
    # Return local model weights as the global starting point
    return GetParametersRes(
        status=Status(code=Code.OK, message="OK"),
        parameters=ndarrays_to_parameters(self.model.get_weights()),
    )
```

> **When skipped:** If `initialize_parameters()` returned something, this method is never called at all.

---

### 3. `evaluate(server_round, parameters)` — Server Strategy *(initial eval)*

**Called by:** Server, right after parameters are initialised.  
**Purpose:** Optional server-side evaluation of the initial global parameters.  
**Returns:** `(loss, metrics)` tuple, or `None` to skip.

```python
def evaluate(self, server_round, parameters):
    return None  # skip initial evaluation
```

> **No client involvement.** This uses the server's own test set, not clients. Distinct from the client-side `evaluate()` called later in the round.

---

## Phase 2 — Round N (repeats for every round)

### 4. `configure_fit(server_round, parameters, client_manager)` — Server Strategy

**Called by:** Server, at the start of each round.  
**Purpose:** Decide which clients train this round and what to send them.  
**Key internal call:** `client_manager.sample(num_clients=N, min_num_clients=N)` — **this is where hangs occur** if clients haven't registered yet.  
**Returns:** List of `(ClientProxy, FitIns)` tuples — one per selected client.

```python
def configure_fit(self, server_round, parameters, client_manager):
    clients = client_manager.sample(num_clients=3, min_num_clients=3)
    fit_ins = FitIns(parameters=parameters, config={"round": server_round})
    return [(client, fit_ins) for client in clients]
```

> **gRPC trigger:** Returning this list causes Flower to send a `FitIns` message to each selected client over gRPC.

---

### 5. `fit(ins)` — Client

**Called by:** Server (via gRPC), once per selected client.  
**Purpose:** Perform local training / computation. Return updated parameters and metrics.  
**Returns:** `FitRes` containing updated parameters, sample count, and metrics dict.

```python
def fit(self, ins):
    # ins.parameters = global parameters from server
    # ins.config     = config dict (e.g. {"round": 1})

    # Do local work: train model, compute embeddings, etc.
    updated_params = ...

    return FitRes(
        status=Status(code=Code.OK, message="OK"),
        parameters=ndarrays_to_parameters(updated_params),
        num_examples=len(self.local_data),
        metrics={"loss": 0.42},
    )
```

> **gRPC return:** `FitRes` is sent back to the server over gRPC when this returns.

---

### 6. `aggregate_fit(server_round, results, failures)` — Server Strategy

**Called by:** Server, after all `FitRes` results have arrived.  
**Purpose:** Aggregate the parameters returned by all clients.  
**Returns:** `(Parameters, metrics_dict)` — the new global parameters for this round.

```python
def aggregate_fit(self, server_round, results, failures):
    # results = list of (ClientProxy, FitRes)
    # failures = list of clients that failed or timed out

    arrays = [parameters_to_ndarrays(res.parameters) for _, res in results]
    averaged = [np.mean([a[i] for a in arrays], axis=0) for i in range(len(arrays[0]))]

    return ndarrays_to_parameters(averaged), {"round": server_round}
```

> **No client involvement.** Pure server-side aggregation logic.

---

### 7. `configure_evaluate(server_round, parameters, client_manager)` — Server Strategy

**Called by:** Server, after `aggregate_fit` completes.  
**Purpose:** Decide which clients evaluate the new global parameters.  
**Returns:** List of `(ClientProxy, EvaluateIns)` tuples, or `[]` to skip evaluation.

```python
def configure_evaluate(self, server_round, parameters, client_manager):
    # Skip evaluation entirely
    return []

    # Or select clients for evaluation
    clients = client_manager.sample(num_clients=3, min_num_clients=3)
    eval_ins = EvaluateIns(parameters=parameters, config={})
    return [(client, eval_ins) for client in clients]
```

---

### 8. `evaluate(ins)` — Client *(only if step 7 returns non-empty list)*

**Called by:** Server (via gRPC), on each selected client.  
**Purpose:** Evaluate the global model on local test data.  
**Returns:** `EvaluateRes` with loss, sample count, and metrics.

```python
def evaluate(self, ins):
    # ins.parameters = updated global parameters to evaluate

    loss, accuracy = self.model.evaluate(self.test_data)

    return EvaluateRes(
        status=Status(code=Code.OK, message="OK"),
        loss=float(loss),
        num_examples=len(self.test_data),
        metrics={"accuracy": accuracy},
    )
```

> **When skipped:** If `configure_evaluate()` returned `[]`, this method is never called.

---

### 9. `aggregate_evaluate(server_round, results, failures)` — Server Strategy

**Called by:** Server, after all `EvaluateRes` results arrive.  
**Purpose:** Aggregate evaluation metrics across clients.  
**Returns:** `(float loss, metrics_dict)` or `(None, {})` if skipped.

```python
def aggregate_evaluate(self, server_round, results, failures):
    if not results:
        return None, {}
    losses = [res.loss * res.num_examples for _, res in results]
    total = sum(res.num_examples for _, res in results)
    return sum(losses) / total, {}
```

---

### 10. `evaluate(server_round, parameters)` — Server Strategy *(end-of-round)*

**Called by:** Server, at the end of each round with the newly aggregated parameters.  
**Purpose:** Optional server-side evaluation after aggregation (e.g. on a held-out test set on the server).  
**Returns:** `(loss, metrics)` or `None`.

> **Distinct from step 3:** Same method signature, but called with updated parameters after each round rather than just once at init.

---

## Complete Call Order

```
INIT (once):
  1. initialize_parameters()          [server strategy]
        └── if None → get_parameters()  [client — first connected]
  2. evaluate()                       [server strategy — initial params]

ROUND N (repeats):
  3. configure_fit()                  [server strategy]
        └── sample() blocks here until min_num_clients connect
        └── → FitIns sent to each client via gRPC
  4.     fit()                        [each selected client]
        └── → FitRes returned via gRPC
  5. aggregate_fit()                  [server strategy]
  6. configure_evaluate()             [server strategy]
        └── → EvaluateIns sent to each client via gRPC (if non-empty)
  7.     evaluate()                   [each selected client — if called]
        └── → EvaluateRes returned via gRPC
  8. aggregate_evaluate()             [server strategy]
  9. evaluate()                       [server strategy — updated params]
```

---

## What crosses gRPC vs stays local

| Exchange | Transport |
|----------|-----------|
| `FitIns` → client | gRPC |
| `FitRes` ← client | gRPC |
| `EvaluateIns` → client | gRPC |
| `EvaluateRes` ← client | gRPC |
| `GetParametersRes` ← client | gRPC |
| `configure_fit`, `aggregate_fit`, `evaluate` (server) | Local — no network |

---

## Key debugging notes

**`sample()` hangs** — the most common failure point in distributed setups. `sample(num_clients=N, min_num_clients=N)` blocks until N clients have registered. On Nectar, if any client VM is slow to start or has a firewall issue, this blocks indefinitely. Check client logs first — if clients show "Connecting..." but never advance, the gRPC port (default 8080) is likely blocked.

**`get_parameters()` unexpectedly called** — means your `initialize_parameters()` returned `None`. Always return explicit parameters to avoid non-deterministic client selection.

**`fit()` returns but `aggregate_fit()` never fires** — one or more clients failed silently. Check the `failures` list in `aggregate_fit()`. A client timeout with no exception will appear here.

**Client `evaluate()` never called** — expected if `configure_evaluate()` returns `[]`. Intentional in Phase 1 of this debug series.

---

## Phase summary (this debug series)

| Phase | What we test |
|-------|-------------|
| Phase 1 ✅ | Bare connection — floats, custom strategy, 3 clients |
| Phase 2 | NumPy tensor exchange — no model |
| Phase 3 | Split model — bottom/top, embeddings |
| Phase 4 | Full fit + evaluate with instrumentation |
| Phase 5 | Nectar hardening — gRPC keepalive, timeouts |