import pyvisa,time,csv
from pyvisa.constants import StopBits, Parity
from datetime import datetime
from paho.mqtt import client as mqtt_client
import json

rm = pyvisa.ResourceManager()

my_instrument = rm.open_resource('ASRL/dev/ttyUSB0::INSTR',baud_rate=19200, data_bits=8,write_termination='\r',read_termination='\r',parity=Parity.none)
my_instrument.timeout = 1000*60*5
my_instrument.write("*RST")
print(my_instrument.query("*IDN?"))
my_instrument.write("*CLS")

my_instrument.write(":syst:pres")
time.sleep(2)

#my_instrument.write(":CALibration:UNPRotected:ACALibration:INITiate")
#my_instrument.write(":CALibration:UNPRotected:ACALibration:STEP1")
#my_instrument.write(":CALibration:UNPRotected:ACALibration:DONE")

ACALtemp = my_instrument.query(":CALibration:UNPRotected:ACALibration:TEMPerature?") 
# my_instrument.query(":SENSe:TEMPerature:RTEMperature?")

#my_instrument.write(":sens:volt:ref:acq")
#my_instrument.query("*OPC?")
#my_instrument.write(":sens:volt:ref:stat on")

my_instrument.write("INIT:CONT OFF")
my_instrument.write(":ABORt")

my_instrument.write(":OUTPut:STATe OFF")
my_instrument.write(":SENSe:VOLTage:RANGe 0")
my_instrument.write(":SENSe:VOLTage:RANGe:AUTO off")

my_instrument.write(":DISPlay:ENABle off")
my_instrument.write(":SENSe:VOLTage:LPASs OFF")
my_instrument.write(":SENSe:VOLTage:DFILter:STATe OFF")
my_instrument.write(":SYSTem:AZERo:STATe ON")
my_instrument.write(":SYSTem:FAZero:STATe ON")
my_instrument.write(":SYSTem:LSYNc:STATe ON")

my_instrument.write(":SENSe:VOLTage:NPLCycles 5")


broker = '192.168.178.27'
port = 1883
topic = "lab_sensors/TMP117"
client_id = f'subscribe-{42}'
TMP117_room_temp = 0.0


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        x = msg.payload.decode()[33:38]
        global TMP117_room_temp
        TMP117_room_temp = float(x)
        print(TMP117_room_temp)

    client.subscribe(topic)
    client.on_message = on_message

client = connect_mqtt()
subscribe(client)
    


timestr = time.strftime("%Y%m%d-%H%M%S_")
with open('csv/'+timestr+'Keithley_2182a_tempco.csv', mode='w') as csv_file:
    fieldnames = ['time', '2182a_volt', 'TMP117_room_temp', 'RTEMperature', 'ACALtemp']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    clock=datetime.now()
    while True:
        client.loop()
        val = my_instrument.query(":MEASure?")
        internal_temp = my_instrument.query(":SENSe:TEMPerature:RTEMperature?")
        writer.writerow({'time':time.time(), '2182a_volt':val, 'TMP117_room_temp':TMP117_room_temp, 'RTEMperature':internal_temp, 'ACALtemp':ACALtemp})

        print("Measured: "+str(val))
        print("internal_temp: "+str(internal_temp))
        print("last room temp: "+str(TMP117_room_temp))
