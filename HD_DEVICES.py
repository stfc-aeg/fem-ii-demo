from random import randint
import random
import time
import Adafruit_BBIO.GPIO as BBGPIO
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.MCP230xx as MCP


class HdDevice:
    """ Represents a generic hardware device """

    def __init__(self, status, address, alias):
        """ Superclass constructor

        :param status: on/off status of the device
        :param address: bus address of the device
        :param alias: descriptive name of the device for user interaction

        """
        self.status = status
        self.addr = address
        self.alias = alias

    def get_status(self, alias=None):
        return self.status
    
    def get_addr(self, alias=None):
        return self.addr
    
    def set_status(self, status, alias=None):
        self.status = status
    
    def set_addr(self, addr, alias=None):
        self.addr = addr
 
    def get_alias(self, alias=None):
        return self.alias

    #   MUST BE OVERRIDEN 
    def get_data(self, alias=None):
        pass

    def get_config(self, alias=None):
        pass

    def set_config(self, config, alias=None):
        pass

    def run_process(self, process, alias=None):
        pass


class HdMcp230xx(HdDevice):
    """ Subclass, extends HD_DEVICE

    Represents an MCP I/0 Expander
    Overrides get_data, get_config and set_config
    
    :param model: the MCP model type
    :param busnum: the i2c busnumber for the device

    """
    def __init__(
        self, status="Connected", address=0x20, alias="MCP",
        model="MCP23008", busnum=2
    ):
        """ Subclass constructor """
        HdDevice.__init__(self, status, address, alias)

        self.model = model
        self.busnum = busnum

        if self.model == "MCP23008":
            self.mcp = MCP.MCP23008(self.addr, busnum=self.busnum)
        elif self.model == "MCP23017":
            self.mcp = MCP.MCP23017(self.addr, busnum=self.busnum)

        self.pins = [0, 1, 2]
        self.devices = []

    def setup_outputs(self):
        """ Set up all pins as outputs """
        
        for pin in self.pins:
            self.mcp.setup(pin, GPIO.OUT)
 
    #   MUST BE OVERRIDEN - Currently not implemented due to no requirement
    def get_data(self, alias=None):
        pass
        """
        output = ""
        for device in self.devices:
            output += "Device %s : %s.\n" % (
                device.get_alias(), device.get_data()
            )

        return output
        """
    def get_config(self, alias="LED_RED"):
        pass
        """
        output = ""
        for device in self.devices: 
            if device.get_alias() == alias:
                output += "Device %s : %s.\n" % (
                    device.get_alias(), device.get_config()
                )

        return output
        """
        
    def set_config(self, config, alias="LED_RED"):
        pass
        """
        for device in self.devices: 
            if device.get_alias == alias:
                device.set_config(config)
                
        """

    def run_process(self, process, timeout=None, rate=None, alias="LED_RED"):
        pass
        """
        for device in self.devices: 
            if device.get_alias == alias:
                if device.process_status[process] == False:
                    device.run_process(process, timeout, rate)
        """

    def process_running(self, process, alias="LED_RED"):
        pass
        """
        for device in self.devices:
            if device.get_alias() == alias:
               return device.process_status[process]
        """


