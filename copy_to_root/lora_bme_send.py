from time import sleep
from sx127x import SX127x
from controller_esp import Controller
import machine
import bme280_i2c_spi
import ujson

#User Configuration-------------------------
lora_parameters = {'frequency': 868E6, 
	'tx_power_level': 20, 'signal_bandwidth': 40E3,
	'spreading_factor': 11, 'coding_rate': 8, 'preamble_length': 8,
	'implicitHeader'  : False, 'sync_word': 0x12, 'enable_CRC': True}

spi_cable_select = 2 #SPI cable select port number

topic='MyDevices/device_007/calib_none/tele/SENSOR' #valid MQTT topic string

deep_sleep=True
sleep_duration = SAMPLE_INTERVAL = 1800 #30 minutes
#--------------------------------------------

controller = Controller()

lora = controller.add_transceiver(
    SX127x(name='LoRa',parameters = lora_parameters),
    pin_id_ss=Controller.PIN_ID_FOR_LORA_SS,
    pin_id_RxDone=Controller.PIN_ID_FOR_LORA_DIO0)

counter = 0
print("LoRa Sender")

spi = machine.SPI(1, baudrate=5000000, polarity=0, phase=0)
cs = machine.Pin(spi_cable_select, machine.Pin.OUT)
cs.on()
try:
	h_bme = bme280_i2c_spi.BME280_I2C_SPI(spi=spi, spi_cs=cs)
	h_bme.set_measurement_settings({
		'filter': bme280_i2c_spi.BME280_FILTER_COEFF_OFF,
		'osr_h':  bme280_i2c_spi.BME280_OVERSAMPLING_1X,
		'osr_p':  bme280_i2c_spi.BME280_OVERSAMPLING_1X,
		'osr_t':  bme280_i2c_spi.BME280_OVERSAMPLING_1X})

	h_bme.set_power_mode(bme280_i2c_spi.BME280_FORCED_MODE)
except:
	h_bme=None
sleep(0.4)
cs.off()

while True:
	A=machine.ADC(0).read()

	if h_bme is not None:
		cs.on()
		data=h_bme.get_measurement()
		h_bme.set_power_mode(bme280_i2c_spi.BME280_FORCED_MODE)
		sleep(0.4)
		cs.off()
		
		mqtt_msg={'topic':topic,
			'payload':{"T":round(data['temperature']*100)/100,"P":data['pressure']/100,"H":data['humidity'],"A":A}}
		mqtt_msg=ujson.dumps(mqtt_msg)
	else:
		mqtt_msg='No BME Found!'


	lora.println(mqtt_msg)
	#lora.sleep() #put lora board into sleep mode (don't know if this works of not yet!)

	if deep_sleep:
		# initialize RTC
		rtc = machine.RTC()
		rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
		print('A very quick sleep to get the message through...')
		sleep(0.1)
		# set RTC.ALARM0 to fire after requested time (waking the device)
		#rtc.alarm(rtc.ALARM0, 300000) # 5 minutes
		rtc.alarm(rtc.ALARM0, SAMPLE_INTERVAL*1000)
		machine.deepsleep()		
	else:
		sleep(sleep_duration)
