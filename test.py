   #   Override to return the current voltage
import random

def main():

    volts1 = int("5") - 0.5
    volts2 = int("5") + 0.5
    fake_volts = random.uniform(volts1, volts2)
    return str(fake_volts) + "V"

if __name__ == "__main__":
    print main()