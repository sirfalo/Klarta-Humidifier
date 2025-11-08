"""Klarta Humea Integration - v4.0 FINAL - Constants"""

# Domain
DOMAIN = "klarta_humea"

# Data Points (DPs)
DP_POWER = "1"
DP_TEMPERATURE = "10"
DP_CURRENT_HUMIDITY = "14"
DP_NIGHT_MODE = "16"
DP_CONSTANT_MODE = "19"
DP_TARGET_HUMIDITY = "101"
DP_WATER_LEVEL = "102"
DP_FAN_MODE = "103"

# Humidity Range
MIN_TARGET_HUMIDITY = 40
MAX_TARGET_HUMIDITY = 75

# Connection Throttle (seconds)
MIN_UPDATE_INTERVAL = 45
KEEP_ALIVE_INTERVAL = 30

# Error Recovery
ERROR_914_THRESHOLD = 2  # Recreate device after 2 Error 914s
TIMEOUT_THRESHOLD = 3    # Recreate device after 3 consecutive timeouts

# Socket Settings
SOCKET_TIMEOUT = 5.0  # seconds
SOCKET_RETRIES = 2
SOCKET_PERSISTENT = True
SOCKET_NODELAY = False
