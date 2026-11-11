"""
VFL Debug - Phase 1: Client 1 (client_V)
"""

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

CID = "client_2"
VALUE = 2.0
SERVER = "127.0.0.1:5010"

BLUE = "\033[94m"
RESET = "\033[0m"


class NumberClient(fl.client.Client):

    def get_parameters(self, ins):

        print(BLUE + f"\n-----------Start of get_parameters-----------\n" + RESET)

        print("First client to be connected")

        print(BLUE + f"\n-----------Start of get_parameters-----------\n" + RESET)

        return fl.common.GetParametersRes(
            status=Status(code=Code.OK, message="OK"),
            parameters=ndarrays_to_parameters([np.array([VALUE])]),
        )

    def fit(self, ins: FitIns) -> FitRes:
        server_round = ins.config.get("round", "?")

        print(f"\n----------------------------------------[{CID}] fit | Round {server_round} | Sending value={VALUE}----------------------------------------\n")

        print(BLUE + f"\n-----------Start of fit-----------\n" + RESET)

        

        print(BLUE + f"\n-----------End of fit-----------\n" + RESET)
        return FitRes(
            status=Status(code=Code.OK, message="OK"),
            parameters=ndarrays_to_parameters([np.array([VALUE])]),
            num_examples=1,
            metrics={"cid": CID, "value": VALUE},
        )

    def evaluate(self, ins: EvaluateIns) -> EvaluateRes:

        print(BLUE + f"\n-----------Start of Evaluate-----------\n" + RESET)


        print("Evaluate method")

        print(BLUE + f"\n-----------End of Evaluate-----------\n" + RESET)
        return EvaluateRes(
            status=Status(code=Code.OK, message="OK"),
            loss=0.0,
            num_examples=1,
            metrics={},
        )


print(f"[{CID}] Connecting to {SERVER} ...")
fl.client.start_client(server_address=SERVER, client=NumberClient())
print(f"[{CID}] Done.")