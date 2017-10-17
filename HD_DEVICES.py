from random import randint
import random

#   Superclass for a hardware device
class HD_DEVICE:

    def __init__(self, status, address, alias):
        
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

#   subclass representing an LED
class HD_LED(HD_DEVICE):

    def __init__(self, status="OFF", address="0X01", alias="LED"):
        HD_DEVICE.__init__(self, status, address, alias)

    #   LED has no data, return status
    def get_data(self):
        return self.status

    #   LED has no config, return status
    def get_config(self):
        return self.status

    #   CONFIG == STATUS
    def set_config(self, config):
        self.status = config

#   subclass representing a temperature sensor
class HD_TEMP(HD_DEVICE):

    def __init__(self, status="OFF", address="0X02", temp = randint(-100, 200), fc = "C", alias="TEMP"):
        HD_DEVICE.__init__(self, status, address, alias)
        self.temp = temp
        self.fc = fc

    #   override to return a fake temperature reading
    def get_data(self):

        #   Fake a new temperature reading
        self.temp = randint(-100, 200)

        if self.fc == "F":
            return str((self.temp * 1.8) + 32) + self.fc
        else:
            return str(self.temp) + " " + self.fc

    #   Override to set the Farenheit/Celcius parameter
    def set_config(self, fc):
        self.fc = fc   

    #   Override to return the F/C config
    def get_config(self):
        return self.fc

#   subclass representing some sort of power/voltage controller
class HD_POWER(HD_DEVICE):

    def __init__(self, status="OFF", address="0X03", volts="5", config="5", alias="POWER"):
        HD_DEVICE.__init__(self, status, address, alias)
        self.volts = volts
        self.config = config

    #   Override to return the current voltage
    def get_data(self):

        #   Read a fake voltage reading around the current voltage config
        volts1 = float(self.config) - 0.2
        volts2 = float(self.config) + 0.2
        fake_volts = random.uniform(volts1, volts2)
        return str(fake_volts) + "V"

    #   override to set the voltage configuration to 5 or 3.3 volts
    def set_config(self, config):
        self.config = config

    #   Override to return the configuration
    def get_config(self):
        return self.config + "V"