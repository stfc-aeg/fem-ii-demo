from random import randint
import random


class HD_DEVICE:
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


class HD_LED(HD_DEVICE):
    """ Subclass, extends HD_DEVICE

    Represents a simple LED hardware device
    Overrides get_data, get_config and set_config
    
    """
    def __init__(self, status="OFF", 
                address="0X01", alias="LED"):
        """ Subclass constructor """
        
        HD_DEVICE.__init__(self, status, address, alias)

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


class HD_TEMP(HD_DEVICE):
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

        HD_DEVICE.__init__(self, status, address, alias)
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


class HD_POWER(HD_DEVICE):
    """ Subclass, extends HD_DEVICE

    Represents a simple Power control hardware device
    Overrides get_data, get_config and set_config
    :param volts: current voltage reading
    
    """
    def __init__(self, status="OFF", address="0X03", 
                volts="5", config="5", alias="POWER"):
        """ Subclass constructor """

        HD_DEVICE.__init__(self, status, address, alias)
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