#!/usr/bin/env python
import serial
import time
from rich import print

# Class definition
class intergas_pc_interface:
  ## define class constants 
  baudrate = 9600
  timeout = 2
  def __init__(self,port):
    self.port = port
  
  def __parse_boiler_data__(self):
    ''' internal method that is used to convert raw bytes to logical values '''
    print(bytes(self.recv))
 
  def connect(self):  
    ''' method for connecting to the given serial port '''
    self.ser = serial.Serial(port='/dev/' + self.port, baudrate=self.baudrate,timeout=self.timeout)
    self.is_open = self.ser.is_open
    return self.ser
  
  def read_boiler_data(self):
    ''' method that reads the data from the boiler and stores it in the class'''
    if self.is_open == True:
      # creating a hexcode packet to write to the serial connection
      packet = bytearray()
      packet.append(0x53)
      packet.append(0x3F)
      packet.append(0x0D)

      self.ser.write(packet)
      self.recv = self.ser.read(32) # store the first 32 bytes that are recieved in a class variable
      self. __parse_boiler_data__() 
  

if __name__ == '__main__':
  # initate the connection to the serial interface at port  
  intergas_interface = intergas_pc_interface('ttyAMA0')
  intergas_interface.connect()

  if intergas_interface.is_open == True:
    print('Serial connection is open')
    intergas_interface.read_boiler_data() # read the boiler data once
    
