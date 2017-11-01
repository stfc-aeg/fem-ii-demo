from random import randint
import random
import time
import Adafruit_BBIO.GPIO as GPIO

class HdDevice:
    """ Represents a generic hardware device """

    def __init__(self, status, 
                address, alias):
        """ Superclass constructor

        :param status: on/off status of the device
        :param address: bus address of the device
        :param alias: descriptive name of the device for user interaction

        """
        self.status = status
        self.addr = address
        self.alias = alias

    def get_status(self):
        return self.status
    
    def get_addr(self):
        return self.addr
    
    def set_status(self, status):
        self.status = status
    
    def set_addr(self, addr):
        self.addr = addr
 
    def get_alias(self):
        return self.alias

    #   MUST BE OVERRIDEN 
    def get_data(self):
        pass

    def get_config(self):
        pass

    def set_config(self, config):
        pass

    def run_process(self, process):
        pass

class HdLed(HdDevice):
    """ Subclass, extends HD_DEVICE

    Represents a simple LED hardware device
    Overrides get_data, get_config and set_config
    
    """
    def __init__(self, status="OFF", 
                address="0X01", alias="LED", pin="P8_10"):
        """ Subclass constructor """
        
        HdDevice.__init__(self, status, address, alias)
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.KEEP_BLINKING = False
        self.process_running = False

    # @ovveride
    def get_data(self):
        """ Returns the status of the LED
         
        As LED has no data, returns the status
        i.e ON/OFF
        """    
        return self.status

    # @ovveride    
    def get_config(self):
        """ Returns the status of the LED

        As LED has no specific configuration 
        the status i.e ON/OFF is returned
        """

        return self.status

   # @ovveride
    def set_config(self, config):
        """ Sets the status of the LED
        
        :param config: ON/OFF status of the LED
        As the LED has no configuration, 
        sets the status i.e ON/OFF
        """
        self.status = config
        if config == "ON":
            GPIO.output(self.pin, GPIO.HIGH)
        elif config == "OFF":
            GPIO.output(self.pin, GPIO.LOW)
        
    def stop_process(self, process):

        if process == "BLINK":
            self.KEEP_BLINKING = False
            
    def run_process(self, process, timeout=None, rate=1):
        self.process_running = True

        if process == "BLINK":
            if timeout == None:
                self.KEEP_BLINKING == True
            status = self.blink(timeout,rate)
            self.status = "OFF"
        return status

    def turn_on(self):
        GPIO.output(self.pin, GPIO.HIGH)
        self.status = "ON"

    def turn_off(self):
        GPIO.output(self.pin, GPIO.LOW)
        self.status = "OFF"

    def blink(self, timeout, rate):
        try:
            if timeout == None:
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

            self.status = "OFF"
            self.process_running = False
            return True
        except ValueError:
            return False

class HdTemp(HdDevice):
    """ Subclass, extends HD_DEVICE

    Represents a simple Temperature sensing hardware device
    Overrides get_data, get_config and set_config
    :param temp: current temperature reading
    :param fc: degrees configuration, F = Farenheit, C = Celcius
    
    """
    def __init__(self, status="OFF", address="0X02", 
                temp=randint(-100, 200), fc="C", 
                alias="TEMP"):
        """ Subclass constructor """

        HdDevice.__init__(self, status, address, alias)
        self.temp = temp
        self.fc = fc

    # @ovveride
    def get_data(self):
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
    def set_config(self, fc):
        """ Sets the degree configuration
        
        :param fc: Farenheit or Celcius config option
        """
        self.fc = fc   

    # @ovveride
    def get_config(self):
        """ Returns the current degrees configuration"""

        return self.fc


class HdPower(HdDevice):
    """ Subclass, extends HD_DEVICE

    Represents a simple Power control hardware device
    Overrides get_data, get_config and set_config
    :param volts: current voltage reading
    
    """
    def __init__(self, status="OFF", address="0X03", 
                volts="5", config="5", alias="POWER"):
        """ Subclass constructor """

        HdDevice.__init__(self, status, address, alias)
        self.volts = volts
        self.config = config

    # @ovveride
    def get_data(self):
        """ Returns the current voltage """

        #Read a fake voltage reading around the current voltage config
        volts1 = float(self.config) - 0.2
        volts2 = float(self.config) + 0.2
        fake_volts = random.uniform(volts1, volts2)
        return str(fake_volts) + "V"

    # @ovveride
    def set_config(self, config):
        """ Set the voltage to 3.3 or 5
        
        :param config: voltage setting, 3.3 or 5volts
        """
        self.config = config

    # @ovveride
    def get_config(self):
        """ Return the voltage configuration"""

        return self.config + "V"
