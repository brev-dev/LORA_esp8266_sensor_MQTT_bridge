import webrepl_setup

import network
sta_if=network.WLAN(network.STA_IF)
ap_if=network.WLAN(network.AP_IF)
sta_if.active()
ap_if.active()
sta_if.active(True)
ap_if.active(False)
sta_if.connect('dd-wrt','freshjade659')
sta_if.isconnected()
sta_if.ifconfig()

import time
time.sleep(6)

import machine
machine.reset()
