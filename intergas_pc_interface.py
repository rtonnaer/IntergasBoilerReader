#!/usr/bin/env python
import serial
import time
import struct
from rich import print
from rich.table import Table
from rich.console import Console

import ctypes

# Data conversions that are needed
c_uint8 = ctypes.c_uint8
class B27Flags_bits(ctypes.LittleEndianStructure):
    _fields_ = [
            ("gp_switch", c_uint8, 1),
            ("tap_switch", c_uint8, 1),
            ("roomtherm", c_uint8, 1),
            ("pump", c_uint8, 1),
            ("dwk", c_uint8, 1),
            ("alarm_status", c_uint8, 1),
            ("ch_cascade_relay", c_uint8, 1),
            ("opentherm", c_uint8, 1),
        ]

class B27Flags(ctypes.Union):
    _fields_ = [("b", B27Flags_bits),
                ("asbyte", c_uint8)]

class B29Flags_bits(ctypes.LittleEndianStructure):
    _fields_ = [
            ("gasvalve", c_uint8, 1),
            ("spark", c_uint8, 1),
            ("io_signal", c_uint8, 1),
            ("ch_ot_disabled", c_uint8, 1),
            ("low_water_pressure", c_uint8, 1),
            ("pressure_sensor", c_uint8, 1),
            ("burner_block", c_uint8, 1),
            ("grad_flag", c_uint8, 1),
        ]

class B29Flags(ctypes.Union):
    _fields_ = [("b", B29Flags_bits),
                ("asbyte", c_uint8)]

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
    
    # Conversion of the Floating Values
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

    # Conversion of Flags in Byte 27
    flags = B27Flags() 
    flags.asbyte = self.recv[27]
    self.gp_switch = flags.b.gp_switch
    self.tap_switch = flags.b.tap_switch
    self.roomtherm = flags.b.roomtherm
    self.pump = flags.b.pump
    self.dwk = flags.b.dwk
    self.alarm_status = flags.b.alarm_status
    self.ch_cascade_relay = flags.b.ch_cascade_relay
    self.opentherm = flags.b.opentherm
    
    # Conversion of Flags in Byte 29
    B29flags = B29Flags()
    B29flags.asbyte = self.recv[29]
    self.gasvalve = B29flags.b.gasvalve
    self.spark =  B29flags.b.spark
    self.io_signal = B29flags.b.io_signal
    self.ch_ot_disabled = B29flags.b.ch_ot_disabled
    self.low_water_pressure = B29flags.b.low_water_pressure
    self.pressure_sensor = B29flags.b.pressure_sensor
    self.burner_block = B29flags.b.burner_block
    self.grad_flag = B29flags.b.grad_flag
  
    # Conversion of the CH Pressure ?? 
    self.ch_pressure = None
    if not B29flags.b.pressure_sensor:
      self.ch_pressure = -35
    # Getting the Display Code  
    self.displ_code = self.recv[24]
    # conversion of display code to textstring
    c2s = {
      51: "Warm water",
      102: "CV Brandt",
      126: "CV in rust",
      204: "Tapwater nadraaien",
      231: "CV nadraaien",
     }
  
    self.status = c2s.get(self.displ_code, "Onbekend (%s)" % self.displ_code)
  

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
    ## Printing the Measured values
    table = Table(title="Intergas Data - Values") # defining a rich table incl. column headers
    table.add_column('Description')
    table.add_column('Value')
    table.add_column('Unit')
    # adding rows
    table.add_row()
    table.add_row("Rookgas",str(self.t1),'C')
    table.add_row("Wateraanvoer",str(self.t2),'C')
    table.add_row("Waterretour",str(self.t3),'C')
    table.add_row("Warmwater",str(self.t4),'C')
    table.add_row("externe boiler",str(self.t5),'C')
    table.add_row("Buitenvoeler",str(self.t6),'C')
    table.add_row("Druk",str(self.ch_pressure),'Bar')
    table.add_row("Ingestelde Temperatuur",str(self.temp_set),'C')
    table.add_row("Ingestelde Fan speed",str(self.fanspeed_set),"RPM")
    table.add_row("Huidige Fanspeed",str(self.fanspeed),"RPM")
    table.add_row("Fans PWM",str(self.fan_pwm),"unit")
    table.add_row("??",str(self.io_curr),"unit")
   
    ## Printing the Flags
    tableFlags = Table(title="Intergas Data - Flags") # defining a rich table incl. column headers
    tableFlags.add_column('Description')
    tableFlags.add_column('Flag')

    tableFlags.add_row("General Power (?)",str(self.gp_switch))
    tableFlags.add_row("Tap Water",str(self.tap_switch))
    tableFlags.add_row("Kamer Thermostaat",str(self.roomtherm))
    tableFlags.add_row("Pomp Schakelaar",str(self.pump))
    tableFlags.add_row("Drieweg Klep",str(self.dwk))
    tableFlags.add_row("Alarm",str(self.alarm_status))
    tableFlags.add_row("Cascade Klep?",str(self.ch_cascade_relay))
    tableFlags.add_row("Open Therm",str(self.opentherm))

    tableMisc = Table(title="Intergas Data - Misc")
    tableMisc.add_column('Description')
    tableMisc.add_column('Value')
    
    tableMisc.add_row("STatus",self.status)

    # Rendering the Console
    console = Console()
    console.print(table)
    console.print(tableFlags)
    console.print(tableMisc)

if __name__ == '__main__':
  # initate the connection to the serial interface at port  
  intergas_interface = intergas_pc_interface('ttyAMA0')
  intergas_interface.connect()

  if intergas_interface.is_open == True:
    print('Serial connection is open')
    while True:
     intergas_interface.read_boiler_data() # read the boiler data once
     intergas_interface.print_data() # print the data
     time.sleep(1)
