'''
    Server with three emulated hardware devices
    Communicates with 


'''

import zmq
from odin_data.ipc_message import IpcMessage, IpcMessageException
from HD_DEVICES import HD_LED, HD_POWER, HD_TEMP
from zmq.utils.strtypes import unicode, cast_bytes

msg_types = {"CMD"}
msg_vals = {"STATUS", "CONFIG", "NOTIFY"}
hd_addrs = { "0X01", "0X02", "0X03"}


class ipc_server:

    def __init__(self):

        ident = b'FEMII-ZYNQ'
        self.identity = "Server {}" % ident
        self.url = "tcp://*:5556"
        self.context = zmq.Context() 
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.setsockopt(zmq.IDENTITY, self.identity.encode())
        self.address_pool = ["0X01","0X02","0X03", "0X04", "0X05"]
        self.devices = [HD_LED(), HD_TEMP(), HD_POWER()]
        self.lookup = {}
    
    def bind(self):

        self.socket.bind(self.url)
    
    #   Assign an address to all registered hardware devices from the address pool
    def assign_addresses(self):

        x = 0
        for device in self.devices:
            if x < len(self.address_pool):
                device.set_addr(self.address_pool[x])
                x += 1

    #   Generates a look up table of hardware alias names and their addresses
    def make_lookup(self):

        for device in self.devices:
            address = device.get_addr()
            alias = device.get_alias()
            self.lookup[alias] = address

    #   Receives a device alias name and returns the address of the device from the lookup table
    def process_address(self, request):

        _alias = request.get_param("DEVICE")
        for device in self.devices:
            if _alias == device.get_alias():
                address = device.get_addr()

        return address
    
    #   sends a request, waits for a reply, processes the request and returns response
    def run_rep(self):

        while True:

            try:
                #   receive the request as a multi-part
                client_address, request = self.socket.recv_multipart()

                #   split off the request part into an IpcMessage
                request = IpcMessage(from_str=request)

                #   Notify user
                print("received request : %s from %s" % (request, client_address.decode()))
                
                #   Get the alias device name used in the request
                req_alias = request.get_param("DEVICE")
                
                #   get the address of the device
                req_address = self.process_address(request)

                #   get the message value (CONFIG/STATUS/READ)
                req_msg_val = request.get_msg_val()
                req_device = None
                req_config = None

                #   configure a reply_message
                reply_message = IpcMessage(msg_type="CMD", msg_val="NOTIFY")
                
                #   Find the device attached to that request address
                for device in self.devices:
                    if req_address == device.get_addr():
                        req_device = device

                #   process a configuration request
                if req_msg_val == "CONFIG":
                    req_config = request.get_param("CONFIG")
                    req_device.set_config(req_config)
                    reply_string = "Processed Request from %s. Set %s at address %s to: %s." % (client_address.decode(), req_alias, req_address, req_device.get_config())

                #   process a status request
                if req_msg_val == "STATUS":
                    rep_status = req_device.get_status()
                    reply_string = "Processed Request from %s. Status of %s at address %s is: %s." % (client_address.decode(), req_alias, req_address, rep_status)

                #   process a read request
                if req_msg_val == "READ":
                    rep_value = req_device.get_data()
                    reply_string = "Processed Request from %s. Value of %s at address %s is: %s." % (client_address.decode(), req_alias, req_address, rep_value)

                #   configure a ipcMessage
                reply_message.set_param("REPLY", reply_string)

                #   Encode the message for sending
                reply_message = reply_message.encode()

                #   check if its unicode, if so covert to bytes
                if isinstance(reply_message, unicode):
                    reply_message = cast_bytes(reply_message)

                #   send a multipart back to the client 
                self.socket.send_multipart([client_address, b"", reply_message,])
                
            #   Catch IPCMessage Exception
            except IpcMessageException as err:
                print("IPC MESSAGE Error Found %s: " % str(err))

def main(): 

    server = ipc_server()

    #   configure hardware addresses and alias look up tables
    server.assign_addresses()
    server.make_lookup()
    print("Hardware device address tree:") 
    print(server.lookup)

    #   bind the socket and run reply loop
    server.bind()
    server.run_rep()

if __name__ == "__main__":
    main()