class HdLed(HdDevice):
    """ Subclass, extends HD_DEVICE

    Represents a simple LED hardware device
    Overrides get_data, get_config and set_config
    :param pin: the pin number for the LED
    :param mode: Mode of communication (GPIO or via an MCP)
    :param _mcp: MCP object if the LED is attached to an MCP
    
    """
    def __init__(
        self, status="OFF", address="0X01", alias="LED", pin="P8_10",
        mode="GPIO", _mcp=None
    ):
        """ Subclass constructor """
        
        HdDevice.__init__(self, status, address, alias)
        self.pin = pin
        self.mode = mode
        if _mcp is not None:
            self.mcp = _mcp
        elif mode == "GPIO":
            BBGPIO.setup(self.pin, BBGPIO.OUT)

        self.KEEP_BLINKING = False
        self.process_status = {"BLINK": False}
    

    # @ovveride
    def get_data(self, alias=None):
        """ Returns the status of the LED
         
        As LED has no data, returns the status
        i.e ON/OFF
        """    
        return self.status

    # @ovveride    
    def get_config(self, alias=None):
        """ Returns the status of the LED

        As LED has no specific configuration 
        the status i.e ON/OFF is returned
        """

        return self.status

    # @ovveride
    def set_config(self, config, alias=None):
        """ Sets the status of the LED
        
        :param config: ON/OFF status of the LED
        :param alias: Alias Name of the LED
        As the LED has no configuration, 
        sets the status i.e ON/OFF
        """
        self.status = config
        if config == "ON":
            if self.mode == "MCP":
                self.mcp.output(self.pin, 1)
            else:
                BBGPIO.output(self.pin, BBGPIO.HIGH)
        elif config == "OFF":
            if self.mode == "MCP":
                self.mcp.output(self.pin, 0)
            else:
                BBGPIO.output(self.pin, BBGPIO.LOW)
        
    def stop_process(self, process, alias=None):
        """ Stops the current process

        :param process: the process to be stopped
        :param alias: the alias of the device

        Sets the process_status for the given process as False
        """
        self.process_status[process] = False
        if process == "BLINK":
            self.KEEP_BLINKING = False
        
    def run_process(self, process, timeout=None, rate=1, alias=None):
        """ Starts the current process

        :param process: the process to be stopped
        :param timeout: The timeout for the process i.e when to stop automatically
        :param rate: The rate to perform the process, if it is a periodic process.
        :param alias: the alias of the device
        
        returns the status of the method call (True for success, False for fail)
        Sets the process_status for the given process as True.
        Calls the appropriate method and sets the status as OFF once complete
        """
        self.process_status[process] = True
        if process == "BLINK":
            status = self.blink(timeout, rate)
            self.status = "OFF"
        return status

    def turn_on(self):
        """ Turns ON the LED in either GPIO or MCP mode, sets the status to ON """

        if self.mode == "MCP":
            self.mcp.output(self.pin, 1)
        else:
            BBGPIO.output(self.pin, BBGPIO.HIGH)
        self.status = "ON"

    def turn_off(self):
        """ Turns OFF the LED in either GPIO or MCP mode, sets the status to OFF"""

        if self.mode == "MCP":
            self.mcp.output(self.pin, 0)
        else:
            BBGPIO.output(self.pin, BBGPIO.LOW)
        self.status = "OFF"

    def blink(self, timeout, rate):
        """ Blinking procedure for the LED
        :param timeout: the timeout for the blinking, if none - infinite
        :param rate: the rate at which to blink, if none - random

        Sets the process_status for BLINK to False
        And turns off the LED on completion to ensure no 'hanging' LED's.abs

        Returns true if the method completes without errors, false if ValueError.
        """
        try:
            if rate is None:
                rate = random.uniform(0.05, 1.0)
            if timeout is None:
                self.KEEP_BLINKING = True
                while self.KEEP_BLINKING:
                    self.turn_on()
                    time.sleep(float(rate))
                    self.turn_off()
                    time.sleep(float(rate))

            else:
                start = time.time()
                end = start + float(timeout)
                while time.time() < end:
                    self.turn_on()
                    time.sleep(float(rate))
                    self.turn_off()
                    time.sleep(float(rate))
            
            self.process_status["BLINK"] = False
            self.turn_off()
            return True
        except ValueError:
            return False

    def process_running(self, process, alias=None):
        """ Helper method to check the status of a process 
        :param process: the process to be checked
        :param alias: the name of the device

        """
        return self.process_status[process]


class HdTemp(HdDevice):
    """ Subclass, extends HD_DEVICE

    Represents a simple Temperature sensing hardware device
    Overrides get_data, get_config and set_config
    :param temp: current temperature reading
    :param fc: degrees configuration, F = Farenheit, C = Celcius
    
    """
    def __init__(
        self, status="OFF", address="0X02",
        temp=randint(-100, 200), fc="C",
        alias="TEMP"
    ):
        """ Subclass constructor """

        HdDevice.__init__(self, status, address, alias)
        self.temp = temp
        self.fc = fc

    # @ovveride
    def get_data(self, alias=None):
        """ Returns the current temperature reading
        
        Reading is provided in relation to degrees
        configuration.
        """

        self.temp = randint(-100, 200)  # Fake a new temperature reading

        if self.fc == "F":
            return str((self.temp * 1.8) + 32) + self.fc
        else:
            return str(self.temp) + " " + self.fc

    # @ovveride
    def set_config(self, fc, alias=None):
        """ Sets the degree configuration
        
        :param fc: Farenheit or Celcius config option
        """
        self.fc = fc   

    # @ovveride
    def get_config(self, alias=None):
        """ Returns the current degrees configuration"""

        return self.fc


class HdPower(HdDevice):
    """ Subclass, extends HD_DEVICE

    Represents a simple Power control hardware device
    Overrides get_data, get_config and set_config
    :param volts: current voltage reading
    
    """
    def __init__(
        self, status="OFF", address="0X03", 
        volts="5", config="5", alias="POWER"
    ):
        """ Subclass constructor """

        HdDevice.__init__(self, status, address, alias)
        self.volts = volts
        self.config = config

    # @ovveride
    def get_data(self, alias=None):
        """ Returns the current voltage """

        # Read a fake voltage reading around the current voltage config
        volts1 = float(self.config) - 0.2
        volts2 = float(self.config) + 0.2
        fake_volts = random.uniform(volts1, volts2)
        return str(fake_volts) + "V"

    # @ovveride
    def set_config(self, config, alias=None):
        """ Set the voltage to 3.3 or 5
        
        :param config: voltage setting, 3.3 or 5volts
        """
        self.config = config

    # @ovveride
    def get_config(self, alias=None):
        """ Return the voltage configuration"""

        return self.config + "V"
