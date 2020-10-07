#!/usr/bin/python
import sys
import math
from time import sleep
import paho.mqtt.client as mqtt
from datetime import datetime
import time
import os

print "cpu_temp_read.py"

def on_connect(client, userdata, flags, rc):
    global Connected                #Use global variable
    Connected = True                #Signal connection
    
def on_disconnect(client, userdata, flags, rc=0):    
    global Connected
    Connected = False

def outputTemp():
    try:
        temp = os.popen("vcgencmd measure_temp").readline()
        temp = temp.replace("temp=","")
        temp = temp.replace ("\n", "")
        temp = temp.replace ("'C", "")

        message = "{ \"temperature\": \"%s\" }" % (temp)

        client.publish("ChickenPi/sensors/CpuTemperature", message)
        print(message)
        
        print(" ")
    except Exception as error:
        print "Something went wrong. %s" % (error)

Connected = False
print("Beginning MQTT Connection")
client = mqtt.Client()
client.username_pw_set("chickenPi", "pi")
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.connect("192.168.1.157", 1883)
client.loop_start()

while Connected != True:    #Wait for connection
    time.sleep(1)

print("Completed  MQTT Connection")

try:
    while True:
        if(Connected <> True):
            reattemptConnect = True
            while Connected != True:    #Wait for connection
                try:
                    if(reattemptConnect == True):
                        client.reconnect()

                    reattemptConnect = False
                except:
                    reattemptConnect = True
                    print("reconnect failed")

                time.sleep(1)

                if(Connected == True):
                    print("exiting reconnect loop")

        outputTemp()
        sleep(10)
finally:
    print "\nCleaned up"



