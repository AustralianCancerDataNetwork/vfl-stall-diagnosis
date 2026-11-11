"""
VFL Debug - Phase 1: Bare-bones server
- Collects a single float from each of 3 clients
- Averages them using a custom strategy
- Prints result each round
- No model, no dataset, no tensors
"""

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

BLUE = "\033[94m"
RESET = "\033[0m"


# ─── Custom Strategy ────────────────────────────────────────────────────────

class AverageNumberStrategy(fl.server.strategy.Strategy):
    """
    Minimal custom strategy:
    - Sends a dummy instruction to all clients each round
    - Collects one float from each client
    - Averages them and prints the result
    """

    def __init__(self, num_rounds: int = 3):
        self.num_rounds = num_rounds

    def initialize_parameters(
        self, client_manager: fl.server.ClientManager
    ) -> Optional[Parameters]:
        
        print(BLUE + f"\n-----------Start of initialize_parameters-----------\n" + RESET)

        """No global model parameters needed."""
        print("[Server] initialize_parameters called")

        print(BLUE + f"\n-----------End of initialize_parameters-----------\n" + RESET)

        return ndarrays_to_parameters([np.array([0.0])])  # dummy

    def configure_fit(
        self,
        server_round: int,
        parameters: Parameters,
        client_manager: fl.server.ClientManager,
    ) -> List[Tuple[ClientProxy, FitIns]]:
        
        print(f"\n--------------------------------------[Server] | Round {server_round}--------------------------------------\n")
        
        print(BLUE + f"\n-----------Start of configure_fit-----------\n" + RESET)
        
        """Tell all clients to send their number."""
        

        # Wait until all 3 clients are connected
        clients = client_manager.sample(
            num_clients=3,
            min_num_clients=3,
        )
        print(f"[Server] Sampled {len(clients)} clients")

        fit_ins = FitIns(parameters=parameters, config={"round": server_round})

        print(BLUE + f"\n-----------End of configure_fit-----------\n" + RESET)
        return [(client, fit_ins) for client in clients]

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, FitRes]],
        failures: List[Union[Tuple[ClientProxy, FitRes], BaseException]],
    ) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
        
        print(BLUE + f"\n-----------Start of aggregate_fit-----------\n" + RESET)
        
        """Average the float received from each client."""
        print(f"[Server] aggregate_fit | Round {server_round}")

        if failures:
            print(f"[Server] WARNING: {len(failures)} client(s) failed: {failures}")

        values = []
        for client_proxy, fit_res in results:
            arrays = parameters_to_ndarrays(fit_res.parameters)
            client_value = float(arrays[0][0])
            cid = fit_res.metrics.get("cid", "unknown")
            print(f"  -> Client [{cid}] sent value: {client_value}")
            values.append(client_value)

        if not values:
            print("[Server] No values received!")
            return None, {}

        average = float(np.mean(values))
        print(f"[Server] Average of received values: {average:.4f}")

        print(BLUE + f"\n-----------End of aggregate_fit-----------\n" + RESET)

        return ndarrays_to_parameters([np.array([average])]), {"average": average}

    def configure_evaluate(
        self,
        server_round: int,
        parameters: Parameters,
        client_manager: fl.server.ClientManager,
    ) -> List[Tuple[ClientProxy, EvaluateIns]]:
        
        print(BLUE + f"\n-----------Start of configure_evaluate-----------\n" + RESET)

        """Skip evaluation in Phase 1."""
        print(f"[Server] configure_evaluate | Round {server_round} (skipped)")

        print(BLUE + f"\n-----------End of configure_evaluate-----------\n" + RESET)
        return []

    def aggregate_evaluate(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, EvaluateRes]],
        failures: List[Union[Tuple[ClientProxy, EvaluateRes], BaseException]],
    ) -> Tuple[Optional[float], Dict[str, Scalar]]:
        
        print(BLUE + f"\n-----------Start of aggregate_evaluate-----------\n" + RESET)

        print(BLUE + f"\n-----------End of aggregate_evaluate-----------\n" + RESET)


        """Nothing to aggregate."""
        return None, {}

    def evaluate(
        self,
        server_round: int,
        parameters: Parameters,
    ) -> Optional[Tuple[float, Dict[str, Scalar]]]:
        
        print(BLUE + f"\n-----------Start of evaluate-----------\n" + RESET)
        
        print("this is server evaluate")

        print(BLUE + f"\n-----------End of evaluate-----------\n" + RESET)
        """No server-side evaluation."""
        return None


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    strategy = AverageNumberStrategy()

    print("[Server] Starting Flower server on port 8080...")
    print("[Server] Waiting for 3 clients to connect...\n")

    fl.server.start_server(
        server_address="0.0.0.0:5010",
        config=fl.server.ServerConfig(num_rounds=100),
        strategy=strategy,
    )

    print("\n[Server] All rounds complete. Done.")


if __name__ == "__main__":
    main()