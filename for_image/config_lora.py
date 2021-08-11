from machine import unique_id
from time import ticks_ms
from ubinascii import hexlify

IS_ESP8266 = True
IS_ESP32 = False
IS_MICROPYTHON = True

def mac2eui(mac):
    mac = mac[0:6] + 'fffe' + mac[6:]
    return hex(int(mac[0:2], 16) ^ 2)[2:] + mac[2:]

uuid = hexlify(unique_id()).decode()

if IS_ESP8266:
    NODE_NAME = 'ESP8266_'
if IS_ESP32:
    NODE_NAME = 'ESP32_'

NODE_EUI = mac2eui(uuid)
NODE_NAME = NODE_NAME + uuid

millisecond = ticks_ms

# Controller
SOFT_SPI = None
from controller_esp import Controller


