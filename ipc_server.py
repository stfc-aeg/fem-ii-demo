'''
    Server with N hardware devices
    Communicates with N number of ipc_clients
    Uses Ipc Message formatting

'''

import zmq
import time
import threading
import argparse
import random
from _ipc_message import IpcMessage, IpcMessageException
#from odin_data.ipc_message import IpcMessage, IpcMessageException
from HD_DEVICES import HdLed, HdPower, HdTemp, HdMcp230xx
from zmq.utils.strtypes import unicode, cast_bytes


MSG_TYPES = {"CMD"}
MSG_VALS = {"STATUS", "READ", "PROCESS",  "CONFIG", "NOTIFY"}
HD_ADDR = {"0X01", "0X02", "0X03", "0X20"}


class IpcServer:
    """ IpcServer class, represents a server which uses IpcMessaging

    :param port: The port number used
    :param identity: Server identity
    :param url: TCP URL for server
    :param context: ZMQ context
    :param socket: ZMQ socket - ROUTER
    :param address_pool: Set of available hardware addresses
    :param HdMCP: MCP230xx instance
    :param devices: Set of initialised hardware devices
    :param lookup: Address to alias lookup table for hardware device recognition
    :param encoding: the encoding to use for all ipc messaging (msgpack vs JSON)

    """

    def __init__(self, port):

        ident = 'FEMII-ZYNQ'
        self.identity = "Server %s" % ident
        self.url = "tcp://*:%s" % port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.setsockopt(zmq.IDENTITY, self.identity.encode())
        self.thread_return = None
        self.address_pool = ["0X01", "0X02", "0X03", "0X04", "0X05", "0X06"]
        self.HdMCP = HdMcp230xx()
        self.HdMCP.setup_outputs()
        self.devices = [
            HdLed(alias="LED_BLUE", mode="GPIO"), HdTemp(), HdPower(), 
            HdLed(pin=0, alias="LED_RED", mode="MCP", _mcp=self.HdMCP.mcp), 
            HdLed(pin=1, alias="LED_YELLOW", mode="MCP", _mcp=self.HdMCP.mcp), 
            HdLed(pin=2, alias="LED_GREEN", mode="MCP", _mcp=self.HdMCP.mcp)
        ]
        self.lookup = {}
        self.encoding = "wibble wobbley"

    def bind(self):
        """ binds the zmq socket """
        self.socket.bind(self.url)

    def assign_addresses(self):
        ''' Assign addresses to hardware devices.

        Assigns an address from address_pool to
        all registered hardware devices in self.devices
        '''

        x = 0
        for device in self.devices:
            if x < len(self.address_pool):
                device.set_addr(self.address_pool[x])
                x += 1

    def make_lookup(self):
        ''' Generates list of alias names and their addresses '''

        for device in self.devices:
            address = device.get_addr()
            alias = device.get_alias()
            self.lookup[alias] = address

    def process_address(self, alias):
        ''' Return the address of the alias in request

        :param alias: the device alias name to search for
        Returns the address of the device from the lookup table

        '''

        for device in self.devices:
            if alias == device.get_alias():
                address = device.get_addr()

        return address

    def run_long_process(self, req_device, process, request):
        """ Thread method to run a long process on a device

        :param req_device: The device to run the process on
        :param process: The process to run
        :param request: The ipc message request sent from the client 
        """

        # This makes no sense with more than 1 thread running..
        self.thread_return = None

        if process == "BLINK":
            try:
                req_timeout = request.get_param("TIMEOUT")
                req_rate = request.get_param("RATE")
                """Currently not operating as process returns True 
                AFTER process has completed...
                """
                self.thread_return = req_device.run_process(
                    process, 
                    req_timeout, 
                    req_rate
                )
            except IpcMessageException as e:
                self.thread_return = False

    def handle_start_process(self, req_process, req_device, request):
        """ Manage a 'START' process request
        
        :param req_process: the process to perform
        :parm req_device: the device to perform the process on
        :param request: the ipc message request from the client

        Returns the formatted response from the server to indicate that the
        process has been started at the given address
        """
        if req_device.process_running(req_process) is False:
            thread = threading.Thread(
                target=self.run_long_process, 
                args=(req_device, req_process, request)
            )
            thread.daemon = True
            thread.start()
            reply = "Started %s process on %s at address %s. \n" % (
                req_process,
                req_device.get_alias(),
                req_device.get_addr()
            )
        else:
            reply = "Process %s on %s at address %s is already running.\n" % (
                req_process,
                req_device.get_alias(),
                req_device.get_addr()
            )
        return reply

    def handle_stop_process(self, req_process, req_device):
        """ Manage a 'STOP' process request
        
        :param req_process: the process to perform
        :parm req_device: the device to perform the process on

        Returns the formatted response from the server to indicate that the
        process has been stopped at the given address
        """

        req_device.stop_process(req_process)
        return "Stopped %s process on %s at address %s.\n" % (
            req_process,
            req_device.get_alias(),
            req_device.get_addr()
        )

    def handle_config(self, req_device, req_config):
        """ Manage a 'CONFIG' request
        
        :param req_device: the device to configure
        :parm req_config: the configuration value

        Returns the formatted response from the server to indicate that the
        configuration has been changed at the given address
        """
        req_device.set_config(req_config)
        return "Set %s at %s to: %s.\n" % (
            req_device.get_alias(),
            req_device.get_addr(),
            req_device.get_config()
        )

    def handle_read(self, req_device):
        """ Manage a 'READ' request
        
        :param req_device: the device to read from

        Returns the formatted response from the server including the value 
        from the device at the given address
        """

        rep_value = req_device.get_data()
        return "Value of %s at address %s is: %s.\n" % (
            req_device.get_alias(),
            req_device.get_addr(),
            rep_value
        )

    def handle_status(self, req_device):
        """ Manage a 'STATUS' request
        
        :param req_device: the device to get the status from

        Returns the formatted response from the server including the status 
        of the device at the given address
        """
        rep_status = req_device.get_status()
        return "Status of %s at address %s is: %s.\n" % (
            req_device.get_alias(),
            req_device.get_addr(),
            rep_status
        )

    def run_rep(self):
        """ Synchronose Req-REP loop : Waits for a request from a client, 
        processes and returns a response.
        
        Method receives a multipart message from a client, decodes and handles
        different requests including single or multi device requests. 
        Formats a suitable multipart response to send back to the same client 
        using IPC Message, msg_val = NOTIFY
        
        """

        while True:

            try:
                client_address, request = self.socket.recv_multipart()
                request = IpcMessage(from_str=request)
                print("received request : %s from %s" % (
                    request,
                    client_address.decode()
                    ))

                # Device alias name 
                req_alias = request.get_param("DEVICE")
                req_msg_val = request.get_msg_val()
                req_device = None
                req_config = None
                reply_string = "Internal Error"
                reply_message = IpcMessage(msg_type="CMD", msg_val="NOTIFY", encoding=self.encoding)

                if req_alias == "LED_ALL":
                    # No address for a multi device call
                    req_address = req_alias
                    reply = ""
                    if req_msg_val == "PROCESS":
                        req_process = request.get_param("PROCESS")
                        pro_type, req_process = req_process.split("_")

                        if pro_type == "START":
                            for req_device in self.devices:
                                if "LED" in req_device.get_alias():
                                    reply += self.handle_start_process(
                                        req_process,
                                        req_device,
                                        request
                                    )
                        elif pro_type == "STOP":
                            for req_device in self.devices:
                                if "LED" in req_device.get_alias():
                                    reply += self.handle_stop_process(
                                        req_process,
                                        req_device
                                    )
                        else:
                            reply = "Process type not recognised"
                    elif req_msg_val == "CONFIG":
                        req_config = request.get_param("CONFIG")
                        for req_device in self.devices:
                            if "LED" in req_device.get_alias():
                                reply += self.handle_config(
                                    req_device,
                                    req_config
                                )
                    elif req_msg_val == "STATUS":
                        for req_device in self.devices:
                            if "LED" in req_device.get_alias():
                                reply += self.handle_status(req_device)
                    elif req_msg_val == "READ":
                        for req_device in self.devices:
                            if "LED" in req_device.get_alias():
                                reply += self.handle_read(req_device)
                    elif req_msg_val not in MSG_VALS:
                        reply = "Msg Value not recognised"

                    if reply == "":
                        reply = "Internal error"

                else:
                    reply = ""
                    req_address = self.process_address(req_alias)

                    # Find the device registered
                    for device in self.devices:
                        if req_address == device.get_addr():
                            req_device = device

                    if req_msg_val == "PROCESS":
                        req_process = request.get_param("PROCESS")
                        pro_type, req_process = req_process.split("_")

                        if pro_type == "START":
                            reply += self.handle_start_process(
                                req_process,
                                req_device,
                                request
                            )
                        elif pro_type == "STOP":
                            reply += self.handle_stop_process(
                                req_process,
                                req_device
                            )
                        else:
                            reply = "Process type not recognised"

                    elif req_msg_val == "CONFIG":
                        req_config = request.get_param("CONFIG")
                        reply += self.handle_config(req_device, req_config)

                    elif req_msg_val == "STATUS":
                        reply += self.handle_status(req_device)

                    elif req_msg_val == "READ":
                        reply += self.handle_read(req_device)
                    elif req_msg_val not in MSG_VALS:
                        reply = "Msg Value not recognised"

                    if reply == "":
                        reply = "Internal error"

                reply_string = "Processed Request from %s\n: %s" % (
                    client_address.decode(),
                    reply
                )
                reply_message.set_param("REPLY", reply_string)
                reply_message = reply_message.encode()

                if isinstance(reply_message, unicode):
                    reply_message = cast_bytes(reply_message)

                self.socket.send_multipart(
                    [client_address,
                     b"",
                     reply_message,
                    ]
                )

            except IpcMessageException as err:
                print("IPC MESSAGE Error Found %s: " % str(err))


def main(): 

    # Accept command line arguments for the port
    parser = argparse.ArgumentParser()
    parser.add_argument("-port", "--port", help="Port connection, default = 5555", 
                        default="5555")
    args = parser.parse_args()
    server = IpcServer(args.port)

    # Configure hardware addresses and alias look up tables
    server.assign_addresses()
    server.make_lookup()
    print("Hardware device address tree:")
    print(server.lookup)

    server.bind()
    server.run_rep()


if __name__ == "__main__":
    main()
