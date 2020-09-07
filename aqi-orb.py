#
# Code for my AQI orb
#
# Written by Glen Darling, Sept. 2020.
#

import json
import requests
import signal
import subprocess
import sys
import threading
import time

# Global for the URL of the PurpleAir sensor to monitor
SENSOR_URL = 'https://www.purpleair.com/json?show=51587'

# Import the required libraries
import board
import neopixel

# A global to indicate the input pin number connected to the NeoPixels
neopixel_pin = board.D18

# A global to indicate the number of NeoPixels that are connected
neopixel_count = 8

# The global array of neopixels
neopixels = None

# Initialize the NeoPixels
neopixels = neopixel.NeoPixel(neopixel_pin, neopixel_count)

# Globals to contain the monitored PM2.5 and AQI values
pm25 = 0
aqi = 0

# Global to keep the threads looping
keep_on_swimming = True

# Global table of AQI breakpoints
# Official website uses these RGB colors, but some don't work well on NeoPixels
#     104, 223,  67
#     255, 254,  84
#     240, 132,  50
#     235,  50,  35
#     133,  70, 147
#     115,  20,  37
# So the values in the table below are tweaked a bit for NeoPixels
#
# [        0,       1,    2,   3,   4,   5,   6 ]
# [      bot,     top,  min, max,   r,   g,   b ]
# [---------------------------------------------]
table = [
  [      0.0,     0.0,    0,   0,   0, 255,   0 ],
  [      0.0,    12.1,    0,  50,   0, 255,   0 ],
  [     12.1,    35.5,   51, 100, 128, 128,   0 ],
  [     35.5,    55.5,  101, 150, 192,  64,   0 ],
  [     55.5,   150.5,  151, 200, 255,   0,   0 ],
  [    150.5,   250.5,  201, 300, 192,   0,  16 ],
  [    250.5,   350.5,  301, 400,  24,   0,   4 ],
  [    350.5,   500.5,  401, 500,  24,   0,   4 ],
  [    500.5, 99999.9,  501, 999,  24,   0,   4 ],
  [  99999.9,100000.0,  999,1000,  24,   0,   4 ]
]

# Debug flags
DEBUG_AQI = False
DEBUG_RGB = False
DEBUG_REQ_THREAD = False
DEBUG_MAIN_LOOP = False
DEBUG_SIGNAL = False

# Debug print
def debug(flag, str):
  if flag:
    print(str)

# Given a PM2.5 value, return the table row number that is applicable:
def pm25_to_row_num(pm25):
  # Never return first or last row of table
  for i in range(1, len(table) - 1):
    row = table[i]
    if pm25 <= row[1]:
      return i
  # Never return first or last row of table
  return len(table) - 2

# Given a PM2.5 value, return the applicable AQI
def pm25_to_aqi(pm25):
  i = pm25_to_row_num(pm25)
  row = table[i]
  rb = row[0]
  rt = row[1]
  f = ((1.0 * pm25) - rb) / (rt - rb)
  mn = row[2]
  mx = row[3]
  return int(mn + f * (mx - mn))

# Given a PM2.5 value, return the applicable AQI color (r,g,b)
def pm25_to_rgb(pm25):
  i = pm25_to_row_num(pm25)
  row = table[i]
  rb = row[0]
  rt = row[1]
  f = ((1.0 * pm25) - rb) / (rt - rb)
  r1= row[4]
  g1= row[5]
  b1= row[6]
  row = table[i + 1]
  r2= row[4]
  g2= row[5]
  b2= row[6]
  r = r1 + f * (r2 - r1)
  g = g1 + f * (g2 - g1)
  b = b1 + f * (b2 - b1)
  return (r, g, b)

# The thread that monitors the AQI and sets the NeoPixels accordingly
REQUEST_TIMEOUT_SEC = 30
SLEEP_BETWEEN_AQI_CHECKS_SEC = 15
class AqiThread(threading.Thread):
  def run(self):
    global pm25
    debug(DEBUG_REQ_THREAD, "API monitor thread started!")
    global keep_on_swimming
    while keep_on_swimming:
      try:
        debug(DEBUG_REQ_THREAD, ('REQ: url="%s", t/o=%d' % (SENSOR_URL, REQUEST_TIMEOUT_SEC)))
        r = requests.get(SENSOR_URL, timeout=REQUEST_TIMEOUT_SEC)
        if 200 == r.status_code:
          debug(DEBUG_REQ_THREAD, ('--> "%s" [succ]' % (SENSOR_URL)))
          j = r.json()
          pm25 = float(j['results'][0]['PM2_5Value'])
          aqi = pm25_to_aqi(pm25)
          debug(DEBUG_REQ_THREAD, ('*** PM2.5 == %0.1f --> AQI == %d ***' % (pm25, aqi)))
        else:
          debug(DEBUG_REQ_THREAD, ('--> "%s" [fail]' % (SENSOR_URL)))
      except requests.exceptions.Timeout:
        debug(DEBUG_REQ_THREAD, ('--> "%s" [time]' % (SENSOR_URL)))
      except:
        debug(DEBUG_REQ_THREAD, ('--> "%s" [expt]' % (SENSOR_URL)))
      time.sleep(SLEEP_BETWEEN_AQI_CHECKS_SEC)
    debug(DEBUG_SIGNAL, 'Exited AQI thread.')

# Main program (to start the web server thread)
if __name__ == '__main__':

  def signal_handler(signum, frame):
    global keep_on_swimming
    debug(DEBUG_SIGNAL, 'Signal received!')
    keep_on_swimming = False
    time.sleep(5)
    sys.exit(0)
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGQUIT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  if DEBUG_AQI:
    debug(DEBUG_AQI, '--> Testing AQI value calculations:')
    #for x in range(0, 999, 1):
    for x in [0.0, 12.0, 12.1, 34.4, 35.5, 55.4, 55.5, 150.4, 150.5, 250.4, 250.5, 350.4, 350.5, 500.4, 500.5, 99999.9, 1000000]:
      a = pm25_to_aqi(x)
      debug(DEBUG_AQI, ('*** PM2.5 == %0.1f --> AQI == %d ***' % (x, a)))

  if DEBUG_RGB:
    debug(DEBUG_RGB, '--> Testing RGB value calculations:')
    for x in range(0, 350, 5):
      rgb = pm25_to_rgb(x)
      a = pm25_to_aqi(x)
      debug(DEBUG_RGB, ('*** PM2.5 == %0.1f --> AQI == %d --> RGB == (%d,%d,%d) ***' % (x, a, rgb[0], rgb[1], rgb[2])))
      neopixels.fill(rgb)
      time.sleep(0.5)

  # Start the thread that checks the AQI from the sensor
  aqi_check = AqiThread()
  aqi_check.start()

  # Loop forever checking the global AQI value and setting the NeoPixels
  SLEEP_BETWEEN_NEOPIXEL_UPDATES_SEC = 15
  debug(DEBUG_MAIN_LOOP, "Main loop is starting...")
  while keep_on_swimming:
    rgb = pm25_to_rgb(pm25)
    a = pm25_to_aqi(pm25)
    debug(DEBUG_MAIN_LOOP, ('--> PM2.5 == %0.1f --> AQI == %d --> RGB == (%d,%d,%d) ***' % (pm25, a, rgb[0], rgb[1], rgb[2])))
    neopixels.fill(rgb)
    time.sleep(SLEEP_BETWEEN_NEOPIXEL_UPDATES_SEC)

  debug(DEBUG_SIGNAL, 'Exited main thread.')

