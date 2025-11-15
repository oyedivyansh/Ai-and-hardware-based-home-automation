🖐️ Gesture-Controlled Home Automation System
Control real-world home appliances using your hand gestures

Python • OpenCV • MediaPipe • Arduino • PySerial

📌 Overview

This project allows you to control home appliances (bulb, fan, socket, buzzer) using hand gestures detected through a webcam.
The system uses:

MediaPipe → Hand Landmarks Detection

OpenCV → Real-time video processing

PySerial → Communicating with Arduino

Arduino → Controls the physical devices

Finger Count Gestures → Each gesture triggers a different device

It is built for old age people, disabled users, and hands-free smart home use.

🚀 Features

✔ Real-time gesture detection (1–5 fingers)
✔ Control 4+ devices using finger-count logic
✔ Smooth, stable performance using debounce logic
✔ Automatic camera & Arduino reconnection handling
✔ One gesture to control all devices
✔ Safe shutdown + resource cleanup
✔ Arduino-ready commands (BULB_ON, FAN_OFF, etc.)

✋ Gesture → Device Mapping
Fingers	Action
1 Finger	Toggle Bulb
2 Fingers	Toggle Socket
3 Fingers	Toggle Buzzer
4 Fingers	Toggle Fan
5 Fingers	Toggle ALL ON/OFF
0 Fingers	Reset gesture counter
🧠 System Architecture
Webcam → OpenCV → MediaPipe → Finger Count Logic → Command Encoder → Arduino → Devices

🛠️ Technologies Used
Software

Python

OpenCV

MediaPipe

PySerial

Hardware

Arduino (UNO/Nano)

Relay Module

Home Appliances (Bulb / Fan / Socket / Buzzer)

📂 Project Structure
gesture-home-automation/
│
├── main.py                # Python gesture recognition + serial communication
├── arduino/
│   ├── automation.ino     # Arduino side code for device control
│
└── README.md              # Documentation

🎯 How It Works

MediaPipe detects 21 hand landmarks.

A custom function counts fingers raised.

Debounce logic prevents unwanted rapid toggling.

Python sends commands to Arduino:

BULB_ON
FAN_OFF
BUZZER_ON


Arduino activates relay modules to control appliances.

🔌 Arduino Command Set

The Python script sends these exact commands:

BULB_ON / BULB_OFF
SOCKET_ON / SOCKET_OFF
BUZZER_ON / BUZZER_OFF
FAN_ON / FAN_OFF


Your Arduino sketch must listen on Serial and toggle relays accordingly.

📸 Screenshots (Optional)

Add these after uploading:

/screenshots/frame.png
/screenshots/gesture_demo.gif

▶️ Run the Project
1️⃣ Install dependencies
pip install opencv-python mediapipe pyserial

2️⃣ Update Arduino Serial Port

Edit this line in main.py:

ARDUINO_PORT = 'COM8'

3️⃣ Run the script
python main.py

4️⃣ Press q anytime to exit.
🧪 Error Handling Built-in

✔ Auto-reopen camera
✔ Handles lost Arduino connection
✔ Checks invalid frames
✔ Graceful shutdown → closes camera + Arduino serial

🔮 Future Enhancements

MQTT / IoT Cloud Support

Voice + Gesture Hybrid Control

Mobile App Dashboard

ESP32 Wireless Version

Integration with Google Home / Alexa
