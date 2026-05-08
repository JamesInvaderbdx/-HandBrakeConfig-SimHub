import serial
import serial.tools.list_ports
import pyvjoy
import time
import sys

def find_arduino():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if 'CH340' in p.description or 'Arduino' in p.description or 'USB-SERIAL' in p.description.upper():
            return p.device
    return None

port = find_arduino()
if not port:
    print("Arduino non détecté. Ports disponibles :")
    for p in serial.tools.list_ports.comports():
        print(f"  {p.device} — {p.description}")
    sys.exit(1)

print(f"Arduino trouvé sur {port}")

j = pyvjoy.VJoyDevice(1)
ser = serial.Serial(port, 115200, timeout=1)
time.sleep(2)  # attente reset Arduino

print("Lecture en cours... Ctrl+C pour stopper")

try:
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) != 3:
            continue
        x, y, btn = int(parts[0]), int(parts[1]), int(parts[2])
        j.data.wAxisX = int(x * 32767 / 1023)
        j.data.wAxisY = int(y * 32767 / 1023)
        j.data.lButtons = btn
        j.update()
except KeyboardInterrupt:
    print("Arrêt.")
    ser.close()
