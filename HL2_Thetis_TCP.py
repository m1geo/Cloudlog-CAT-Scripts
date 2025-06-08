# HL2 Thetis to CloudLog
# George Smart, M1GEO
# https://www.george-smart.co.uk
# https://github.com/m1geo/Cloudlog-CAT-Scripts
# 08 June 2025
#
# This code is a skeleton example. It's not super stable, but does work. No frills.
# Use with caution.

# Thetis CAT on localhost:13013 TCP (See Thetis CAT application settings)
# Use "PowerSDR" as CAT transceiver emulation
SDR_IP = "localhost"
SDR_PORT = 13013

# Your CloudLog Server details
CLOUDLOG_URL = "https://www.george-smart.co.uk/Cloudlog/index.php/api/radio"
CLOUDLOG_KEY = "cl668f1b449aae0"
CLOUDLOG_RIG = "Hermes-Lite 2 (Shack)"

import time
import datetime
import socket
import requests

# Mode dict from PowerSDR CAT Datasheet ("MD;" cmd)
modes = {1:"LSB", 2:"USB", 3:"CW", 4:"FM", 5:"AM", 6:"DIGL", 9:"DIGU"}

# Pretty startup message
print("Thetis SDR for HL2 to CloudLog")
print("George Smart, M1GEO")
print("08 June 2025")
print("")

# Connect and turn off AI (auto information) - we'll be oldschool and poll for freq/mode
print("Connecting to Thetis")
cat_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cat_skt.connect((SDR_IP, SDR_PORT))
time.sleep(0.1)
data = cat_skt.recv(512).decode()
print("CAT Server Info: '%s'" % data)
print("Connected.")

def read_radio_freq():
    cat_skt.send(bytes("FA;", 'ASCII'))
    data = cat_skt.recv(512)
    freq_data = data.decode()[2:][:-1]
    if "?" in freq_data or len(freq_data) == 0:
        print("Couldn't pass frequency data from: '%s'" % freq_data)
        return 0.0
    freq = int(freq_data) # this is fragile, but good enough
    return freq

def read_radio_mode():
    cat_skt.send(bytes("MD;", 'ASCII'))
    data = cat_skt.recv(512)
    mode_data = data.decode()[2:][:-1]
    if "?" in mode_data or len(mode_data) == 0:
        return ("UNK:%s" % mode_data)
    mode_int = int(mode_data) # this is fragile, but good enough
    try:
        mode_str = modes[mode_int]
    except:
        mode_str = ("UNK:%u" % mode_int)
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
    timestamp = datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")
    #print("%s     Freq %.6f MHz      Mode %s" % (timestamp, freq/1e6, mode))
    # if changed, print to screen and update server
    if oldfreq != freq or oldmode != mode:
        oldfreq = freq
        oldmode = mode
        print("%s     Freq %.6f MHz      Mode %s" % (timestamp, freq/1e6, mode))
        clresp = send_to_cloudlog(timestamp, freq, mode)
        if clresp.status_code == 200:
            print("OK")
        else:
            print(clresp)
    time.sleep(1)