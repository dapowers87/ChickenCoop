import RPi.GPIO as gpio
import time
import sys
import requests
import datetime
import time
import threading
import paho.mqtt.client as mqtt

print "motor.py"

time.sleep(10)

#PINS################
HBridgeOutA = 26
HBridgeOutB = 13
#
CloseButton = 6
OpenButton = 12
#
TopReed = 22
BottomReed = 27
#PINS################

#-1: Closing
#0: Stationary
#1: Opening
global MovementState
MovementState = 0

def on_connect(client, userdata, flags, rc):
    global Connected                #Use global variable
    Connected = True                #Signal connection

def on_disconnect(client, userdata, flags, rc=0):
    global Connected
    Connected = False

def on_message(client, userdata, message):
    if(message.payload == "OPEN"):
        print("**OPEN Recevied")
        OpenGate()
    elif (message.payload == "CLOSE"):
        print("**CLOSE Recevied")
        CloseGate()
    elif (message.payload == "STOP"):
        print("**STOP Received")
        StopGate("Remotely Stopped")
    elif (message.payload == "FIX_CLOSE_OVERSHOOT"):
        print("**FIX_CLOSE_OVERSHOOT Received")
        FixCloseOvershoot()
    elif (message.payload == "OPEN_MANUALLY"):
        print("**OPEN_MANUALLY Received")
        OpenGateManually()
    else:
        print(message.payload)

Connected = False
print("Beginning MQTT Connection")
client = mqtt.Client()
client.username_pw_set("chickenPi", "pi")
client.on_message = on_message
client.on_connect = on_connect
client.on_disconnect = on_disconnect
#client.connect("m11.cloudmqtt.com", 11608)
client.connect("192.168.1.151", 1883)
client.loop_start()       #connect to broker

while Connected != True:    #Wait for connection
    time.sleep(0.1)

client.subscribe("chickenPi/door/set")

print("Completed  MQTT Connection")

def UpdateHADetailedState(message, topic="chickenPi/door/DetailedState"):
    client.publish(topic, message, 0, True)

def UpdateHACoverState(message):
    client.publish("chickenPi/door/State", message, 0, True)

def PublishJammedSignal(state):
    message = ""
    if(state == True):
        message = "ON"
    else:
        message = "OFF"
    client.publish("chickenPi/door/Jammed", message, 0, True)

def PublishFailedSensorSignal(state):
    message = ""
    if(state == True):
        message = "ON"
    else:
        message = "OFF"
    client.publish("chickenPi/door/FailedSensor", message, 0, True)

