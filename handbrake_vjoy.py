# -*- coding: utf-8 -*-
import serial
import pyvjoy
import serial.tools.list_ports

PORT     = "COM4"
BAUD     = 115200
RAW_MIN  = 50       # valeur brute levier relâché  -> calibrer
RAW_MAX  = 970      # valeur brute levier tiré     -> calibrer
VJOY_ID  = 4        # device vJoy #4

j = pyvjoy.VJoyDevice(VJOY_ID)

print(f"Connexion sur {PORT}...")
ser = serial.Serial(PORT, BAUD, timeout=1)
print("OK — lecture capteur Hall (Ctrl+C pour quitter)\n")

try:
    while True:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line.isdigit():
            continue
        raw = int(line)
        val = max(0, min(raw - RAW_MIN, RAW_MAX - RAW_MIN))
        axis = int(val / (RAW_MAX - RAW_MIN) * 32767)
        j.data.wAxisZ = axis
        j.update()
        print(f"  raw={raw}  axis={axis}", end="\r")
except KeyboardInterrupt:
    print("\nArrêt.")
finally:
    ser.close()
