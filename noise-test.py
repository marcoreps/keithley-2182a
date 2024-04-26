import pyvisa,time,csv
from pyvisa.constants import StopBits, Parity
from datetime import datetime
rm = pyvisa.ResourceManager()


batchsize = 200


my_instrument = rm.open_resource('ASRL/dev/ttyUSB0::INSTR',baud_rate=19200, data_bits=8,write_termination='\r',read_termination='\r',parity=Parity.none)
my_instrument.timeout = 20000
my_instrument.write("*RST")
print(my_instrument.query("*IDN?"))
my_instrument.write("*CLS")

my_instrument.write(":syst:pres")
time.sleep(2)

my_instrument.write(":sens:volt:ref:acq")
my_instrument.query("*OPC?")

my_instrument.write(":sens:volt:ref:stat on")

my_instrument.write("INIT:CONT OFF")
my_instrument.write(":ABORt")

my_instrument.write(":OUTPut:STATe OFF")
my_instrument.write(":SENSe:VOLTage:RANGe 0")
my_instrument.write(":SENSe:VOLTage:RANGe:AUTO off")

#my_instrument.write(":DISPlay:ENABle off")
my_instrument.write(":SENSe:VOLTage:LPASs OFF")
my_instrument.write(":SENSe:VOLTage:DFILter:STATe OFF")
my_instrument.write(":SYSTem:AZERo:STATe OFF")
my_instrument.write(":SYSTem:FAZero:STATe ON")
my_instrument.write(":SYSTem:LSYNc:STATe ON")

my_instrument.write(":SENSe:VOLTage:NPLCycles 5")

#my_instrument.write(":Trigger:Source BUS")
my_instrument.write(":Trigger:Delay 0")
my_instrument.write("TRIGger:COUNt "+str(batchsize))

my_instrument.write(":TRACe:POINts "+str(batchsize))
my_instrument.write(":TRACe:FEED SENSe")
my_instrument.write(":TRACe:FEED:CONTrol NEXT")

my_instrument.write(":INITiate")

timestr = time.strftime("%Y%m%d-%H%M%S_")
with open('csv/'+timestr+'Keithley_2182a_short_NPLC5.csv', mode='w') as csv_file:
    fieldnames = ['2182a_volt']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    clock=datetime.now()
    batches=0
    while True:
        if (int(my_instrument.query(":TRACe:FREE?").split(",")[1]) == 18*batchsize):
            results=my_instrument.query_ascii_values("TRACe:DATA?")
            
            my_instrument.write("TRACe:CLEar")
            my_instrument.write(":TRACe:FEED:CONTrol NEXT")
            my_instrument.write("INITiate")
            for val in results:
                writer.writerow({'2182a_volt': float(val)})

            batches = batches+1

            print("Batches received: "+str(batches))
            print("Script runtime seconds: "+str((datetime.now()-clock).total_seconds()))
            print("Effective readings per second: "+str(batchsize*batches/(datetime.now()-clock).total_seconds()))