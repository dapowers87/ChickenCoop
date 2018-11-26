#!/usr/bin/python
import sys
import Adafruit_DHT
import RPi.GPIO as GPIO
import math
from time import sleep
import paho.mqtt.client as mqtt
from datetime import datetime
import time

print "temp_read.py"

def on_connect(client, userdata, flags, rc):
    global Connected                #Use global variable
    Connected = True                #Signal connection
    
def on_disconnect(client, userdata, flags, rc=0):    
    global Connected
    Connected = False

def outputTempHum():
    try:
        humidity, temperature = Adafruit_DHT.read_retry(dht_chip_type, dht_pin)
        
        if(humidity == None or temperature == None):
            print("%s: Received None value..." % datetime.now())
            return
        
        global last_humidity
        global last_temp
        if(last_humidity == -1):
            last_humidity = humidity
            last_temp = temperature
        
        message = "{ \"temperature\": \"%.1f\", \"humidity\": \"%.1f\"}" % (temperature * 9. / 5. + 32, humidity)
        
        if(math.fabs(last_temp - temperature) > 20
           or humidity > 100
           or humidity < 0
           or math.fabs(last_humidity - humidity) > 20):
            print("Bad read... %s" % message)
        else:
            client.publish("ChickenPi/sensors/NestDHT11", message)
            print(message)
            last_humidity = humidity
            last_temp = temperature
            
        print(" ")
    except error:
        print "Something went wrong. %s" % (error)

GPIO.setwarnings(False)

dht_pin = 24
dht_chip_type = 11

last_temp = -1
last_humidity = -1

Connected = False
client = mqtt.Client()
client.username_pw_set("chickenPi", "pi")
client.on_connect = on_connect
client.on_disconnect = on_disconnect
#client.connect("m11.cloudmqtt.com", 11608)
client.connect("192.168.1.151", 1883)
client.loop_start()

while Connected != True:    #Wait for connection
    time.sleep(1)

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
        
        outputTempHum()
        sleep(10)
finally:
    GPIO.cleanup()
    print "\nCleaned up"



