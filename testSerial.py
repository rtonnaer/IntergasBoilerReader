#! /usr/bin/env python
import serial
from rich import print
from rich.console import Console
from rich.table import Table
import ctypes
from struct import *

# CLASS DEFINITIONS FOR BYTES PARSING
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

# FUNCTION FOR PARSING THE BYTE PACKAGE
def parse_packet(s):
  d = list(map(ord,unpack('=cccccccccccccccccccccccccccccccc', s)))
  
  msb = float(d[1])
  lsb = float(d[0])
  
  def getFloat(msb, lsb):
    if msb > 127:
      f = -(float(msb ^ 255) + 1) * 256 - lsb / 100
    else:
      f = float(msb * 265 + lsb) / 100
    return f
  
  t1 = getFloat(d[1],d[0]) # Rookgassensor (?)
  t2 = getFloat(d[3],d[2]) # Aanvoersensor S1
  t3 = getFloat(d[5],d[4]) # Retoursensor S2
  t4 = getFloat(d[7],d[6]) # Warmwatersensor S3
  t5 = getFloat(d[9],d[8]) # Boilersensor S4
  t6 = getFloat(d[11],d[10]) # buitenvoeler (?)
  ch_pressure = getFloat(d[13],d[12])
  temp_set = getFloat(d[15],d[14])
  fanspeed_set = getFloat(d[17],d[16])
  fanspeed = getFloat(d[19],d[18])
  fan_pwm = getFloat(d[21],d[20])
  io_curr = getFloat(d[23],d[22])
  
  
  
  flags = B27Flags()
  flags.asbyte = d[27]
  gp_switch = flags.b.gp_switch
  tap_switch = flags.b.tap_switch
  roomtherm = flags.b.roomtherm
  pump = flags.b.pump
  dwk = flags.b.dwk
  alarm_status = flags.b.alarm_status
  ch_cascade_relay = flags.b.ch_cascade_relay
  opentherm = flags.b.opentherm
  
  B29flags = B29Flags()
  B29flags.asbyte = d[29]
  gasvalve = B29flags.b.gasvalve
  spark =  B29flags.b.spark
  io_signal = B29flags.b.io_signal
  ch_ot_disabled = B29flags.b.ch_ot_disabled
  low_water_pressure = B29flags.b.low_water_pressure
  pressure_sensor = B29flags.b.pressure_sensor
  burner_block = B29flags.b.burner_block
  grad_flag = B29flags.b.grad_flag
  
  ch_pressure = None
  if not B29flags.b.pressure_sensor:
      ch_pressure = -35
  displ_code = d[24]
  
  # '-' => uit
  # ' ' => CV in rust
  # '1' => Gewenste temperatuur bereikt
  # '2' => Zelftest
  # '3' => Ventileren (voor en na-ventileren)
  # '4' => Ontsteken
  # '5' => CV Bedrijf
  # '6' => Tapwaterbedrijf
  # '7' => Opwarming boiler (tussenstap dmv omschakelventiel)

  
  ch_pressure = ch_pressure
  
  c2s = {
      51: "Warm water",
      102: "CV Brandt",
      126: "CV in rust",
      204: "Tapwater nadraaien",
      231: "CV nadraaien",
  }
  
  status = c2s.get(displ_code, "Onbekend (%s)" % displ_code)
  status = status

  return [t1, t2, t3, t4, t5, t6, ch_pressure, temp_set, fanspeed_set, fanspeed, fan_pwm, \
        io_curr, gp_switch, tap_switch, roomtherm, pump, dwk, alarm_status, ch_cascade_relay, opentherm, \
        gasvalve, spark, io_signal, ch_ot_disabled, low_water_pressure, pressure_sensor, burner_block, grad_flag, \
        ch_pressure] 
        

# Define the serial connection
serialCon = serial.Serial(
	port = "/dev/ttyAMA0",
	baudrate = 9600,
	timeout = 2)

# write to connection
serialCon.write('S?\r'.encode())
# read 32 bits from connection
s = serialCon.read(32)
# send the 32 bytes to the parse function and store it`s return
[t1, t2, t3, t4, t5, t6, ch_pressure, temp_set, fanspeed_set, fanspeed, fan_pwm, \
        io_curr, gp_switch, tap_switch, roomtherm, pump, dwk, alarm_status, ch_cascade_relay, opentherm, \
        gasvalve, spark, io_signal, ch_ot_disabled, low_water_pressure, pressure_sensor, burner_block, grad_flag, \
        ch_pressure] = parse_packet(s)

# Use rich to print a table to the terminal
tableTemps = Table(title="Intergas Temperaturen")
tableTemps.add_column('T1')
tableTemps.add_column('T2')
tableTemps.add_column('T3')
tableTemps.add_column('T4')
tableTemps.add_column('T5')
tableTemps.add_column('T6')
tableTemps.add_row(str(t1),str(t2),str(t3),str(t4),str(t5),str(t6))
console = Console()
console.print(tableTemps)

tableStatus = Table(title="Intergas Status Overzicht")
tableStatus.add_column('io_curr')
tableStatus.add_column('gp_switch')
tableStatus.add_row(str(bool(io_curr)),str(bool(gp_switch)))
console.print(tableStatus)
