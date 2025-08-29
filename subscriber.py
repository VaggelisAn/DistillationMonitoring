import random
import socket
import requests
import paho.mqtt.client as mqtt
from os import getenv
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import matplotlib.pyplot as plt

from config import DB_NAME, BROKER_ADDRESS, BROKER_PORT, MY_TEAM, MY_TEAM_PASSWORD, INFLUXDB_URL, STATUS_OK, STATUS_WARNING, STATUS_HOLD, QUALITY_THRESHOLD, TEMPERATURE_RANGE, ALCOHOL_RANGE
from predict_quality import curve_score, ideal_temp_curve, ideal_alcohol_curve

# Public IP: 194.177.207.38 / Private IP: 10.64.44.156

INFLUXDB_URL = INFLUXDB_URL
MY_TEAM = MY_TEAM
MY_TEAM_PASSWORD = MY_TEAM_PASSWORD

load_dotenv()

db_name = DB_NAME
broker_address = BROKER_ADDRESS
broker_port = BROKER_PORT
topic = f"iot/{MY_TEAM}/#"
client_id = f"client_{random.randint(0, 1000)}"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.username_pw_set(MY_TEAM, MY_TEAM_PASSWORD)

end_device_data = {}
temperature = []
alcohol = []
score = []
ideal_temps = ideal_temp_curve()
ideal_alcohol = ideal_alcohol_curve()

FIRST_READING = True
start_time = 0

def insert_data(db_name, user, password, measurement, value, timestamp=None):
    line = f"{measurement} value={value}"
    if timestamp:
        line += f" {timestamp}"
    response = requests.post(f"{INFLUXDB_URL}/write", 
                                params={"db": db_name},
                                data=line,
                                auth=HTTPBasicAuth(MY_TEAM, MY_TEAM_PASSWORD))
    print("Received and published data:", response.ok)

# - - - Message Handler - - -
# Handle and process incoming messages (temperature, alcohol, secs_passed from end device)
def on_message(client, userdata, msg):
    global end_device_data, FIRST_READING, start_time
    measurement = msg.topic.split("/")[-1]
    value = msg.payload.decode()

    # Receive data from end device 
    if measurement == "temperature":
        end_device_data["temperature"] = float(value)
    elif measurement == "alcohol":
        end_device_data["alcohol"] = float(value)
    elif measurement == "secs_passed":
        end_device_data["secs_passed"] = int(value)
        # Save starting time (check predict_quality to understand why)
        if (FIRST_READING == True):
            start_time = int(value)
            FIRST_READING = False

    # Check if we have all three values
    if all(key in end_device_data for key in ["temperature", "alcohol", "secs_passed"]):
        # Receive current readings from end device
        curr_temperature = end_device_data["temperature"]
        curr_alcohol = end_device_data["alcohol"]
        secs_passed = end_device_data["secs_passed"]

        # Store data to InfluxDB
        insert_data(db_name, MY_TEAM, MY_TEAM_PASSWORD, "temperature", curr_temperature)
        insert_data(db_name, MY_TEAM, MY_TEAM_PASSWORD, "alcohol", curr_alcohol)

        # Update temperature and alcohol histories
        temperature.append(curr_temperature)
        alcohol.append(curr_alcohol)

        # Calculate scores
        temperature_score = curve_score(temperature, ideal_temps, value_range=TEMPERATURE_RANGE, time=secs_passed, start_time=start_time)
        alcohol_score  = curve_score(alcohol, ideal_alcohol, value_range=ALCOHOL_RANGE, time=secs_passed, start_time=start_time)
        overall_score = (temperature_score+alcohol_score)/2

        # Update score history
        score.append(overall_score)

        # Store overall score to InfluxDB and publish to MQTT (to receive from end device)
        insert_data(db_name, MY_TEAM, MY_TEAM_PASSWORD, "overall_score", f"{overall_score:.2f}")
        client.publish(f"iot/{MY_TEAM}/overall_score", f"{overall_score:.2f}")
        if (overall_score < QUALITY_THRESHOLD):
            print(f"Warning: Overall score is below {QUALITY_THRESHOLD}!")
            client.publish(f"iot/{MY_TEAM}/status", int(STATUS_WARNING))
        else:
            client.publish(f"iot/{MY_TEAM}/status", int(STATUS_OK))
        print(f"Overall score = {overall_score:.2f}/10")

        # update live plots
        ax1.clear()
        ax2.clear()
        ax3.clear()

        # Plot actual temperature + ideal
        ax1.plot(temperature, 'r-', label="Actual")
        ax1.plot(ideal_temps[:len(temperature)], 'r--', label="Ideal")
        ax1.set_title("Temperature over time")
        ax1.set_ylabel("Temp (°C)")
        ax1.legend()

        # Plot actual alcohol + ideal
        ax2.plot(alcohol, 'b-', label="Actual")
        ax2.plot(ideal_alcohol[:len(alcohol)], 'b--', label="Ideal")
        ax2.set_title("Alcohol over time")
        ax2.set_ylabel("ppm")
        ax2.legend()

        # Plot score
        ax3.plot(score, 'g-', label="Overall Score")
        ax3.set_title("Overall score over time")
        ax3.set_ylabel("Score (/10)")
        ax3.set_xlabel("Time (s)")
        ax3.legend()

        plt.tight_layout()
        plt.pause(0.01)  # refresh

        # Clear end_device_data to receive new set of data
        end_device_data = {} 
    else:
        # Hold status if not all data received
        client.publish(f"iot/{MY_TEAM}/status", int(STATUS_HOLD))



def main():
    global ax1, ax2, ax3
    try:
        client.on_message = on_message

        client.connect(broker_address, broker_port)
        client.subscribe(topic)

        # --- setup live plot ---
        plt.ion()
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 10))


        print(f"Subscribing to `{topic}`. Waiting for messages...")

        client.loop_forever()
        
    except KeyboardInterrupt:
        print("Receive Ctrl+C signal! Bye")
        client.loop_stop()
        client.disconnect()
        plt.ioff()
        plt.show()


if __name__ == "__main__":
    main()

    exit(0)

