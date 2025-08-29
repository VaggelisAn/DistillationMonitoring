from math import log, e # natural log and e
import numpy as np
from config import DISTILLATION_TIME, STARTING_TEMP, STARTING_ALCOHOL, LOG_COEF, LOG_ARG, EXP_COEF, EXP_ARG

# ----- Ideal curves -----
def ideal_temp_curve(distillation_time=DISTILLATION_TIME, starting_temp=STARTING_TEMP, log_coef=LOG_COEF, log_arg=LOG_ARG):
    t = np.arange(0, distillation_time+1)
    temps = np.zeros_like(t, dtype=float)
    temps[0] = starting_temp
    temps[1:] = log_coef * np.log(log_arg * t[1:])
    return temps

def ideal_alcohol_curve(distillation_time=DISTILLATION_TIME, starting_alcohol=STARTING_ALCOHOL, exp_coef=EXP_COEF, exp_arg=EXP_ARG):
    t = np.arange(0, distillation_time+1)
    alcohols = np.zeros_like(t, dtype=float)
    alcohols[0] = starting_alcohol
    alcohols[1:] = exp_coef * np.e ** (exp_arg * t[1:])
    return alcohols

# ----- Simple scorer -----
# Normal Round Mean Squared Error (RMSE) based scorer
# NRMSE is calculated between candidate and ideal. 
# Value range used for normalization (could also be calculated on call, but this is faster).
# time range and start time allows comparing the candidate against a part (slice in coding terms) of the ideal curve.
def curve_score(candidate, ideal, value_range=80, time=300, start_time=0):
    # Ensure we don’t go beyond array lengths
    end_idx = min(time, len(ideal))
    cand_end_idx = min(time - start_time, len(candidate))

    # Align both arrays to same length
    length = min(cand_end_idx, end_idx - start_time)
    if length <= 0:
        return 0  # no data to compare

    cand_slice = candidate[0:length]
    ideal_slice = ideal[start_time:start_time+length]

    diff = cand_slice - ideal_slice
    rmse = np.sqrt(np.mean(diff**2))
    norm_error = rmse / value_range

    # clip score between 0 and 10
    score = max(0, 10 * (1 - norm_error))
    return score

# ----- Example -----
if __name__ == "__main__":
    ideal_temps = ideal_temp_curve()
    ideal_alc = ideal_alcohol_curve()

    # Make a candidate by changing the ideal slightly
    candidate_temps = ideal_temps + np.random.normal(0, 2, size=ideal_temps.shape)  # +-2C noise
    candidate_alc = ideal_alc * 0.95  # slightly lower alcohol

    temp_score = curve_score(candidate_temps, ideal_temps, value_range=80, time=300)      # 20 - 100
    alc_score  = curve_score(candidate_alc, ideal_alc, value_range=2000, time=300)        # ~2000 - 0

    print(f"Temperature curve score: {temp_score:.2f}/10")
    print(f"Alcohol curve score:     {alc_score:.2f}/10")
    print(f"Overall score (avg):     {(temp_score+alc_score)/2:.2f}/10")