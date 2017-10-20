'''
    Server with three emulated hardware devices
    Communicates with N number of ipc_clients
    Uses Ipc Message formatting


'''

import zmq
import argparse
from odin_data.ipc_message import IpcMessage, IpcMessageException
from HD_DEVICES import HD_LED, HD_POWER, HD_TEMP
from zmq.utils.strtypes import unicode, cast_bytes


MSG_TYPES = {"CMD"}
MSG_VALS = {"STATUS", "CONFIG", "NOTIFY"}
HD_ADDR = {"0X01", "0X02", "0X03"}


class IpcServer:

    def __init__(self, port):

        ident = 'FEMII-ZYNQ'
        self.identity = "Server %s" % ident
        self.url = "tcp://*:%s" % port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.setsockopt(zmq.IDENTITY, self.identity.encode())
        self.address_pool = ["0X01", "0X02", "0X03", "0X04", "0X05"]
        self.devices = [HD_LED(), HD_TEMP(), HD_POWER()]
        self.lookup = {}

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

    def process_address(self, request):
        ''' Return the address of the alias in request
        
        :param request: the IPCmessage from the client request
        Returns the address of the device from the lookup table

        '''

        _alias = request.get_param("DEVICE")
        for device in self.devices:
            if _alias == device.get_alias():
                address = device.get_addr()

        return address
    
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
                
                # get the address of the device
                req_address = self.process_address(request)

                # get the message value (CONFIG/STATUS/READ)
                req_msg_val = request.get_msg_val()
                req_device = None
                req_config = None

                reply_message = IpcMessage(msg_type="CMD", msg_val="NOTIFY")
                
                # Find the device attached to that request address
                for device in self.devices:
                    if req_address == device.get_addr():
                        req_device = device

                if req_msg_val == "CONFIG":
                    req_config = request.get_param("CONFIG")
                    req_device.set_config(req_config)
                    reply_string = "Processed Request from %s. Set %s at \
                                    address %s to: %s." % (client_address.decode(), 
                                    req_alias, req_address, req_device.get_config())

                if req_msg_val == "STATUS":
                    rep_status = req_device.get_status()
                    reply_string = "Processed Request from %s. Status of %s at \
                                    address %s is: %s." % (client_address.decode(), 
                                    req_alias, req_address, rep_status)

                if req_msg_val == "READ":
                    rep_value = req_device.get_data()
                    reply_string = "Processed Request from %s. Value of %s at \
                                    address %s is: %s." % (client_address.decode(), 
                                    req_alias, req_address, rep_value)

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
