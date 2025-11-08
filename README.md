# 💧 Klarta Humea Grande WiFi – Home Assistant Integration

## 📝 What is this?

**Klarta Humea Grande WiFi** is a custom component for Home Assistant that brings full local control and monitoring of your Klarta Humea humidifier to your smart home. You control power, set target humidity, adjust fan speed, activate night mode, and monitor water level and temperature—**all from your Home Assistant dashboard**.

**Features:**
- 🔌 Turn humidifier ON/OFF
- 🎯 Set target humidity
- 📊 Monitor current humidity
- 🌙 Control Night Mode (switch)
- 🌡️ Monitor temperature sensor
- 💧 Monitor water level (read-only)
- 🌀 Select Fan Speed (Low, Medium, High) via a selector

---

## 📦 Installation

### 1. Get Device Info

Before starting, you’ll need:
- **Device ID**
- **Local Key**
- *(Optional)* Device IP and Protocol (defaults to 3.4)

See the [LocalTuya guide](https://github.com/rospogrigio/localtuya/wiki/How-to-get-Local-Keys-and-Device-IDs) if you don’t know how to get these.

### 2. Copy Files

Place all these files in `/config/custom_components/klarta_humea`:
- `__init__.py`
- `manifest.json`
- `config_flow.py`
- `const.py`
- `humidifier.py`
- `switch.py`
- `sensor.py`
- `select.py`
- `device_manager_v5_7_FINAL.py`

*(Use File Editor add-on, Samba, or File Browser to upload.)*

### 3. Restart Home Assistant

Open **Settings → System → Restart**.

### 4. Add the Integration

Go to **Settings → Devices & Services → Add Integration**. Search for “Klarta Humea Grande WiFi”, fill in your info, and complete setup.

---

## 🛠️ How to Use

### Available Entities

- **Humidifier:**  
  - `humidifier.xxx` – On/Off, target humidity, current humidity

- **Fan Speed:**  
  - `select.xxx_fan_speed` – 🌀 Choose Low/Medium/High

- **Night Mode:**  
  - `switch.xxx_night_mode` – 🌙 On/Off

- **Power:**  
  - `switch.xxx_power` – 🔌 On/Off

- **Sensors:**  
  - `sensor.xxx_temperature` – 🌡️ Current Temp (°C)  
  - `sensor.xxx_water_level` – 💧 Water_enough / Refill

### 💡 Example Lovelace Cards

- **Add these entities to your dashboard for control:**
  - `humidifier.xxx`
  - `select.xxx_fan_speed`
  - `switch.xxx_night_mode`
  - `switch.xxx_power`
  - `sensor.xxx_temperature`
  - `sensor.xxx_water_level`

### ⚙️ Automations & Scripts

- Trigger automations based on humidity, temperature, or water level.
- Use scripts to automatically change fan speed or night mode.

---

## 🆘 Troubleshooting

- **No entities?**  
  Double-check Device ID, Local Key, IP, and Protocol. See Home Assistant logs for errors.
- **Fan speed or night mode doesn’t work?**  
  Ensure your model supports these features in the official app.
- **Water level or temp missing?**  
  Wait for device updates and verify sensor support
