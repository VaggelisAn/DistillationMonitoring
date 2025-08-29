import time

import random
import socket
import logging
import paho.mqtt.client as mqtt
from os import getenv
from dotenv import load_dotenv

from simulate_sensors import simulate_sensors
from read_sensors import read_sensors, write_led
from predict_quality import ideal_temp_curve, ideal_alcohol_curve, curve_score

from config import PUBLISH_INTERVAL, ALCOHOL_CONVERSION_CONST, BROKER_ADDRESS, BROKER_PORT, MY_TEAM_PASSWORD, DISTILLATION_TIME, STATUS_OK, STATUS_WARNING, QUALITY_THRESHOLD

SIMULATION = 0

LOGGING: str = "console"
LOG_FILE: str = "stats.log"

load_dotenv()

MY_TEAM = socket.gethostname()
MY_TEAM_PASSWORD = MY_TEAM_PASSWORD

if SIMULATION == 0:
	PUBLISH_INTERVAL = PUBLISH_INTERVAL  # default is 60sec
	conversion_const = ALCOHOL_CONVERSION_CONST 
	ideal_temps = ideal_temp_curve()
	ideal_alcohol = ideal_alcohol_curve()
else:
	PUBLISH_INTERVAL = PUBLISH_INTERVAL # defaults is 1sec  

broker_address = BROKER_ADDRESS
broker_port = BROKER_PORT
topic = f"iot/{MY_TEAM}"
client_id = f"client_{random.randint(0, 1000)}"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.username_pw_set(MY_TEAM, MY_TEAM_PASSWORD)

client.connect(broker_address, broker_port)
client.loop_start()

subscriber_data = {}

def config_logging() -> None:
  	logging.basicConfig(
		filename=LOG_FILE,
		filemode='w',
		level=logging.INFO,
		format='%(asctime)s - %(levelname)s - %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S'
)

# - - - Message Handler - - - 
# Handle incoming messages (overall score and status from subscriber)
def on_message(client, userdata, msg):
	global subscriber_data
	received_data = msg.topic.split("/")[-1]
	value = msg.payload.decode()
	if received_data == "overall_score":
		subscriber_data["overall_score"] = float(value)
	elif received_data == "status":
		subscriber_data["status"] = int(value)
	
	if (all(key in subscriber_data for key in ["overall_score", "status"])):
		overall_score = subscriber_data["overall_score"]
		status = subscriber_data["status"]
		if status == STATUS_OK or status == STATUS_WARNING:
			if LOGGING == "console":
				print(f"Overall score = {overall_score:.2f}/10")
				if (status == STATUS_WARNING):
					print(f"Warning: Overall score is below {QUALITY_THRESHOLD}.")
					write_led(HIGH=True) 
				else:
					write_led(HIGH=False)

			else:
				logging.info(f"Overall score = {overall_score:.2f}/10")


def main() -> None:
	config_logging()

	secs_passed = 0
	temperature = []
	alcohol = []
	curr_temperature = 0
	curr_alcohol = 0

	subscriber_data = {}
	try:
		while True:
			if (secs_passed == DISTILLATION_TIME - 1):
				print("Distillation process ended.")
				break  # end of distillation

			client.on_message = on_message

			client.connect(broker_address, broker_port)
			client.subscribe(f"{topic}/#")
			
			# Get readings (either synthetic or real)
			if SIMULATION == 1:
				temperature, alcohol = simulate_sensors(secs_passed)
				curr_temperature = temperature
				curr_alcohol = alcohol

			else:
				curr_temperature, curr_alcohol = read_sensors() # get current readings from sensors
				curr_alcohol = curr_alcohol * conversion_const  # convert to ppm

			# Publish sensor data and log to console/file
			if LOGGING == "console":
				print(f"Temperature = {curr_temperature:.2f}C | Alcohol = {curr_alcohol:.2f}ppm | @ {secs_passed}s")

				client.publish(f"{topic}/temperature", f"{curr_temperature:.2f}")
				client.publish(f"{topic}/alcohol", f"{curr_alcohol:.2f}")
				client.publish(f"{topic}/secs_passed", int(secs_passed))
			else:
				logging.info(f"Temperature value is: {curr_temperature:.2f}")
				logging.info(f"Alcohol value is: {curr_alcohol:.2f}")

			# Sleep until next publish
			time.sleep(PUBLISH_INTERVAL)
			secs_passed = secs_passed + PUBLISH_INTERVAL

	except KeyboardInterrupt:
		if LOGGING == "console":
			print("Received Ctrl+C signal! Bye")
		else:
			logging.info("Received Ctrl+C signal! Bye")

	finally:
		client.loop_stop()  # Stop the background MQTT loop
		client.disconnect()  # Disconnect from the broker

if __name__ == "__main__":
	main()
	exit(0) 