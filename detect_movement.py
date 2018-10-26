#!/usr/bin/python
import sys
import Adafruit_DHT
import RPi.GPIO as GPIO
import math
from time import sleep
import paho.mqtt.client as mqtt
from datetime import datetime
import time

print "detect_movement.py"

global motionDetected 
motionDetected = False

def on_connect(client, userdata, flags, rc):
    global Connected                #Use global variable
    Connected = True                #Signal connection
    
def on_disconnect(client, userdata, flags, rc=0):    
    global Connected
    Connected = False

def publishFindings(state):
    client.publish("ChickenPi/sensors/Movement", '{ "detected" : "%s" }' % str(state).lower())

def motionSensor(channel):
    motionDetected = True     
    print("Motion detected @ %s" % datetime.now())        
    publishFindings(True)
    while GPIO.input(hum_pin): 
        sleep(10)
    motionDetected = False
        
GPIO.setwarnings(False)


hum_pin = 4

GPIO.setmode(GPIO.BCM)
GPIO.setup(hum_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(hum_pin, GPIO.RISING, callback=motionSensor, bouncetime=150)

Connected = False
client = mqtt.Client()
client.username_pw_set("chickenPi", "pi")
client.on_connect = on_connect
client.on_disconnect = on_disconnect
#client.connect("m11.cloudmqtt.com", 11608)
client.connect("192.168.1.151", 1883)
client.loop_start()

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
        
        sleep(20)
        if motionDetected <> True:
            publishFindings(False)
        
finally:
    GPIO.cleanup()
    print "\nCleaned up"



