#! /usr/bin/env python
import paho.mqtt.client as mqtt


# Defining a MQTT Client and Connect to Home Assistant
client = mqtt.Client()
retVal = client.connect('homeassistant.local')


# Publish a value to homeassistant
client.publish('test',"Hi")