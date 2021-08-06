# LORA_esp8266_sensor_and_MQTT_bridge
The limited number of gpio pins on an esp8266 make it a challenge to use as the basis for a LORA sensor. Here's a configuration that leaves just enough ports available for SPI communications, or for interfacing with other simple sensors. My setup uses a BME280 (temperature, pressure, humidity) sensor, and micropython.

This is purely a sensor(s)-to-MQTT-bridge setup. We won't be doing anything advanced like connecting to a [public LORA network](https://www.thethingsnetwork.org/). For that, you'd both need to interface with additional DIO ports on the LORA module, and require different software: I haven't seen a micropython implementation for this use-case.

## Example hardware 
(links will inevitably expire over time)
You can find an example of a complete circuitboard layout in 

iring

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
| ESP-12F | BME280 |
| ---| --- |
| gpio12 | MISO (labeled as SDO) |
| gpio13 | MOSI (labeled as SDA) |
| gpio14 | SCK (labeled as SCL) |
| gpio2\* | NSS (labeled as CSB) |

\*the choice of gpio2 for the slave select pin means that the ESP-12F's onboard LED will illuminate when the BME280 is being accessed. That's a reasonable compromise given the lack of available gpio.

Optional:
| ESP-12F |  |
| ---| --- |
| gpio4  | mode switch |
| gpio16 | deep sleep |



## Micropython and drivers



## Radio configuration

A number of radio settings influence the range and reliability of a LORA transceiver pair. [Here's](https://medium.com/home-wireless/testing-lora-radios-with-the-limesdr-mini-part-2-37fa481217ff) a good discussion on the topic.

The key parameters for us are as follows:
- frequency (defined by your region and hardware): 169E6, 433E6, 434E6, 866E6, 868E6, 915E6
- tx_power_level (default 2): 0 <= x <=14 (or 2 <= x <=17 with boost - I don't understand yet which is active!)
- bandwidth (default 125e3): Set to lower than the required bin value: (7.8E3, 10.4E3, 15.6E3, 20.8E3, 31.25E3, 41.7E3, 62.5E3, 125E3, 250E3)
- spreading_factor (default 8): 6 <= x <= 12
- coding_rate (default 5): 5 <= x <= 8 (true coding rate in the range 1-4 equals this value minus 4)

Respect the fair-use transmission time per sensor of 30 seconds per day. The Semtec "LORA Calculator" tool gives the airtime (and therefore the minimum time between readings) for different radio settings. Or there's an online tool [here](https://loratools.nl/#/airtime).

### Example settings
Here's what I use to maximize range with multiple obstacles. With this, I can reliably get a signal from a sensor in the basement to a receiver four floors above:
- tx_power_level = 20
- signal_bandwidth = 40E3
- spreading_factor = 11
- coding_rate = 8
- preamble_length = 8

### Antenna considerations
Your cheapest/simplest option is an appropriate wire attached to the antenna port on the LORA module. These sometimes come bundled with the modules. This'll work adequately over short ranges, but will limit your maximum range compared to a higher-gain antenna. Given my use-case is pushing the limit (due to obstructions, rather than absolute range), I use something bigger.
