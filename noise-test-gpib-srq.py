# My usual goto library pyvisa-py doesn't currently implement SRQ support.
# So here I am using the linux-gpib python bindings to react to SRQ states
# and avoid bothering the voltmeter with frequent "done yet?" requests.

import gpib,time,csv,sys
from datetime import datetime


batchsize = 50

my_instrument = gpib.find("2182a")
gpib.config(0,gpib.IbcAUTOPOLL,1)  # Enable automatic serial polling
gpib.config(my_instrument,gpib.IbcTMO, gpib.T30s) # Set timeout to 30 seconds

gpib.write(my_instrument,"SYSTem:ERRor?")
print(gpib.read(my_instrument,100))

gpib.write(my_instrument,"*RST")

gpib.write(my_instrument,"*IDN?")
print(gpib.read(my_instrument,100))

gpib.write(my_instrument,"*CLS")

gpib.write(my_instrument,"stat:meas:enab 512") #enable BFL
gpib.write(my_instrument,"*sre 1") #enable MSB

gpib.write(my_instrument,":INIT:CONT OFF;:ABORT")
gpib.write(my_instrument,":SENS:FUNC 'VOLT:DC'")
gpib.write(my_instrument,":SENS:CHAN 1")
gpib.write(my_instrument,":SENS:VOLT:CHAN1:LPAS:STAT OFF")
gpib.write(my_instrument,":SENS:VOLT:CHAN1:DFIL:STAT OFF")
gpib.write(my_instrument,":SENS:VOLT:DC:NPLC 1")
gpib.write(my_instrument,":SENS:VOLT:CHAN1:RANG 0")
gpib.write(my_instrument,":SENS:VOLT:DC:DIG 4")
gpib.write(my_instrument,":FORM:ELEM READ")
gpib.write(my_instrument,":TRIG:COUN "+str(batchsize))
gpib.write(my_instrument,"trac:poin "+str(batchsize))
gpib.write(my_instrument,"trac:feed sens1")
gpib.write(my_instrument,":TRIG:DEL 0")
gpib.write(my_instrument,":TRIG:SOUR IMM")
gpib.write(my_instrument,":DISP:ENAB OFF")

gpib.write(my_instrument,":TRACe:FEED:CONTrol NEXT")
gpib.write(my_instrument,"INITiate; *wai")

try:
    timestr = time.strftime("%Y%m%d-%H%M%S_")
    with open('csv/'+timestr+'Keithley_2182a_short_NPLC1.csv', mode='w') as csv_file:
        fieldnames = ['2182a_volt']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        clock=datetime.now()
        batches=0
        while True:
            sta = gpib.wait(my_instrument, gpib.TIMO | gpib.RQS) # Wait for Timeout or Request Service on device
            if (sta & gpib.TIMO) != 0:
                print("Timed out")
            else:
                print("Device asserted RQS")
                
                
                gpib.write(my_instrument,"TRACe:DATA?")
                readings = gpib.read(my_instrument,1000).decode("utf-8").rstrip()
                readings = readings.split(",")
                #print(readings)
                
                gpib.write(my_instrument,"TRACe:CLEar")
                gpib.write(my_instrument,":TRACe:FEED:CONTrol NEXT")
                gpib.write(my_instrument,"INITiate; *wai")

                for val in readings:
                    writer.writerow({'2182a_volt': float(val)})

                batches = batches+1

                print("Batches received: "+str(batches))
                print("Script runtime seconds: "+str((datetime.now()-clock).total_seconds()))
                print("Effective readings per second: "+str(batchsize*batches/(datetime.now()-clock).total_seconds()))
                
except (KeyboardInterrupt, SystemExit) as exErr:

    gpib.write(my_instrument,":ABORt")
    gpib.close(my_instrument)
    print("kthxbye")
    sys.exit(0)