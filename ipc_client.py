'''
    Client. 
    Communicates with a single ipc_server
    Uses Ipc Message formatting
    
'''
import sys
from random import randint
import zmq
import argparse
from odin_data.ipc_message import IpcMessage
from zmq.utils.strtypes import unicode, cast_bytes

#   Fixed config options for quick validating of user input
MSG_TYPES = {"CMD"}
MSG_VALS = {"STATUS", "CONFIG", "READ"}
HD_DEVICES = {"LED", "TEMP", "POWER"}
LED_STATES = {"ON", "OFF"}
TEMP_STATES = {"C", "F"}
VOLT_STATES = {"5", "3.3"}

class IpcClient:


    def __init__(self, url, port):
        ident= str(randint(0,100000))
        self.identity = "Client %s" % ident
        self.url = "%s:%s" % (url, port)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, self.identity.encode())
        
    def connect(self):
        """ Connect the socket """
        self.socket.connect(self.url)

    def recv_reply(self):
        """ Receive reply from ZMQ socket
            
        Receives a multipart message, forms an IPCmessage 
        and prints out the REPLY string 
        
        """
        # Strip off the address
        r_address, reply = self.socket.recv_multipart()

        # format it as an IPC message
        reply = IpcMessage(from_str=reply)
        print("Received Response: %s" % reply.get_param("REPLY"))

    def form_ipc_msg(self, msgType, msgVal, msgDevice, msgConfig):
        """ Forms and returns an encoded IPC Message
        
        :param msgtype: The type of message i.e CMD
        :param msgVal: The value of the request i.e STATUS/CONFIG
        :param msgDevice: The device alias name
        :param msgConfig: The configuration parameter
        Returns the encoded ipc message for sending over zmq socket
        
        """
        request = IpcMessage(msgType, msgVal)
        request.set_param("DEVICE", msgDevice)

        if msgVal == "CONFIG":
            request.set_param("CONFIG", msgConfig)

        print("%s Configuring service request..." % self.identity)

        #   Encode the message to be sent
        request = request.encode()
        if isinstance(request, unicode):
            request = cast_bytes(request)

        return request

    def run_req(self, run_once, msgType, msgVal, msgDevice, msgConfig):
        """ Req-Reply loop, sends request, waits for response
        
        :param run_once: Boolean value, true when command line arguments were 
                        provided at runtime
                        REQ-REP loop will run once if true.
        :param msgType: THe type of message 
        :param msgVal: The message value i.e STATUS/CONFIG
        :param msgDevice: The alias of the target hardware device
        :param msgConfig: The configuration parameter, None if not provided.
        
        """

        if run_once == True:
            request = self.form_ipc_msg(msgType, msgVal, msgDevice, msgConfig)
            self.socket.send(request)
            self.recv_reply()

        else:
            #Infinite loop of retrieving user input and running REQ-REP
            while True:
                
                print("---------------------------------")

                # Validate msg_type (CMD)
                msg_type = input("Message Type: " + "\n")
                while msg_type not in MSG_TYPES:
                    msg_type = input("No such type.\nMessage Type: " + "\n")
                
                # Validate msg_val (READ/CONFIG/STATUS)
                msg_val = input("Message Value: " + "\n")
                while msg_val not in MSG_VALS:
                    msg_val = input("No such value.\nMessage Value: " + "\n")

                #   Get the alias of the request hardware device
                msg_device = input("Device: " + "\n")
                while msg_device not in HD_DEVICES:
                    msg_device= input("No such device registered.\n \
                                        Device: " + "\n")

                # Initialise config to none incase its a STATUS or READ message
                msg_config = None

                # Hard coded configuration processing for different device options 
                if msg_val == "CONFIG":
                    if msg_device == "LED":
                        msg_config = input("LED STATE:" + "\n")
                        while msg_config not in LED_STATES:
                            msg_config = input("ON or OFF are the only LED \
                                                configurations.\nLED STATE: \n")
                    
                    if msg_device == "TEMP":
                        msg_config = input("F/C:" + "\n")
                        while msg_config not in TEMP_STATES:
                            msg_config = input("F/C are the only temperature \
                                                configurations.\nF/C: \n")

                    if msg_device == "POWER":
                        msg_config = input("VOLTAGE:" + "\n")
                        while msg_config not in VOLT_STATES:
                            msg_config = input("5 and 3.3 are the only voltage \
                                                configurations.\nVOLTAGE: \n")

                request = self.form_ipc_msg(msg_type, msg_val, 
                                            msg_device, msg_config)
                self.socket.send(request)
                self.recv_reply()


