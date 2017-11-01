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
MSG_VALS = {"STATUS", "CONFIG", "READ", "PROCESS"}
HD_DEVICES = {"LED", "TEMP", "POWER"}
LED_STATES = {"ON", "OFF"}
PROCESSES = {"LED":"BLINK"}
TEMP_STATES = {"C", "F"}
VOLT_STATES = {"5", "3.3"}

DEF_BLINK_RATE = "1"
DEF_BLINK_TIMEO = "10"
DEF_POWER_CONFIG = "5"
DEF_LED_CONFIG = "ON"
DEF_TEMP_CONFIG = "C"
DEF_URL = "tcp://localhost"
DEF_PORT = "5555"

class IpcClient:


    def __init__(self, url, port):
        ident= str(randint(0,100000))
        self.identity = "Client %s" % ident
        self.tcp = url
        self.url = "%s:%s" % (url, port)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, self.identity.encode())
        
        self.subscribe = self.context.socket(zmq.SUB)
        self.WAIT_FOR_ACK = False

    def connect(self):
        """ Connect the socket """
        self.socket.connect(self.url)

        self.subscribe.connect("%s:5556" % self.tcp)
        self.subscribe.setsockopt_string(zmq.SUBSCRIBE, self.identity)

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

    def recv_ack(self):

        ack = self.subscribe.recv_string()
        print("Received Response: %s" % ack)

    def form_ipc_msg(self, msgType, msgVal, msgDevice, msgConfig, msgProcess, options={}):
        """ Forms and returns an encoded IPC Message
        
        :param msgtype: The type of message i.e CMD
        :param msgVal: The value of the request i.e STATUS/CONFIG/PROCESS
        :param msgDevice: The device alias name
        :param msgConfig: The configuration parameter
        Returns the encoded ipc message for sending over zmq socket
        
        """
        request = IpcMessage(msgType, msgVal)
        request.set_param("DEVICE", msgDevice)

        if msgVal == "CONFIG":
            request.set_param("CONFIG", msgConfig)
        
        if msgVal == "PROCESS":
            request.set_param("PROCESS", msgProcess)
            self.WAIT_FOR_ACK = True

            if msgProcess == "BLINK":
                request.set_param("TIMEOUT", options["blink_timeout"])
                request.set_param("RATE", options["blink_rate"])

        print("%s Configuring service request..." % self.identity)

        #   Encode the message to be sent
        request = request.encode()
        if isinstance(request, unicode):
            request = cast_bytes(request)

        return request

    def isDigit(self, value):
        """ Checks whether value is a digit """
        
        try:
            float(value)
            return True
        except ValueError:
            return False

    def run_req(self, run_once, msgType, msgVal, msgDevice, msgConfig, msgProcess, options={}):

        
        """ Req-Reply loop, sends request, waits for response
        
        :param run_once: Boolean value, true when command line arguments were 
                        provided at runtime
                        REQ-REP loop will run once if true.
        :param msgType: THe type of message 
        :param msgVal: The message value i.e STATUS/CONFIG
        :param msgDevice: The alias of the target hardware device
        :param msgConfig: The configuration to be applied, None if not provided.
        :param msgProcess: The process to be performed
        :param options: Dictionary holding configuration or process options.
        
        """
        self.WAIT_FOR_ACK = False
        
        if run_once == True:
            request = self.form_ipc_msg(msgType, msgVal, msgDevice, msgConfig, msgProcess, options)
            self.socket.send(request)
            if self.WAIT_FOR_ACK:
                self.recv_ack()
            self.recv_reply()

        else:
            #Infinite loop of retrieving user input and running REQ-REP
            while True:
                
                self.WAIT_FOR_ACK = False

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
                msg_process = None
                blink_timeout = None
                blink_rate = None

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
                elif msg_val == "PROCESS":
                    msg_process = input("PROCESS :" + "\n")
                    while msg_process not in PROCESSES[msg_device]:
                        msg_process = input("No such process for the device. PROCESS:" + "\n")
                    
                    if msg_process == "BLINK":
                        blink_timeout = input("BLINK TIMEOUT (in seconds):" + "\n")
                        while self.isDigit(blink_timeout) == False:
                            blink_timeout = input("Must be a number, BLINK TIMEOUT (in seconds):" + "\n")
                        options["blink_timeout"] = blink_timeout

                        blink_rate = input("BLINK RATE (in seconds):" + "\n")
                        while self.isDigit(blink_rate) == False:
                            blink_rate = input("Must be a number, BLINK RATE(in seconds):" + "\n")
                        options["blink_rate"] = blink_rate

                request = self.form_ipc_msg(msg_type, msg_val, 
                                            msg_device, msg_config, msg_process, options)
                self.socket.send(request)

                if self.WAIT_FOR_ACK:
                    self.recv_ack()
                self.recv_reply()


