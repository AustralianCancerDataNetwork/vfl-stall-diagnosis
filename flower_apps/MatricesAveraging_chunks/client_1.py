"""
VFL Chunked Transfer - CLIENT 1

Design:
- Client owns the chunking entirely
- Client decides NUM_CHUNKS (5, 10, 20, 100... whatever fits in gRPC)
- Splits matrix column-wise, sends one chunk per round
- Tracks which chunk to send via a simple counter
- Server is never told chunk numbers — it just collects and reassembles
"""

import os
os.environ["GRPC_ARG_KEEPALIVE_TIME_MS"]    = "60000"   # ping every 60s
os.environ["GRPC_ARG_KEEPALIVE_TIMEOUT_MS"] = "30000"   # wait 30s for pong
os.environ["GRPC_ARG_KEEPALIVE_PERMIT_WITHOUT_CALLS"] = "1"

import flwr as fl
from flwr.common import (
    FitIns,
    FitRes,
    EvaluateIns,
    EvaluateRes,
    Status,
    Code,
    ndarrays_to_parameters,
)
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# CLIENT CONFIG — client decides chunking independently
# ─────────────────────────────────────────────────────────────────────────────

CID          = "client_1"
SERVER       = "115.146.84.72:5010"
MATRIX_SHAPE = (5, 10000)   # full local matrix size
NUM_CHUNKS   = 200           # <-- client decides: 5, 10, 20, 100...
                           #     server.py must have the same NUM_CHUNKS value

# ─────────────────────────────────────────────────────────────────────────────


class ChunkedClient(fl.client.Client):

    def __init__(self):
        # Build the full matrix once (replace with real data / forward pass output)
        self.matrix = np.random.rand(*MATRIX_SHAPE).astype(np.float16)

        # Pre-split into chunks along columns
        # np.array_split handles non-divisible sizes gracefully
        self.chunks = np.array_split(self.matrix, NUM_CHUNKS, axis=1)

        # Counter: which chunk to send next
        self.next_chunk = 0

        print(f"[{CID}] Matrix shape: {self.matrix.shape}")
        print(f"[{CID}] Split into {NUM_CHUNKS} chunks:")
        for i, c in enumerate(self.chunks):
            print(f"         chunk {i}: shape={c.shape}  size={c.nbytes} bytes")

    def get_parameters(self, ins):
        return fl.common.GetParametersRes(
            status=Status(code=Code.OK, message="OK"),
            parameters=ndarrays_to_parameters([np.array([0.0])]),
        )

    def fit(self, ins: FitIns) -> FitRes:
        server_round = ins.config.get("round", "?")

        # Pick the current chunk and advance the counter
        chunk_to_send = self.chunks[self.next_chunk]

        print(f"[{CID}] Round {server_round} → sending chunk {self.next_chunk}/{NUM_CHUNKS-1} | shape={chunk_to_send.shape}")

        self.next_chunk = (self.next_chunk + 1) % NUM_CHUNKS

        return FitRes(
            status=Status(code=Code.OK, message="OK"),
            parameters=ndarrays_to_parameters([chunk_to_send]),
            num_examples=1,
            metrics={"cid": CID},   # server only needs to know who sent it
        )

    def evaluate(self, ins: EvaluateIns) -> EvaluateRes:
        return EvaluateRes(
            status=Status(code=Code.OK, message="OK"),
            loss=0.0,
            num_examples=1,
            metrics={},
        )


print(f"\n[{CID}] Connecting to {SERVER} ...")
fl.client.start_client(
    server_address=SERVER,
    client=ChunkedClient(),
    transport='grpc-bidi',
)
print(f"[{CID}] Done.")