# - - - predict_quality.py - - -

# Constants regarding the default physical values in the distillation process:
DISTILLATION_TIME = 300     # seconds
STARTING_TEMP = 20          # C'
STARTING_ALCOHOL = 2000    # ppm

# Constants regarding the shape of the ideal curves:
# temperature log curve parameters:
LOG_COEF = 13.6            
LOG_ARG = 3.9               
# alcohol exponential curve parameters:
EXP_COEF = 2000       
EXP_ARG = -0.014  

# --------------------------------

# - - - subscriber.py - - - 
# Constants regarding InfluxDB and MQTT broker connection:
INFLUXDB_URL = "http://xxx.xxx.xxx.xxx:xxxx" 
MY_TEAM_PASSWORD = "team_password"
DB_NAME = "team_db"
BROKER_ADDRESS = "xxx.xxx.xxx.xxx"
BROKER_PORT = xxxx
MY_TEAM = "team_name" # raspberry pi should have this name, otherwise change the get_socket() line to match this name in end_device.py

# Status codes:
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_HOLD = 2
QUALITY_THRESHOLD = 5  # threshold for overall score to trigger a warning

# ---------------------------------

# - - - end_device.py - - -
PUBLISH_INTERVAL = 1 # seconds
ALCOHOL_CALIBRATION_CONST = 0.01  # calibration constant for alcohol sensor
ALCOHOL_CONVERSION_CONST = 3.3 * ALCOHOL_CALIBRATION_CONST * 1000000 / 4095 # Convert from raw voltage to ppm
TEMPERATURE_RANGE = 80
ALCOHOL_RANGE = 2000