import time
import predict_quality 
import numpy as np
import matplotlib.pyplot as plt

SIMULATION = 1
secs_passed = 0

ideal_temps = predict_quality.ideal_temp_curve()
ideal_alcohol = predict_quality.ideal_alcohol_curve()

# ----- Read Sensors -----
def simulate_sensors(secs_passed):
    global ideal_alcohol, ideal_temps
    # synthetic noisy sensor data
    temperature = (ideal_temps + np.random.normal(0, 2, size=ideal_temps.shape))[secs_passed]  # +-2C noise
    mq3_raw = (ideal_alcohol * 0.95)[secs_passed]
    return (temperature, mq3_raw)

# ----- Main Loop -----
if __name__ == "__main__":
    DISTILLATION_TIME = 300
    SAMPLE_INTERVAL = 1
    secs_passed = 0
    
    # histories
    temperature_history = []
    alcohol_history = []
    score_history = []

    ideal_temps = predict_quality.ideal_temp_curve()
    ideal_alcohol = predict_quality.ideal_alcohol_curve()

    while secs_passed < DISTILLATION_TIME:
        temperature_s, alcohol_s = simulate_sensors()

        print(f"temperature = {temperature_s:.2f}, alcohol = {int(alcohol_s)}, time = {secs_passed}s")
        
        temperature_history.append(temperature_s)
        alcohol_history.append(alcohol_s)

        temp_score = predict_quality.curve_score(
            temperature_history, ideal_temps, value_range=80, time=secs_passed
        )
        alc_score = predict_quality.curve_score(
            alcohol_history, ideal_alcohol, value_range=2000, time=secs_passed
        )
        overall_score = (temp_score + alc_score) / 2
        score_history.append(overall_score)

        print(f"Temperature curve score: {temp_score:.2f}/10")
        print(f"Alcohol curve score:     {alc_score:.2f}/10")
        print(f"Overall score (avg):     {overall_score:.2f}/10")

        time.sleep(SAMPLE_INTERVAL)
        secs_passed += 1
