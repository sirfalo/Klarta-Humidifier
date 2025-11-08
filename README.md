Klarta Humea Grande WiFi – Home Assistant Integration
What is this?
Klarta Humea Grande WiFi custom component brings full control and live sensor monitoring of your Klarta Humea humidifier into Home Assistant. It supports reliable LAN control using a local key and exposes all key device features as Home Assistant entities.

Features:

Turn humidifier ON/OFF

Set target humidity

Monitor current humidity

Control Night Mode (switch)

Monitor temperature sensor

Monitor water level sensor (read-only)

Select Fan Speed (Low, Medium, High) via a select entity

Installation
1. Get Device Info
To use this, you need:

Device ID

Local Key

(Optionally) Device IP and Protocol (3.4)

See Getting Tuya Local Key if unsure.

2. Download/Copy the Files
Copy these files into a new folder /config/custom_components/klarta_humea in your Home Assistant config directory:

__init__.py

manifest.json

config_flow.py

const.py

humidifier.py

switch.py

sensor.py

select.py

device_manager_v5_7_FINAL.py

(File browser, Samba, or File Editor add-on can be used.)

3. Restart Home Assistant
Go to Settings → System → Restart

4. Add Integration
Navigate to Settings → Devices & Services → Add Integration → Search for “Klarta Humea Grande WiFi”.

Enter:

Name for device

Device ID

Local Key

Device IP

Protocol (leave default 3.4 normally)

Save the integration.

How to Use
Main Features
Humidifier (Entity: humidifier.xxx): On/Off, target and current humidity

Fan Speed (select.xxx_fan_speed): Choose Low/Medium/High

Night Mode (switch.xxx_night_mode): Toggle night mode on/off

Power (switch.xxx_power): Quick power toggle

Sensors:

Water Level: sensor.xxx_water_level – “Water_enough” or “Refill”

Temperature: sensor.xxx_temperature – in Celsius

UI Example
In Overview, add the relevant entities to your dashboard:

humidifier.xxx

select.xxx_fan_speed

switch.xxx_night_mode

sensor.xxx_temperature

sensor.xxx_water_level

Use automations and scripts to automate based on humidity, water level, or status.

Troubleshooting
No entities appear?
Double-check Device ID, Local Key, IP address, and protocol. Check Home Assistant logs for errors.

Water level or temperature is missing?
Wait for the device to send updates. Ensure your device is online.

Fan speed or night mode don't respond?
Verify your humidifier supports these functions in the Tuya/Smart Life app.

Credits
Based on TinyTuya and Home Assistant’s custom component guides.
