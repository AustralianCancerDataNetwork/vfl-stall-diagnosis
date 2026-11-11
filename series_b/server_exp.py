"""
Journal experiment server: MatricesAveraging with optional TLS and timestamped rounds.

Same exchange as MatricesAveraging/server.py: each round the 3 clients send a 5 x N float16
matrix and the server returns their element-wise average. Configured by environment:
  TLS=1            serve gRPC over TLS with the NNVertical certificates
  ROUNDS=5         rounds per attempt
  ROUND_TIMEOUT=60 Flower round deadline (s)
"""

import os
import time
from pathlib import Path

import flwr as fl
import numpy as np
from flwr.common import FitIns, ndarrays_to_parameters, parameters_to_ndarrays

TLS = os.environ.get("TLS") == "1"
ROUNDS = int(os.environ.get("ROUNDS", "5"))
ROUND_TIMEOUT = float(os.environ.get("ROUND_TIMEOUT", "60"))
CERTS = Path.home() / "FL_Nectar_Comm/NNVertical/certificates"


def log(msg):
    print(f"{time.time():.3f} {msg}", flush=True)


class MatrixAverageStrategy(fl.server.strategy.Strategy):

    def initialize_parameters(self, client_manager):
        return ndarrays_to_parameters([np.array([0.0])])  # dummy, as in the original

    def configure_fit(self, server_round, parameters, client_manager):
        clients = client_manager.sample(num_clients=3, min_num_clients=3)
        log(f"ROUND_START {server_round}")
        return [(c, FitIns(parameters=parameters, config={"round": server_round})) for c in clients]

    def aggregate_fit(self, server_round, results, failures):
        log(f"ROUND_END {server_round} results={len(results)} failures={len(failures)}")
        if not results:
            return None, {}
        values = [parameters_to_ndarrays(r.parameters)[0] for _, r in results]
        average = np.mean(values, axis=0)
        return ndarrays_to_parameters([np.array([average])]), {}

    def configure_evaluate(self, server_round, parameters, client_manager):
        return []

    def aggregate_evaluate(self, server_round, results, failures):
        return None, {}

    def evaluate(self, server_round, parameters):
        return None


def main():
    certificates = None
    if TLS:
        certificates = tuple((CERTS / f).read_bytes() for f in ("ca.crt", "server.pem", "server.key"))
    log(f"SERVER_START tls={int(TLS)} rounds={ROUNDS} round_timeout={ROUND_TIMEOUT}")
    fl.server.start_server(
        server_address="115.146.84.72:5010",
        config=fl.server.ServerConfig(num_rounds=ROUNDS, round_timeout=ROUND_TIMEOUT),
        strategy=MatrixAverageStrategy(),
        certificates=certificates,
    )
    log("SERVER_DONE")


if __name__ == "__main__":
    main()
