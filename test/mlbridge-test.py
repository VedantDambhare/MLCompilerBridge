# ------------------------------------------------------------------------------
#
# Part of the MLCompilerBridge Project, under the Apache License v2.0 with LLVM
# Exceptions. See the LICENSE file for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
#
# ------------------------------------------------------------------------------

import argparse
import numpy as np
import ctypes

import sys
import torch, torch.nn as nn

sys.path.append("../CompilerInterface")
from PipeCompilerInterface import PipeCompilerInterface
from GrpcCompilerInterface import GrpcCompilerInterface

sys.path.append("../MLModelRunner/gRPCModelRunner/Python-Utilities")
import helloMLBridge_pb2, helloMLBridge_pb2_grpc, grpc
from concurrent import futures

FAIL = 1
SUCCESS = 0

parser = argparse.ArgumentParser()
parser.add_argument(
    "--use_pipe", type=bool, default=False, help="Use pipe or not", required=False
)
parser.add_argument(
    "--data_format",
    type=str,
    choices=["json", "protobuf", "bytes"],
    help="Data format to use for communication",
)
parser.add_argument(
    "--pipe_name",
    type=str,
    help="Pipe Name",
)
parser.add_argument(
    "--silent", type=bool, help="Only prints errors when set to true", default=False
)
parser.add_argument(
    "--use_grpc",
    action="store_true",
    help="Use grpc communication",
    required=False,
    default=False,
)
parser.add_argument(
    "--server_port",
    type=int,
    help="Server Port",
    default=5050,
)
args = parser.parse_args()


class DummyModel(nn.Module):
    def __init__(self, input_dim=10):
        nn.Module.__init__(self)
        self.fc1 = nn.Linear(input_dim, 1)

    def forward(self, input):
        x = self.fc1(input)
        return x


expected_type = {
    1: "int",
    2: "long",
    3: "float",
    4: "double",
    5: "char",
    6: "bool",
    7: "vec_int",
    8: "vec_long",
    9: "vec_float",
    10: "vec_double",
}

expected_data = {
    1: 11,
    2: 1234567890,
    3: 3.14,
    4: 0.123456789123456789,
    5: ord("a"),
    6: True,
    7: [11, 22, 33],
    8: [123456780, 222, 333],
    9: [11.1, 22.2, 33.3],
    10: [-1.1111111111, -2.2222222222, -3.3333333333],
}

returned_data = {
    1: 12,
    2: ctypes.c_long(1234567891),
    3: 4.14,
    4: ctypes.c_double(1.123456789123456789),
    5: ord("b"),
    6: False,
    7: [12, 23, 34],
    8: [ctypes.c_long(123456780), ctypes.c_long(123456781), ctypes.c_long(123456782)],
    9: [1.11, 2.22, -3.33, 0],
    10: [ctypes.c_double(1.12345678912345670), ctypes.c_double(-1.12345678912345671)],
}

# may not be configured for extended types
if args.data_format == "json":
    returned_data[2] = ctypes.c_long(12345)
    returned_data[8] = [
        ctypes.c_long(6780),
        ctypes.c_long(6781),
        ctypes.c_long(6782),
    ]  # [ctypes.c_long(6780),ctypes.c_long(6781),ctypes.c_long(6782)],


def run_pipe_communication(data_format, pipe_name):
    compiler_interface = PipeCompilerInterface(data_format, "/tmp/" + pipe_name)
    if not args.silent:
        print("PipeCompilerInterface init...")
    compiler_interface.reset_pipes()

    status = SUCCESS
    i = 0
    while True:
        i += 1
        try:
            data = compiler_interface.evaluate()
            if data_format == "json":
                key = list(data)[0]
                data = data[key]
            elif data_format == "bytes":
                data = [x for x in data[0]]
                if len(data) == 1:
                    data = data[0]

            if not args.silent:
                print(" ", expected_type[i], "request:", data)

            if isinstance(expected_data[i], list):
                for e, d in zip(expected_data[i], data):
                    if abs(e - d) > 10e-6:
                        print(
                            f"Error: Expected {expected_type[i]} request: {expected_data[i]}, Received: {data}"
                        )
                        status = FAIL
                        # raise Exception(f"Mismatch in {expected_type[i]}")

            elif abs(data - expected_data[i]) > 10e-6:
                print(
                    f"Error: Expected {expected_type[i]} request: {expected_data[i]}, Received: {data}"
                )
                status = FAIL
                # raise Exception(f"Mismatch in {expected_type[i]}")

            compiler_interface.populate_buffer(returned_data[i])

            if i == len(expected_type):
                data = compiler_interface.evaluate(mode="exit")
                exit(status)
        except Exception as e:
            print("*******Exception*******", e)
            compiler_interface.reset_pipes()


class service_server(helloMLBridge_pb2_grpc.HelloMLBridgeService):
    def __init__(self, data_format, pipe_name):
        # self.serdes = SerDes.SerDes(data_format, pipe_name)
        # self.serdes.init()
        pass

    def getAdvice(self, request, context):
        try:
            print(request)
            print("Entered getAdvice")
            print("Data: ", request.tensor)
            reply = helloMLBridge_pb2.ActionRequest(action=1)
            return reply
        except:
            reply = helloMLBridge_pb2.ActionRequest(action=-1)
            return reply


def test_func():
    data = 3.24
    import struct

    print(data, type(data))
    byte_data = struct.pack("f", data)
    print(byte_data, len(byte_data))

    print("decoding...")
    decoded = float(byte_data)

    print(decoded, type(decoded))


if __name__ == "__main__":
    if args.use_pipe:
        run_pipe_communication(args.data_format, args.pipe_name)
    elif args.use_grpc:
        compiler_interface = GrpcCompilerInterface(
            mode="server",
            add_server_method=helloMLBridge_pb2_grpc.add_HelloMLBridgeServiceServicer_to_server,
            grpc_service_obj=service_server(),
            hostport=args.server_port,
        )
        compiler_interface.start_server()
