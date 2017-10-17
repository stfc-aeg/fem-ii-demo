import ipc_client
import ipc_server

import zmq
from odin_data.ipc_message import IpcMessage


def main():

    client = ipc_client.ipc_client()
    server = ipc_server.ipc_server()

    server.bind()
    client.connect()

    while True:
       
        server.run_rep()
        client.run_req()

if __name__ == "__main__":
    main()