# LORA_esp8266_sensor_and_MQTT_bridge
The limited number of gpio pins on an esp8266 make it a challenge to use as the basis for a LORA sensor. Here's a configuration that leaves just enough ports available for SPI communications, or for interfacing with 1-wire sensors. My setup uses a BME280 sensor (temperature, pressure, humidity), and micropython.

This is purely a sensor(s)-to-MQTT-bridge setup. We won't be doing anything advanced like connecting to a [public LORA network](https://www.thethingsnetwork.org/). For that, you'd need to both interface with additional DIO ports on the LORA module, and find different software: I haven't seen a micropython implementation for this use-case.

## Utilized drivers

sx127x LORA driver originally from https://github.com/Wei1234c/SX127x_driver_for_MicroPython_on_ESP8266, which I [forked and stripped-down](https://github.com/brev-dev/SX127x_driver_for_MicroPython_on_ESP8266) to the bare minimum to keep within esp8266 memory limits.
BME280: https://github.com/brev-dev/micropython_bme280_i2c_spi
MQTT: https://github.com/RuiSantosdotme/ESP-MicroPython/blob/1caad431c59167e0135cad3ae0ec1b19d182bb28/code/MQTT/umqttsimple.py

## Example hardware 
I use this with my [custom sensor board](https://github.com/brev-dev/another_esp8266_sensor_board).

## Wiring

To the LORA module:
| ESP8266 | RFM95W |
| ---| --- |
| gpio5 | DIO0\* |
| gpio12 | MISO |
| gpio13 | MOSI |
| gpio14 | SCK |
| gpio15 | NSS |

\*other DIO ports not needed for this simple application

To the sensor (e.g. BME280 over SPI):
| ESP8266 | BME280 |
| ---| --- |
| gpio12 | MISO (labeled as SDO) |
| gpio13 | MOSI (labeled as SDA) |
| gpio14 | SCK (labeled as SCL) |
| gpio2\* | NSS (labeled as CSB) |

\*the choice of gpio2 for the slave select pin means that the ESP-12F's onboard LED will illuminate when the BME280 is being accessed. That's a reasonable compromise given the lack of available gpio.

Optional:
| ESP8266 |  |
| ---| --- |
| gpio4  | mode switch |
| gpio16 | deep sleep |



## Micropython and drivers



### Making a firmware image
These are incomplete personal notes, derived form information provided at http://www.microdev.it/wp/en/2018/06/25/micropython-micropython-compiling-for-esp8266/.
I use a raspberry pi for the compilation.

```
mkdir ~/Micropython
mkdir ~/Micropython/esp8266
cd ~/Micropython/esp8266
git clone https://github.com/micropython/micropython

#  Cross-compiler stuff (only need to do once)

git clone --recursive  https://github.com/pfalcon/esp-open-sdk

sudo apt-get install make unrar-free autoconf automake libtool gcc g++ gperf flex bison texinfo gawk ncurses-dev libexpat-dev python-dev python python-serial sed git unzip bash help2man wget bzip2 libtool-bin
```

Now need to change some of the code (in the current version) which is doing an incorrect bash version check (see https://github.com/pfalcon/esp-open-sdk/issues/365):

Change line 193 at esp-open-sdk/crosstool-NG/configure.ac
like this:
```
 |$EGREP '^GNU bash, version ([0-9\.]+)')
```

Then back to work...
```
cd esp-open-sdk
make STANDALONE=y |& tee make0.log
```
Back to the firmware itself
```
export PATH=/home/pi/Micropython/esp8266/esp-open-sdk/xtensa-lx106-elf/bin:$PATH
cd ~/Micropython/esp8266/micropython
git submodule update --init

make -C mpy-cross
cd ports/esp8266
make axtls
make
```
The firmware is generated under ports/esp8266/build folder with the name firmware_combined.bin

#### Adding additional files to a firmware image
Put the desired files in micropython/ports/esp8266/modules.

Then from the directory micropython/ports/esp8266, run:
```
make clean
make
```
And finally recompile the firmware as above.

### Flashing the firmware
Use your chosen method to get the esp8266 connected to a PC via UART, and know the UART COM port (e.g., COM3)
I use the python package epstool for flashing (in Windows):
```
pip install esptool
esptool.py --port COM3 --chip esp8266 erase_flash
esptool.py --port COM3 --chip esp8266  write_flash --flash_mode dio --flash_size detect 0x0 <firmware_file>
```
Reset and connect via serial (putty). Then:
```
import initial_setup
```
This command runs the following (which you could do manually):
```
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
```
Now you can access the device via webrepl. Either run a copy of the client [online](https://micropython.org/webrepl/) or copy it locally from https://github.com/micropython/webrepl. The port will be 8266. So access your device at an address in the format ###.###.###.###:8266

### Copy additional files
Through the webrepl interface, you can now copy the needed files from ###.
If this is a sensor, rename main.py.sensor to main.py
If this is a receiver/bridge, rename main.py.mqtt_bridge to main.py


## Radio configuration

A number of radio settings influence the range and reliability of a LORA transceiver pair. A good discussion on the topic can be found at https://medium.com/home-wireless/testing-lora-radios-with-the-limesdr-mini-part-2-37fa481217ff.

The key parameters for us are as follows:
- frequency (defined by your region and hardware): 169E6, 433E6, 434E6, 866E6, 868E6, 915E6
- tx_power_level (default 2): 0 <= x <=14 (or 2 <= x <=17 with boost - I don't understand yet which is active!)
- bandwidth (default 125e3): Set to lower than the required bin value: (7.8E3, 10.4E3, 15.6E3, 20.8E3, 31.25E3, 41.7E3, 62.5E3, 125E3, 250E3)
- spreading_factor (default 8): 6 <= x <= 12
- coding_rate (default 5): 5 <= x <= 8 (true coding rate in the range 1-4 equals this value minus 4)

Respect the fair-use transmission time per sensor. The Semtec "LORA Calculator" tool gives the airtime (and therefore the minimum time between readings) for different radio settings. Or there's an online tool [here](https://loratools.nl/#/airtime).

### Example settings
Here's what I use to maximize range with multiple obstacles. With this, I can reliably get a signal from a sensor in the basement to a receiver four floors above:
- tx_power_level = 20
- signal_bandwidth = 40E3
- spreading_factor = 11
- coding_rate = 8
- preamble_length = 8

### Antenna considerations
Your cheapest/simplest option is an appropriate wire attached to the antenna port on the LORA module. These sometimes come bundled with the modules. This'll work adequately over short ranges, but will limit your maximum range compared to a higher-gain antenna. Given my use-case is pushing the limit (due to obstructions, rather than absolute range), I use something bigger.
