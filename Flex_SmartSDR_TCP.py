# Flex SmartSDR to CloudLog
# George Smart, M1GEO
# https://www.george-smart.co.uk
# https://github.com/m1geo/Cloudlog-CAT-Scripts
# 10 July 2024
#
# This code is a skeleton example. It's not super stable, but does work. No frills.
# Use with caution.

# SmartSDR CAT on localhost:5002 TCP (See SmartSDR CAT application settings)
SMARTSDR_IP = "localhost"
SMARTSDR_PORT = 5002

# Your CloudLog Server details
CLOUDLOG_URL = "https://your_web_domain.tld/Cloudlog/index.php/api/radio"
CLOUDLOG_KEY = "clXXXXXXXXXXXXX"
CLOUDLOG_RIG = "Your Radio Name"

import time
import datetime
import socket
import requests

# Mode dict from SmartSDR CAT Datasheet ("MD;" cmd)
modes = {1:"LSB", 2:"USB", 3:"CW", 4:"FM", 5:"AM", 6:"DIGL", 9:"DIGU"}

# Pretty startup message
print("Flex SmartSDR to CloudLog")
print("George Smart, M1GEO")
print("10 July 2024")
print("")

# Connect and turn off AI (auto information) - we'll be oldschool and poll for freq/mode
print("Connecting to SmartSDR")
cat_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cat_skt.connect((SMARTSDR_IP, SMARTSDR_PORT))
cat_skt.send(bytes("\nAI0;\n", 'ASCII')) # turn off AI
print("Connected.")

def read_radio_freq():
    cat_skt.send(bytes("\nFA;\n", 'ASCII'))
    data = cat_skt.recv(512).decode()
    freq = int(data[2:][:-1]) # this is fragile, but good enough
    return freq

def read_radio_mode():
    cat_skt.send(bytes("\nMD;\n", 'ASCII'))
    data = cat_skt.recv(512)
    mode_int = int(data.decode()[2]) # this is fragile, but good enough
    try:
        mode_str = modes[mode_int]
    except:
        mode_str = ("UNK%u" % mode_int)
    return mode_str

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
    # if changed, print to screen and update server
    if oldfreq != freq or oldmode != mode:
        oldfreq = freq
        oldmode = mode
        timestamp = datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        print("%s     Freq %.6f MHz      Mode %s" % (timestamp, freq/1e6, mode))
        clresp = send_to_cloudlog(timestamp, freq, mode)
        if clresp.status_code == 200:
            print("OK")
        else:
            print(clresp)
    time.sleep(1)