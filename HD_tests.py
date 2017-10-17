from HD_DEVICES import HD_LED, HD_VOLTS, HD_TEMP

def main():

    led = HD_LED()
    volts = HD_VOLTS()
    temp = HD_TEMP()

    print("LED: " + led.get_addr() + " " + led.get_status())
    print("VOLTS: " + volts.get_addr() + " " + volts.get_status() + " " + volts.get_volts())
    print("TEMP: " + temp.get_addr() + " " + temp.get_status() + " " + temp.get_temp())

    volts.set_volts("3.3")
    print(volts.get_volts())
    
if __name__ == "__main__":
    main()