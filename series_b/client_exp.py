"""
Journal experiment client: MatricesAveraging client with optional TLS and timestamped rounds.

Usage: client_exp.py <cid>, configured by environment:
  COLS=1000  matrix is 5 x COLS, float16 (as in MatricesAveraging/client_*.py)
  TLS=1      connect over TLS, trusting flower_apps/NNVertical/certificates/ca.crt
"""

import os
import sys
import time
from pathlib import Path

import flwr as fl
import numpy as np
from flwr.common import Code, EvaluateRes, FitRes, Status, ndarrays_to_parameters

CID = sys.argv[1]
SERVER = "115.146.84.72:5010"
MATRIX_SHAPE = (5, int(os.environ.get("COLS", "1000")))
TLS = os.environ.get("TLS") == "1"
CA = Path(__file__).resolve().parents[1] / "flower_apps/NNVertical/certificates/ca.crt"


def log(msg):
    print(f"{time.time():.3f} [{CID}] {msg}", flush=True)


class MatrixClient(fl.client.Client):

    def get_parameters(self, ins):
        return fl.common.GetParametersRes(
            status=Status(code=Code.OK, message="OK"),
            parameters=ndarrays_to_parameters([np.array([1.0])]),
        )

    def fit(self, ins):
        server_round = ins.config.get("round", "?")
        log(f"FIT_RECEIVED {server_round}")
        matrix = np.random.rand(*MATRIX_SHAPE).astype(np.float16)
        log(f"FIT_RETURN {server_round} shape={matrix.shape}")
        return FitRes(
            status=Status(code=Code.OK, message="OK"),
            parameters=ndarrays_to_parameters([matrix]),
            num_examples=1,
            metrics={"cid": CID},
        )

    def evaluate(self, ins):
        return EvaluateRes(status=Status(code=Code.OK, message="OK"), loss=0.0, num_examples=1, metrics={})


log(f"CONNECT {SERVER} tls={int(TLS)} shape={MATRIX_SHAPE}")
fl.client.start_client(
    server_address=SERVER,
    client=MatrixClient(),
    transport="grpc-bidi",
    root_certificates=CA.read_bytes() if TLS else None,
)
log("DONE")