def InitializePins():
    gpio.setmode(gpio.BCM)

    gpio.setup(HBridgeOutA, gpio.OUT)
    gpio.setup(HBridgeOutB, gpio.OUT)

    gpio.output(HBridgeOutA, False) #stop motor
    gpio.output(HBridgeOutB, False)

    gpio.setup(CloseButton, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(OpenButton, gpio.IN, pull_up_down=gpio.PUD_DOWN)

    gpio.setup(TopReed, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(BottomReed, gpio.IN, pull_up_down=gpio.PUD_DOWN)

def GetReed(reed):
    #Get 3 true reads in a row

    val = True
    for x in range(0, 3):
        val = val and gpio.input(reed)

    return val

def CloseGate():
    if(GetReed(BottomReed) == 1):
        print("Gate already closed")
        PrintReed()
        UpdateHACoverState("Closed")
        UpdateHADetailedState("Closed")
        PublishJammedSignal(False)
        return

    print("Closing Gate")
    gpio.output(HBridgeOutA, False)
    gpio.output(HBridgeOutB, True)

    global MovementState
    MovementState = -1

    UpdateHADetailedState("Closing")

def FixCloseOvershoot():
    UpMotion()
    time.sleep(3)
    OpenGate()

def UpMotion():
    gpio.output(HBridgeOutA, True)
    gpio.output(HBridgeOutB, False)

def PrintReed():
    top = GetReed(TopReed)
    bottom = GetReed(BottomReed)
    
    print("Top: %s\tBottom: %s" % (top, bottom))

def OpenGateManually():
    print("Opening gate manually")
    UpMotion()
    time.sleep(12)
    StopGate("Manually Open")

def OpenGate():
    if(GetReed(TopReed) == 1):
        print("Gate already open")
        PrintReed()
        UpdateHACoverState("Open")
        UpdateHADetailedState("Open")
        PublishJammedSignal(False)
        return

    print("Opening Gate")
    UpMotion()

    global MovementState
    MovementState = 1

    UpdateHADetailedState("Opening")

    time.sleep(12)
    if(GetReed(BottomReed) == 1):
        PublishJammedSignal(True)
        StopGate("Jammed")

def StopGate(doorState):
    gpio.output(HBridgeOutA, False)
    gpio.output(HBridgeOutB, False)

    global MovementState
    MovementState = 0

    UpdateHADetailedState(doorState)

def GetSunriseSunset():
    URL = "https://api.sunrise-sunset.org/json?lat=30.2171827&lng=-97.8351872&formatted=0"
    r = None
    while r == None:
        try:
            r = requests.get(url = URL)
        except requests.exceptions.ConnectionError as e:
            print (e)

    data = r.json()
    sunrise = datetime.datetime.strptime(data['results']['sunrise'], '%Y-%m-%dT%H:%M:%S+00:00').replace(second=0, microsecond=0)
    sunset = datetime.datetime.strptime(data['results']['sunset'], '%Y-%m-%dT%H:%M:%S+00:00').replace(second=0, microsecond=0)
    return sunrise, sunset

def automateSunriseSunsetDoor():
    sunrise, sunset = GetSunriseSunset()

    print("Sunrise/Sunset is at %s/%s" % (sunrise, sunset))

    sunriseOffset = 30
    sunsetOffset = 15
    print("%s" % str(sunset + datetime.timedelta(minutes = sunsetOffset)))
    while(True):
        utc = datetime.datetime.utcnow().replace(second=0, microsecond=0)

        #6 should be around midnight local, depending on DST. Update at midnight
        if utc.time() == datetime.time(6, 0):
            print("Updating Sunrise/Sunset")
            sunrise, sunset = GetSunriseSunset()
        elif utc == sunrise + datetime.timedelta(minutes = sunriseOffset):
            print("Opening gate for sunrise")
            OpenGate()
            time.sleep(60)
        elif utc == sunset + datetime.timedelta(minutes = sunsetOffset):
            print("Closing gate for sunset")
            CloseGate()
            time.sleep(60)

def SendInitialStatus():
    top = GetReed(TopReed)
    bottom = GetReed(BottomReed)

    if(top == 1 and bottom == 1):
        UpdateHACoverState("Error. Both Sensors True")
    elif(top == 1):
        UpdateHACoverState("Open")
        UpdateHADetailedState("Open")
    elif(bottom == 1):
        UpdateHACoverState("Closed")
        UpdateHADetailedState("Closed")


InitializePins()

SendInitialStatus()

#threading.Thread(target=automateSunriseSunsetDoor).start()

def ScanForReedSensorFailure():
    failureObserved = False
    failCount = 0
    while (True):
        topReedRead = GetReed(TopReed)
        bottomReedRead = GetReed(BottomReed)
        
        if topReedRead == 1 and bottomReedRead == 1:
            failCount += 1
            if failCount > 5:
                PublishFailedSensorSignal(True)
                if not failureObserved:
                    print("Sensor failure detected")
                    failureObserved = True
        else:
            failCount = 0
            PublishFailedSensorSignal(False)
            if failureObserved:
                print("Sensor failure cleared")
                failureObserved = False
        
        time.sleep(1)

scanThread = threading.Thread(target=ScanForReedSensorFailure)
scanThread.daemon = True
scanThread.start()

try:

    #CloseGate()
    #sys.exit()

    while (True):
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
                    client.subscribe("chickenPi/door/set")
                    print("exiting reconnect loop")

        openButtonRead = 0 #gpio.input(OpenButton)
        closeButtonRead = 0 #gpio.input(CloseButton)

        topReedRead = GetReed(TopReed)
        bottomReedRead = GetReed(BottomReed)

        if( MovementState <> 0 ):
            if(MovementState == -1 and bottomReedRead == 1
                or MovementState == 1 and topReedRead == 1):
                    doorState = ""
                    if(topReedRead == 1):
                        doorState = "Open"
                    else:
                        doorState = "Closed"
                        time.sleep(7) #let door lock
                    UpdateHACoverState(doorState)#update cover status
                    StopGate(doorState)
                    PublishJammedSignal(False)
                    print("Gate reached desired state")
except KeyboardInterrupt:
    print("\n\nExiting\n\n")

    sys.exit()
finally:
    client.disconnect()
    client.loop_stop()
    gpio.cleanup()


