'''
    Server with three emulated hardware devices
    Communicates with N number of ipc_clients
    Uses Ipc Message formatting


'''

import zmq
import time
import threading
import argparse
import random
from odin_data.ipc_message import IpcMessage, IpcMessageException
from HD_DEVICES import HdLed, HdPower, HdTemp, HdMcp230xx
from zmq.utils.strtypes import unicode, cast_bytes


MSG_TYPES = {"CMD"}
MSG_VALS = {"STATUS", "READ", "PROCESS",  "CONFIG", "NOTIFY"}
HD_ADDR = {"0X01", "0X02", "0X03", "0X20"}


class IpcServer:

    def __init__(self, port):

        ident = 'FEMII-ZYNQ'
        self.identity = "Server %s" % ident
        self.url = "tcp://*:%s" % port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.setsockopt(zmq.IDENTITY, self.identity.encode())
        self.thread_return = None
        """
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.setsockopt(zmq.IDENTITY, self.identity.encode())
        """
        self.address_pool = ["0X01", "0X02", "0X03", "0X04", "0X05", "0X06"]


        self.HdMCP = HdMcp230xx()
        self.HdMCP.setup_outputs()
        
        self.devices = [HdLed(alias="LED_BLUE", mode="GPIO"), HdTemp(), HdPower(), HdLed(pin=0, alias="LED_RED", mode="MCP", _mcp=self.HdMCP.mcp), HdLed(pin=1, alias="LED_YELLOW", mode="MCP", _mcp=self.HdMCP.mcp), HdLed(pin=2, alias="LED_GREEN", mode="MCP", _mcp=self.HdMCP.mcp)]
        self.lookup = {}

    def bind(self):
        """ binds both of the zmq sockets """
        self.socket.bind(self.url)
        #self.publisher.bind("tcp://*:5556")

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
        
        :param request: the IPCmessage from the client request
        Returns the address of the device from the lookup table

        '''

        for device in self.devices:
            if alias == device.get_alias():
                address = device.get_addr()

        return address

    def run_long_process(self, req_device, process, request):

        # This makes no sense with more than 1 thread running..
        self.thread_return = None

        if process == "BLINK":
            try:
                req_timeout = request.get_param("TIMEOUT")
                req_rate = request.get_param("RATE")
                # Currently not operating as process returns True AFTER process has completed...
                self.thread_return = req_device.run_process(process, req_timeout, req_rate)
            except IpcMessageException as e:
                self.thread_return = False
              
    def handle_start_process(self, req_process, req_device, request):

        if req_device.process_running(req_process) == False:
            thread = threading.Thread(target=self.run_long_process, args=(req_device, req_process, request))
            thread.daemon = True
            thread.start()
            reply = "Started %s process on %s at address %s. \n" % (req_process, req_device.get_alias(), req_device.get_addr())
        else:
            reply = "Process %s on %s at address %s is already running.\n" % (req_process, req_device.get_alias(), req_device.get_addr())

        return reply

    def handle_stop_process(self, req_process, req_device):

        req_device.stop_process(req_process)
        return  "Stopped %s process on %s at address %s. \n" % (req_process, req_device.get_alias(), req_device.get_addr())

    def handle_config(self, req_device, req_config):

        req_device.set_config(req_config)
        return "Set %s at %s to: %s. \n" % (req_device.get_alias(), req_device.get_addr(), req_device.get_config())

    def handle_read(self, req_device):

        rep_value = req_device.get_data()
        return "Value of %s at address %s is: %s." % (req_device.get_alias(), req_device.get_addr(), rep_value)

    def handle_status(self, req_device):

        rep_status = req_device.get_status()
        return "Status of %s at address %s is: %s." % (req_device.get_alias(), req_device.get_addr(), rep_status)

    
    def run_rep(self):
        ''' sends a request, waits for a reply, returns response  '''

        while True:

            try:
                client_address, request = self.socket.recv_multipart()
                request = IpcMessage(from_str=request)
                print("received request : %s from %s" % 
                    (request, client_address.decode()))
                
                # Get the alias device name used in the request
                req_alias = request.get_param("DEVICE")
                # get the message value (CONFIG/STATUS/READ)
                req_msg_val = request.get_msg_val()
                req_device = None
                req_config = None
                reply_string = "Internal Error"
                reply_message = IpcMessage(msg_type="CMD", msg_val="NOTIFY")

                if req_alias == "LED_ALL":
                    req_address = req_alias
                    reply = ""
                    if req_msg_val == "PROCESS":
                        req_process = request.get_param("PROCESS")
                        pro_type, req_process = req_process.split("_")

                        if pro_type == "START":
                            for req_device in self.devices:
                                if "LED" in req_device.get_alias():
                                    reply += self.handle_start_process(req_process, req_device, request)

                        elif pro_type == "STOP":
                            for req_device in self.devices:
                                if "LED" in req_device.get_alias():
                                    reply += self.handle_stop_process(req_process, req_device)
                    
                    if req_msg_val == "CONFIG":
                        req_config = request.get_param("CONFIG")
                        for req_device in self.devices:
                            if "LED" in req_device.get_alias():
                                reply += self.handle_config(req_device, req_config)
                        
                    if req_msg_val == "STATUS":
                        for req_device in self.devices:
                            if "LED" in req_device.get_alias():
                                reply += self.handle_status(self, req_device)

                    if req_msg_val == "READ":
                        for req_device in self.devices:
                            if "LED" in req_device.get_alias():
                                reply += self.handle_read(req_device)
                    
                    if reply == "":
                        reply = "Internal error"

                else:
                    reply = ""
                    # get the address of the device
                    req_address = self.process_address(req_alias)
                
                    # Find the device attached to that request address
                    for device in self.devices:
                        if req_address == device.get_addr():
                            req_device = device
                
                    if req_msg_val == "PROCESS":
                        req_process = request.get_param("PROCESS")
                        pro_type, req_process = req_process.split("_")

                        if pro_type == "START":
                            reply += self.handle_start_process(req_process, req_device, request)
                        elif pro_type == "STOP":
                            reply += self.handle_stop_process(req_process, req_device)
                            
                    if req_msg_val == "CONFIG":
                        req_config = request.get_param("CONFIG")
                        reply += self.handle_config(req_device, req_config)
        
                    if req_msg_val == "STATUS":
                        reply += self.handle_status(self, req_device)
                        
                    if req_msg_val == "READ":
                        reply += self.handle_read(req_device)
                    
                    if reply == "":
                        reply = "Internal error"

                    
                reply_string = "Processed Request from %s. %s" % (client_address.decode(), reply)
                reply_message.set_param("REPLY", reply_string)

                # Encode the message for sending
                reply_message = reply_message.encode()

                # check if its unicode, if so covert to bytes
                if isinstance(reply_message, unicode):
                    reply_message = cast_bytes(reply_message)

                # send a multipart back to the client 
                self.socket.send_multipart([client_address, b"", reply_message,])
                
            except IpcMessageException as err:
                print("IPC MESSAGE Error Found %s: " % str(err))


def main(): 

    # Accept command line arguments for the port number used, default is 5555
    parser = argparse.ArgumentParser()
    parser.add_argument("-port", "--port", help="Port connection, default = 5555", 
                        default="5555")
    args = parser.parse_args()

    # Initialise a server
    server = IpcServer(args.port)

    # configure hardware addresses and alias look up tables
    server.assign_addresses()
    server.make_lookup()

    # Display the fake device address tree
    print("Hardware device address tree:") 
    print(server.lookup)

    # bind the socket and run reply loop
    server.bind()
    server.run_rep()


if __name__ == "__main__":
    main()
