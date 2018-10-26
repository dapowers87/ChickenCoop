
#!/usr/bin/python
import sys
from time import sleep
import datetime
import paho.mqtt.client as mqtt

print "is_alive.py"

client = mqtt.Client()
client.username_pw_set("chickenPi", "pi")
client.connect("m11.cloudmqtt.com", 11608)

while True:        
    client.publish("ChickenPi/isAlive", '{"is_alive":"true"}')
    print("%s ping" % datetime.datetime.now())
    sleep(60)