def main():

    """ 
        Define arguments for a one-shot client request 
        (URL, PORT, TYPE, VAL, DEVICE, CONFIG)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-url", "--url", help="Remote server url, \
                        default = tcp://localhost", default="tcp://localhost")
    parser.add_argument("-port", "--port", help="Port connection, default = 5555", 
                        default="5555")
    parser.add_argument("-msg_type", "--msg_type", help="Message type, accepts: %s" 
                        % MSG_TYPES, choices=MSG_TYPES)
    parser.add_argument("-msg_val", "--msg_val", help="Message val, accepts: %s " 
                        % MSG_VALS, choices=MSG_VALS)
    parser.add_argument("-device", "--device", help="Target device, accepts: %s " 
                        % HD_DEVICES, choices=HD_DEVICES)
    parser.add_argument("-led_config", "--led_config", 
                        help="LED device configuration option, accepts: %s " 
                        % LED_STATES, choices=LED_STATES)
    parser.add_argument("-temp_config", "--temp_config", 
                        help="Temperature device configuration option, accepts: %s " 
                        % TEMP_STATES, choices=TEMP_STATES)
    parser.add_argument("-power_config", "--power_config", 
                        help="Power device configuration option, accepts: %s " 
                        % VOLT_STATES, choices=VOLT_STATES)
    args = parser.parse_args()

    # Ensure that the config options are given for config messages + right devices
    if (args.msg_val == "CONFIG" and args.device == "LED" 
        and args.led_config == None):
        parser.error("--msg_val of CONFIG and --device of LED requires \
                    --led_config to be specified.")
    if (args.msg_val == "CONFIG" and args.device == "POWER" 
        and args.power_config == None):
        parser.error("--msg_val of CONFIG and --device of POWER requires \
                    --power_config to be specified.")
    if (args.msg_val == "CONFIG" and args.device == "TEMP" 
        and args.temp_config == None):
        parser.error("--msg_val of CONFIG and --device of TEMP requires \
                    --temp_config to be specified.")

    """ 
        Ensure no command line configuration arguments are 
        given to status or read messages
    """
    if ((args.msg_val == "STATUS" or args.msg_val == "READ") 
        and (args.led_config != None or args.power_config != None 
        or args.temp_config != None)):
        parser.error("--msg_val of STATUS or READ cannot take _config arguments.")

    """ 
        Ensure a full CMD message has been provided 
        or none at all - count the non none arguments
    """
    arg_length = 0
    for arg in vars(args):
        if getattr(args, arg) != None:
            arg_length += 1
        print (arg, getattr(args, arg))
    print (arg_length)

    """
        If we have more than just the url and the port
        but less than url, port, type, val and device throw an error
    """
    if arg_length > 2 and arg_length < 5:
        parser.error("A full client request is required or none at all. \
                    Message consists of a msg_type, msg_val, a target device \
                    and optional configuration arguments if msg_val == config.")
    else:
        # A proper message has been provided, run_once is true
        run_once = True
        if arg_length == 2:
            run_once = False
        client = IpcClient(args.url, args.port)
        client.connect()

        # Assign the config argument depending on the device given
        if args.device == "LED":
            _config = args.led_config
        elif args.device == "TEMP":
            _config = args.temp_config
        else:
            _config = args.power_config
        client.run_req(run_once, args.msg_type, 
                        args.msg_val, args.device, 
                        _config)

if __name__ == "__main__":
    main()