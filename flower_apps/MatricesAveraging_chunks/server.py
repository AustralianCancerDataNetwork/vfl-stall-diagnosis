"""
VFL Chunked Transfer - SERVER

Design:
- Server knows NUM_CHUNKS upfront (set manually here)
- Server does NOT tell clients how to chunk or what chunk to send
- Server just collects chunks round by round, waits until it has
  NUM_CHUNKS from every client, then reassembles and averages
- Clients decide everything about chunking on their own side
"""

import os
os.environ["GRPC_ARG_KEEPALIVE_TIME_MS"]    = "60000"   # ping every 60s
os.environ["GRPC_ARG_KEEPALIVE_TIMEOUT_MS"] = "30000"   # wait 30s for pong
os.environ["GRPC_ARG_KEEPALIVE_PERMIT_WITHOUT_CALLS"] = "1"

import flwr as fl
from flwr.common import (
    Parameters,
    FitIns,
    FitRes,
    EvaluateIns,
    EvaluateRes,
    Scalar,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)
from flwr.server.client_proxy import ClientProxy
from typing import List, Tuple, Dict, Optional, Union
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# SERVER CONFIG — set manually to match whatever the clients decided
# ─────────────────────────────────────────────────────────────────────────────

SERVER_ADDR = "115.146.84.72:5010"
NUM_CHUNKS  = 5      # <-- change this to match client setting (5, 10, 20, 100...)
NUM_CLIENTS = 3
NUM_CYCLES  = 10     # how many full matrix transfers to do
NUM_ROUNDS  = NUM_CHUNKS * NUM_CYCLES   # total Flower rounds = 50

# ─────────────────────────────────────────────────────────────────────────────


class ChunkedStrategy(fl.server.strategy.Strategy):

    def __init__(self):
        # chunk_buffer[cid] = list of chunks received so far this cycle
        self.chunk_buffer: Dict[str, List[np.ndarray]] = {}
        self.current_cycle = 1

    def initialize_parameters(self, client_manager) -> Optional[Parameters]:
        return ndarrays_to_parameters([np.array([0.0])])  # dummy

    def configure_fit(
        self,
        server_round: int,
        parameters: Parameters,
        client_manager: fl.server.ClientManager,
    ) -> List[Tuple[ClientProxy, FitIns]]:

        # Work out where we are — purely for logging
        chunk_number_in_cycle = (server_round - 1) % NUM_CHUNKS + 1

        print(f"\n{'='*60}")
        print(f"  Round {server_round}  |  Cycle {self.current_cycle}  |  Collecting chunk {chunk_number_in_cycle} of {NUM_CHUNKS}")
        print(f"{'='*60}")

        clients = client_manager.sample(
            num_clients=NUM_CLIENTS,
            min_num_clients=NUM_CLIENTS,
        )

        # Send nothing special — just an empty config
        # Clients drive their own chunking
        fit_ins = FitIns(parameters=parameters, config={"round": server_round})

        return [(client, fit_ins) for client in clients]

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, FitRes]],
        failures,
    ) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:

        chunk_number_in_cycle = (server_round - 1) % NUM_CHUNKS + 1
        is_last_chunk = (chunk_number_in_cycle == NUM_CHUNKS)

        print(f"\n  [Server] Received chunk {chunk_number_in_cycle}/{NUM_CHUNKS} from all clients")

        # ── Step 1: Store this round's chunk from each client ──────────
        for client_proxy, fit_res in results:
            cid   = fit_res.metrics.get("cid", "unknown")
            chunk = parameters_to_ndarrays(fit_res.parameters)[0]

            if cid not in self.chunk_buffer:
                self.chunk_buffer[cid] = []

            self.chunk_buffer[cid].append(chunk)

            print(f"    [{cid}] chunk {chunk_number_in_cycle} stored | shape={chunk.shape}")

        # ── Step 2: If all chunks are in, reassemble and average ───────
        if is_last_chunk:
            print(f"\n  [Server] All {NUM_CHUNKS} chunks received — reassembling...")

            full_matrices = []

            for cid, chunks in self.chunk_buffer.items():
                # Stack chunks side by side to rebuild full matrix
                full_matrix = np.hstack(chunks)
                full_matrices.append(full_matrix)
                print(f"    [{cid}] reassembled → shape={full_matrix.shape}  mean={full_matrix.mean():.4f}")

            # Average across all clients (element-wise)
            averaged = np.mean(full_matrices, axis=0)
            print(f"\n  [Server] Averaged matrix → shape={averaged.shape}  mean={averaged.mean():.4f}")

            # ── YOUR VFL LOGIC GOES HERE ───────────────────────────────
            # e.g. use `averaged` as the aggregated embedding for backprop

            # Reset buffer for next cycle
            self.chunk_buffer.clear()
            print(f"  [Server] Cycle {self.current_cycle} complete. Buffer cleared.\n")
            self.current_cycle += 1

        return ndarrays_to_parameters([np.array([0.0])]), {}

    def configure_evaluate(self, server_round, parameters, client_manager):
        return []  # skip evaluation

    def aggregate_evaluate(self, server_round, results, failures):
        return None, {}

    def evaluate(self, server_round, parameters):
        return None


def main():
    print(f"\n[Server] Starting on {SERVER_ADDR}")
    print(f"[Server] Expecting {NUM_CHUNKS} chunks per client per cycle")
    print(f"[Server] {NUM_CYCLES} cycles × {NUM_CHUNKS} chunks = {NUM_ROUNDS} total rounds\n")

    fl.server.start_server(
        server_address=SERVER_ADDR,
        config=fl.server.ServerConfig(num_rounds=NUM_ROUNDS, round_timeout=120),
        strategy=ChunkedStrategy(),
    )

    print("\n[Server] Done.")


if __name__ == "__main__":
    main()