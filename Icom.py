# Icom Rig to CloudLog
# George Smart, M1GEO
# https://www.george-smart.co.uk
# https://github.com/m1geo/Cloudlog-CAT-Scripts
# 14 Nov 2024
#
# This code is a skeleton example. It's not super stable, but does work. No frills.
# Use with caution.

# Icom Serial Settings (Change Comport, Speed and CIV_RIG to match your radio)
ICOM_COM = "COM4"
ICOM_BAUD = 115200
CIV_RIG = b'\x98' # change to match radio CIV hex (IC7610=\x98, IC7300=\x94, IC7100=\x88, etc)
CIV_PC = b'\xE0' # leave alone (\xE0 is the default)

# Your CloudLog Server details
CLOUDLOG_URL = "https://your_web_domain.tld/Cloudlog/index.php/api/radio"
CLOUDLOG_KEY = "clXXXXXXXXXXXXX"
CLOUDLOG_RIG = "Your Radio Name"

import time
import datetime
import requests
import serial

# Mode dictionary from IC7610 CI-V manual
modes = {0:"LSB", 1:"USB", 2:"AM", 3:"CW", 4:"RTTY", 5:"FM", 7:"CW-R", 8:"RTTY-R", 12:"PSK", 17:"PSK-R"}

# Pretty startup message
print("Icom Rig to CloudLog")
print("George Smart, M1GEO")
print("14 Nov 2024")
print("")

# Connect and turn off AI (auto information) - we'll be oldschool and poll for freq/mode
print("Connecting to Icom Rig via Serial")
cat_ser = serial.Serial(ICOM_COM, ICOM_BAUD, timeout=1, rtscts=False, dsrdtr=False) # rts/dtr seems to get ignored? I use as CW key
print(cat_ser.name, cat_ser.baudrate)
print("Connected.")

def flush_uart_rx_buffer():
    # empty anything that's in the buffer before we start
    cat_ser.flush()
    cat_ser.flushInput()
    cat_ser.read_all()

def send_civ_command(command, data=b'', preamble=b''):
    flush_uart_rx_buffer()
    cat_ser.write(preamble + b'\xFE\xFE' + CIV_RIG + CIV_PC + command + data + b'\xFD')
    # If CIV_ECHO is on (on the radio or old CIV cable), then we must empty the buffer of what we sent.
    cat_ser.read_until(expected=b'\xFD')
    # Then read reply
    reply = cat_ser.read_until(expected=b'\xFD')
    return reply

def read_radio_freq():
    data = send_civ_command(b'\x03')
    if data[4] == 3: # if we got a frequency back
        try:
            freq = 0
            freq += 1E1 * ((data[5] >> 4) & 0xF) # Byte 5, Upper Nibble
            freq += 1E0 * (data[5] & 0xF)        # Byte 5, Lower Nibble
            freq += 1E3 * ((data[6] >> 4) & 0xF) # Byte 6, Upper Nibble
            freq += 1E2 * (data[6] & 0xF)        # Byte 6, Lower Nibble
            freq += 1E5 * ((data[7] >> 4) & 0xF) # Byte 7, Upper Nibble
            freq += 1E4 * (data[7] & 0xF)        # Byte 7, Lower Nibble
            freq += 1E7 * ((data[8] >> 4) & 0xF) # Byte 8, Upper Nibble
            freq += 1E6 * (data[8] & 0xF)        # Byte 8, Lower Nibble
            freq += 1E9 * ((data[9] >> 4) & 0xF) # Byte 9, Upper Nibble
            freq += 1E8 * (data[9] & 0xF)        # Byte 9, Lower Nibble
        except:
            freq = -1 # sometimes data changes before the entire frame is sent (like if spinning VFO quickly)
    else:
        freq = -1
    return freq # In Hz

def read_radio_mode():
    data = send_civ_command(b'\x04')
    if data[4] == 4: # if we got a mode back
        intmode = 10 * ((data[5] >> 4) & 0xF) + 1 * (data[5] & 0xF)
        if intmode in modes.keys():
            mode = modes[intmode]
        else:
            mode = "UNK:%u" % intmode
    else:
        mode = -1
    return mode

# Creates JSON payload with key, radio name, freq/mode, etc., and sends to server by post request.
def send_to_cloudlog(ts, freq, mode):
    payload = {
        "key": CLOUDLOG_KEY,
        "radio": CLOUDLOG_RIG,
        "frequency": freq,
        "mode": mode,
        "timestamp": ts,
    }
    response = requests.post(CLOUDLOG_URL, json=payload, timeout=3)
    return response

oldfreq = -1
oldmode = -1
while True:
    # poll for freq/mode
    freq = read_radio_freq()
    mode = read_radio_mode()
    if (mode == -1) or (freq < 0):
        continue # on error, just carry on
    # if changed, print to screen and update server
    if oldfreq != freq or oldmode != mode:
        oldfreq = freq
        oldmode = mode
        timestamp = datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")
        print("%s     Freq %.6f MHz      Mode %s" % (timestamp, freq/1e6, mode))
        clresp = send_to_cloudlog(timestamp, freq, mode)
        if clresp.status_code == 200:
            print("OK")
        else:
            print(clresp)
    time.sleep(1)
