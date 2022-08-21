#!/usr/bin/env python
import serial
import time
import struct
from rich import print, Table

# Class definition
class intergas_pc_interface:
  ## define class constants 
  baudrate = 9600
  timeout = 2
  def __init__(self,port):
    self.port = port
  
  def __parse_boiler_data__(self):
    ''' internal method that is used to convert raw bytes to logical values '''
    def getFloat(msb, lsb):
      if msb > 127:
        f = -(float(msb ^ 255) + 1) * 256 - lsb / 100
      else:
        f = float(msb * 265 + lsb) / 100
      return f

    print(f'Raw byte-string: {self.recv}')
    print(f'Length of byte-string: {len(self.recv)}')
    
    
    self.t1 = getFloat(self.recv[1],self.recv[0]) # Rookgas Temperatuur (?)
    self.t2 = getFloat(self.recv[3],self.recv[2]) # Wateraanvoer Temperatuur (S1)
    self.t3 = getFloat(self.recv[5],self.recv[4]) # Waterretour Temperatuur (S2)
    self.t4 = getFloat(self.recv[7],self.recv[6]) # Warmwater Temperatuur (S3)
    self.t5 = getFloat(self.recv[9],self.recv[8]) # (externe) boiler temperatuur (S4)
    self.t6 = getFloat(self.recv[11],self.recv[10]) # Buitenvoeler Temperatuur (?)
    self.ch_pressure  = getFloat(self.recv[13],self.recv[12])
    self.temp_set = getFloat(self.recv[15],self.recv[14])
    self.fanspeed_set = getFloat(self.recv[17],self.recv[16])
    self.fanspeed = getFloat(self.recv[19],self.recv[18])
    self.fan_pwm = getFloat(self.recv[21],self.recv[20])
    self.io_curr = getFloat(self.recv[23],self.recv[22])

   
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
      self.recv = self.ser.read(32) # the boiler sends 32 bytes  of data, these are stored in a class variable
      self.__parse_boiler_data__() # call the internal method to parse the 32 bytes of data
  
  def print_data(self):
    ''' method that uses class variables to pretty print the data to the terminal'''
    
    table = Table(title="Intergas Data") # defining a rich table incl. column headers
    table.add_column('Description')
    table.add_column('Value')
    table.add_column('Unit')
    # adding rows
    table.add_row()

    table._add_row("Rookgas",self.t1,'C')
    table._add_row("Wateraanvoer",self.t2,'C')
    table._add_row("Waterretour",self.t3,'C')
    table._add_row("Warmwater",self.t4,'C')
    table._add_row("externe boiler",self.t5,'C')
    table._add_row("Buitenvoeler",self.t6,'C')
    table._add_row("Druk",self.ch_pressure,'Bar')
    table._add_row("Ingestelde Temperatuur",self.temp_set,'C')
    table._add_row("Ingestelde Fan speed",self.fanspeed_set,"RPM")
    table._add_row("Huidige Fanspeed".self.fanspeed,"RPM")
    table._add_row("Fans PWM",self.fan_pwm)
    table._add_row("??",self.io_curr)


if __name__ == '__main__':
  # initate the connection to the serial interface at port  
  intergas_interface = intergas_pc_interface('ttyAMA0')
  intergas_interface.connect()

  if intergas_interface.is_open == True:
    print('Serial connection is open')
    intergas_interface.read_boiler_data() # read the boiler data once
    intergas_interface.print_data() # print the data
