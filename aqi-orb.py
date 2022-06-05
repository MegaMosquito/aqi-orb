#
# Code for my AQI orb
#
# Written by Glen Darling, Sept. 2020.
#

from datetime import datetime
import json
import requests
import signal
import subprocess
import sys
import threading
import time

# LEDs are dimmed from EVENING_HOUR through MORNING_HOUR (use 24hr clock!)
EVENING_HOUR = 20
MORNING_HOUR = 6

# This code connects to the central PurpleAir cloud APIs
# Example:
#   curl --header "X-API-Key: *****" https://api.purpleair.com/v1/keys
#   curl --header "X-API-Key: *****" https://api.purpleair.com/v1/sensors/*****
# Full API documentation:
#   https://api.purpleair.com
# More info:
#    https://community.purpleair.com/t/making-api-calls-with-the-purpleair-api/180
#
# API Details:
PURPLE_AIR_SENSOR_URL       = 'https://api.purpleair.com/v1/sensors/'
PURPLE_AIR_API_KEY_HEADER   = 'X-API-Key'
#
# My credentials and sensor ID (edit these to contain your own values):
MY_PURPLE_AIR_READ_API_KEY  = '*****'
MY_PURPLE_AIR_WRITE_API_KEY = '*****'
MY_PURPLE_AIR_SENSOR_INDEX  = *****

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
g_pm25 = -1

# Global to keep the threads looping
keep_on_swimming = True

# Color to show when offline
OFFLINE_COLOR = (0, 0, 255)

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
  [      0.0,     0.0,    0,   0,   0, 128,   0 ],
  [      0.0,    12.1,    0,  50,   0, 128,   0 ],
  [     12.1,    35.5,   51, 100,  64,  64,   0 ],
  [     35.5,    55.5,  101, 150, 192,  64,   0 ],
  [     55.5,   150.5,  151, 200, 192,   0,   0 ],
  [    150.5,   250.5,  201, 300, 192,   0,  16 ],
  [    250.5,   350.5,  301, 400,  24,   0,   4 ],
  [    350.5,   500.5,  401, 500,  24,   0,   4 ],
  [    500.5, 99999.9,  501, 999,  24,   0,   4 ],
  [  99999.9,100000.0,  999,1000,  24,   0,   4 ]
]

# Debug flags
DEBUG_API = False
DEBUG_AQI = False
DEBUG_RGB = False
DEBUG_REQ_THREAD = False
DEBUG_MAIN_LOOP = False
DEBUG_DIMMING = False
DEBUG_SIGNAL = False

# Debug print
def debug(flag, str):
  if flag:
    print(str)

# Invoke the PurpleAir "sensors" API for my sensor with my API key
def get_sensor():
  url = PURPLE_AIR_SENSOR_URL + str(MY_PURPLE_AIR_SENSOR_INDEX)
  headers = {
    PURPLE_AIR_API_KEY_HEADER:MY_PURPLE_AIR_READ_API_KEY,
    'Content-Type':'json'
  }
  debug(DEBUG_API, 'API request: "' + url + '"')
  r = requests.get(url, headers=headers)
  if (200 == r.status_code):
    debug(DEBUG_API, '--> [success]')
  else:
    debug(DEBUG_API, '--> [error] status code: ' + r.status_code)
  return r

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
  if pm25 < 0:
    return OFFLINE_COLOR
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

# Thread that monitors the AQI and updates the 'g_pm25' global accordingly
REQUEST_TIMEOUT_SEC = 30
SLEEP_BETWEEN_AQI_CHECKS_SEC = 15
# How main request failures before setting 'g_pm25' to -1?
FAIL_COUNT_TOLERANCE = 8
class AqiThread(threading.Thread):
  def run(self):
    debug(DEBUG_REQ_THREAD, "AQI monitor thread started!")
    global g_pm25
    fail_count = 0
    while keep_on_swimming:
      try:
        debug(DEBUG_REQ_THREAD, ('REQ: t/o=%d' % (REQUEST_TIMEOUT_SEC)))
        r = get_sensor()
        if 200 == r.status_code:
          debug(DEBUG_REQ_THREAD, '--> [success]')
          fail_count = 0
          j = r.json()
          g_pm25 = float(j['sensor']['pm2.5_atm'])
          aqi = pm25_to_aqi(g_pm25)
          debug(DEBUG_REQ_THREAD, ('*** PM2.5 == %0.1f --> AQI == %d ***' % (g_pm25, aqi)))
        else:
          debug(DEBUG_REQ_THREAD, '--> [error]')
          fail_count += 1
      except requests.exceptions.Timeout:
        debug(DEBUG_REQ_THREAD, '--> [timeout]')
        fail_count += 1
      except:
        debug(DEBUG_REQ_THREAD, '--> [exception]')
        fail_count += 1
      if fail_count > FAIL_COUNT_TOLERANCE:
        g_pm25 = -1
      time.sleep(SLEEP_BETWEEN_AQI_CHECKS_SEC)
    debug(DEBUG_SIGNAL, 'Exited AQI thread.')

# Main program
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
      aqi = pm25_to_aqi(x)
      debug(DEBUG_AQI, ('*** PM2.5 == %0.1f --> AQI == %d ***' % (x, aqi)))

  if DEBUG_RGB:
    debug(DEBUG_RGB, '--> Testing RGB value calculations:')
    for x in range(-15, 350, 5):
      rgb = pm25_to_rgb(x)
      aqi = pm25_to_aqi(x)
      debug(DEBUG_RGB, ('*** PM2.5 == %0.1f --> AQI == %d --> RGB == (%d,%d,%d) ***' % (x, aqi, rgb[0], rgb[1], rgb[2])))
      neopixels.fill(rgb)
      time.sleep(0.5)

  # Start the thread that checks the AQI from the sensor
  aqi_check = AqiThread()
  aqi_check.start()

  # Loop forever checking global PM2.5, computing AQI and setting NeoPixels
  SLEEP_BETWEEN_NEOPIXEL_UPDATES_SEC = 15
  debug(DEBUG_MAIN_LOOP, "Main loop is starting...")
  while keep_on_swimming:
    aqi = pm25_to_aqi(g_pm25)
    rgb = pm25_to_rgb(g_pm25)
    debug(DEBUG_DIMMING, ('      Original:      (%3d,%3d,%3d)' % (rgb[0], rgb[1], rgb[2])))
    # Dim all the normal colors (NeoPixels are very bright!)
    if rgb != OFFLINE_COLOR:
      r = rgb[0]
      g = rgb[1]
      b = rgb[2]
      rgb = (r / 4, g / 4, b / 4)
      debug(DEBUG_DIMMING, ('      Dimmed:        (%3d,%3d,%3d)' % (rgb[0], rgb[1], rgb[2])))
    # Further dim in the evening/night
    now = datetime.now()
    hr = int(now.strftime("%H"))
    if hr < MORNING_HOUR or hr > EVENING_HOUR:
      rgb = (int(rgb[0] / 3), int(rgb[1] / 3), int(rgb[2] / 3))
      debug(DEBUG_DIMMING, ('      Night dimmed:  (%3d,%3d,%3d)' % (rgb[0], rgb[1], rgb[2])))
    neopixels.fill(rgb)
    debug(DEBUG_MAIN_LOOP, ('--> PM2.5 == %0.1f --> AQI == %d --> RGB == (%d,%d,%d) ***' % (g_pm25, aqi, rgb[0], rgb[1], rgb[2])))
    time.sleep(SLEEP_BETWEEN_NEOPIXEL_UPDATES_SEC)

  debug(DEBUG_SIGNAL, 'Exited main thread.')

