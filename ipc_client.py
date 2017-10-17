import zmq
from odin_data.ipc_message import IpcMessage
from random import randint
from zmq.utils.strtypes import unicode, cast_bytes

#   Fixed config options for quick validating of user input
msg_types = {"CMD"}
msg_vals = {"STATUS", "CONFIG", "READ"}
hd_devices = { "LED", "TEMP", "POWER"}
LED_STATES = { "ON", "OFF"}
TEMP_STATES = { "C", "F"}
VOLT_STATES = { "5", "3.3"}

class ipc_client:

    def __init__(self):

        ident= str(randint(0, 100000000))
        self.identity = "Client %s" % ident
        self.url = "tcp://localhost:5556"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, self.identity.encode())

    def connect(self):

        self.socket.connect(self.url)

    #   sends a request, waits for a reply and returns response
    def run_req(self):
        
        while True:

            #   Get and validate service request from the user
            print("---------------------------------")

            #   Validate msg_type (CMD)
            msg_type = input("Message Type: " + "\n")
            while msg_type not in msg_types:
                msg_type = input("No such type.\nMessage Type: " + "\n")
            
            #   Validate msg_val (READ/CONFIG/STATUS)
            msg_val = input("Message Value: " + "\n")
            while msg_val not in msg_vals:
                msg_val = input("No such value.\nMessage Value: " + "\n")

            #   Form the IPCMessage request
            request = IpcMessage(msg_type, msg_val)

            #   Get the alias of the request hardware device
            msg_device = input("Device: " + "\n")
            while msg_device not in hd_devices:
                msg_device= input("No such device registered.\nDevice: " + "\n")

            #   set the device parameter
            request.set_param("DEVICE", msg_device)

            #   Hard coded configuration processing for the different device options 
            if msg_val == "CONFIG":
                if msg_device == "LED":
                    msg_config = input("LED STATE:" + "\n")
                    while msg_config not in LED_STATES:
                        msg_config = input("ON or OFF are the only LED configurations.\nLED STATE: \n")
                

                if msg_device == "TEMP":
                    msg_config = input("F/C:" + "\n")
                    while msg_config not in TEMP_STATES:
                        msg_config = input("F/C are the only temperature configurations.\nF/C: \n")


                if msg_device == "POWER":
                    msg_config = input("VOLTAGE:" + "\n")
                    while msg_config not in VOLT_STATES:
                        msg_config = input("5 and 3.3 are the only voltage configurations.\nVOLTAGE: \n")

                #   set the configuration parameter
                request.set_param("CONFIG", msg_config)

            print("%s Configuring service request..." % self.identity)

            #   Encode the message to be sent
            request = request.encode()

            if isinstance(request, unicode):
                request = cast_bytes(request)

            #   send multipart message address is automatically added it seems
            self.socket.send_multipart([b"", request,])
            
            #   Wait for the IPC message response and notify end-user
            #   strip off the first part, get the reply
            r_address, reply = self.socket.recv_multipart()

            #   format it as an IPC message
            reply = IpcMessage(from_str=reply)

            
            #reply = IpcMessage(from_str=self.socket.recv())
            print("Received Response: %s" % reply.get_param("REPLY"))

def main():

    
    client = ipc_client()
    client.connect()
    client.run_req()

if __name__ == "__main__":
    main()