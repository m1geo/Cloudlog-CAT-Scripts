# flrig xmlrpc to CloudLog
# George Smart, M1GEO
# https://www.george-smart.co.uk
# https://github.com/m1geo/Cloudlog-CAT-Scripts
# 07 Aug 2025
#
# This code is a skeleton example. It's not super stable, but does work. No frills.
# Use with caution.

# Your CloudLog Server details
CLOUDLOG_URL = "https://your_web_domain.tld/Cloudlog/index.php/api/radio"
CLOUDLOG_KEY = "clXXXXXXXXXXXXX"
CLOUDLOG_RIG = "Your Radio Name"

import time
import datetime
import requests
import xmlrpc.client

# Pretty startup message
print("Fldigi to CloudLog")
print("George Smart, M1GEO")
print("20 Jul 2025")
print("")

# Connect to FLRig's XML-RPC server
print("Connecting to fldigi xmlrpc")
flrig = xmlrpc.client.ServerProxy("http://localhost:12345")

# List Methods - useful for checking what your radio/flrig support
#meth = flrig.system.listMethods()
#for m in meth:
#    print(m)
#exit(-1)

def read_radio_freq():
    freq = flrig.rig.get_vfo() # maybe get_freq() or simiar?
    freq = float(freq)
    return freq # In Hz

def read_radio_mode():
    mode = flrig.rig.get_mode()
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