def main():

    options = {}

    """ 
        Define arguments for a one-shot client request 
        (URL, PORT, TYPE, VAL, DEVICE, CONFIG, OPTIONS)
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-url", "--url", help="Remote server url, \
                        default = tcp://localhost", default="tcp://localhost")
    parser.add_argument("-port", "--port", help="Port connection, default = 5555", 
                        default=None)
    parser.add_argument("-msg_type", "--msg_type", help="Message type, accepts: %s" 
                        % MSG_TYPES, choices=MSG_TYPES)
    parser.add_argument("-msg_val", "--msg_val", help="Message val, accepts: %s " 
                        % MSG_VALS, choices=MSG_VALS)
    parser.add_argument("-device", "--device", help="Target device, accepts: %s " 
                        % HD_DEVICES, choices=HD_DEVICES)
    parser.add_argument("-process", "--process", help="Process to be performed, accepts: %s." 
                        % PROCESSES, choices=[value for key, value in PROCESSES.items()], default=None)
    parser.add_argument("-led_config", "--led_config", 
                        help="LED device configuration option, accepts: %s. Default = ON" 
                        % LED_STATES, choices=LED_STATES, default=None)
    parser.add_argument("-temp_config", "--temp_config", 
                        help="Temperature device configuration option, accepts: %s. Default = c" 
                        % TEMP_STATES, choices=TEMP_STATES, default=None)
    parser.add_argument("-power_config", "--power_config", 
                        help="Power device configuration option, accepts: %s. Default = 5V" 
                        % VOLT_STATES, choices=VOLT_STATES, default=None)
    parser.add_argument("-b_timeout", "--b_timeout", 
                        help="Timeout for BLINK call, must be in seconds. Default = 10", 
                        type=float, default=None)
    parser.add_argument("-b_rate", "--b_rate", 
                        help="Blink rate for BLINK call, must be in seconds. Default = 1",
                        type=float, default=None)                 
    args = parser.parse_args()


    arg_length = len([x for x in vars(args) if getattr(args, x) is not None])

    RUN_ONCE = None

    args_config = None
    if args.url == None:
        args.url = DEF_URL
    if args.port == None:
        args.port = DEF_PORT

    print(args.url) 
    print(args.port)
    client = IpcClient(args.url, args.port)
    client.connect()

    print(arg_length)

    if arg_length < 3:
        RUN_ONCE = False

    else: 
        #   minimum combination of parameters required for command
        req_command_args = [args.device, args.msg_type, args.msg_val]
        req_length = len([x for x in req_command_args if x is not None])
        if req_length in range(1, 3):
            parser.error("Invalid command message. Requires msg_type, msg_val and msg_device to be defined")
   
        elif args.msg_val == "PROCESS" and args.process == None:
            parser.error("Process requested but no process selected")

        else:
            args.temp_config = DEF_TEMP_CONFIG
            args.power_config = DEF_POWER_CONFIG
            args.led_config = DEF_LED_CONFIG
            args.b_rate = DEF_BLINK_RATE
            args.b_timeout = DEF_BLINK_TIMEO

            RUN_ONCE = True

            if args.device == "LED":
                args_config = args.led_config
            elif args.device == "TEMP":
                args_config = args.temp_config
            else:
                args_config = args.power_config

            if args.msg_val == "PROCESS" and args.process != None:
                if args.process == "BLINK":
                    options["blink_timeout"] = args.b_timeout
                    options["blink_rate"] = args.b_rate

    """
    arg_length = 0
    for arg in vars(args):
        if getattr(args, arg) != None:
            arg_length += 1
        print (arg, getattr(args, arg))
    print (arg_length)

    
    else:
        # A proper message has been provided, run_once is true
        run_once = True
        if arg_length == 2 and args.url != None and args.port != None:
            run_once = False
   
        client = IpcClient(args.url, args.port)
        client.connect()

        # Assign the config argument depending on the device given
        b_timeout = None
        b_rate = None
        if args.device == "LED":
            _config = args.led_config
            if _config == "BLINK":
                options["blink_timeout"] = args.b_timeout
                options["blink_rate"] = args.b_rate
        elif args.device == "TEMP":
            _config = args.temp_config
        else:
            _config = args.power_config
        
    """
    print(RUN_ONCE)
    client.run_req(RUN_ONCE, args.msg_type, 
                        args.msg_val, args.device, 
                        args_config, args.process, options)
    

if __name__ == "__main__":
    main()
