from sx127x import SX127x
from controller_esp import Controller
import ujson as json
from umqttsimple import MQTTClient
global payload_string
payload_string = None

#User Configuration-------------------------
lora_parameters = {'frequency': 868E6, 
	'tx_power_level': 20, 'signal_bandwidth': 40E3,
	'spreading_factor': 11, 'coding_rate': 8, 'preamble_length': 8,
	'implicitHeader'  : False, 'sync_word': 0x12, 'enable_CRC': True}

#MQTT
MQTT_BROKER='192.168.1.13'
LOCATION='lora_relay'
#--------------------------------------------

def on_receive(lora, payload):
    global payload_string
    lora.blink_led()   
            
    try:
        payload_string = payload.decode()
        rssi = lora.packetRssi()
        print("*** Received message ***\n{}".format(payload_string))
        #if config_lora.IS_TTGO_LORA_OLED: lora.show_packet(payload_string, rssi)
        print("with RSSI {}\n".format(rssi))
    except Exception as e:
        print(e)
        payload_string=None

def MQTT_connect(loc, broker, cb=None, topics=None):
	try:
		c=MQTTClient("umqtt_client_"+loc,broker)
		if cb is not None: c.set_callback(cb)
		c.connect()
		if topics is not None:
			for topic in topics:
				c.subscribe(topic)
		return c
	except Exception as e:
		print('MQTT_connect error:',e)
		return None

def write_mqtt_raw(c,topic,payload,retain=False):
	print('MQTT write attempt:',topic, payload)
	try:
		#c.connect()
		c.publish(b""+topic,payload,retain=retain)
		#c.disconnect()
		print('Success!')
		return 0
	except Exception as e:
		print('Error!')
		print(str(e))
		return 1

controller = Controller()
lora = controller.add_transceiver(
    SX127x(name='LoRa',parameters = lora_parameters),
    pin_id_ss=Controller.PIN_ID_FOR_LORA_SS,
    pin_id_RxDone=Controller.PIN_ID_FOR_LORA_DIO0)

lora.onReceive(on_receive)

while True:
	lora.receive()
	#a correct mqtt message will be of the format:
	#{"topic": <valid mqtt topic string>, "payload": {"BME280": {"Pressure": 101501, "Temperature": 22.49, "Humidity": 48.4941}}}
	#try to decode and send as MQTT
	if payload_string is not None:
		print('payload_string:',payload_string)
		try:
			data=json.loads(payload_string)
			topic=data['topic']
			payload=data['payload']
			print('topic:',topic)
			print('payload, type:',payload, type(payload))
			print('payloadj:',json.dumps(payload))
			for i in range(5): #5 attempts to send mqtt message
				try:
					err=write_mqtt_raw(h_mqtt,topic,json.dumps(payload))
					if err==0:
						print('MQTT forwarded on attempt',i+1)
						break
					else:
						raise ValueError('A very specific bad thing happened.')
				except Exception as e: #failed to send mqtt. reset connection
					print('Error message sending on attempt',i+1,':',e)
					h_mqtt = MQTT_connect(LOCATION, MQTT_BROKER, [])
		except Exception as e:
			print('invalid message - could not forward as mqtt.',e)
		payload_string=None