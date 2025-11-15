import cv2
import mediapipe as mp
import serial
import time

# --- Configuration Section ---
# ⚠ IMPORTANT: Change 'COM9' to your Arduino's serial port
ARDUINO_PORT = 'COM8'
BAUD_RATE = 9600
CAMERA_INDEX = 0# 0 for default camera, try 1 or 2 if 0 doesn't work
DEBOUNCE_TIME = 0.7 # Time in seconds to wait before processing the same gesture again/q

# --- Arduino Serial Setup ---
arduino = None # Initialize to None
try:
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1) # timeout for non-blocking read
    time.sleep(2) # Allow Arduino to reset
    print(f"Connected to Arduino on {ARDUINO_PORT}")
except serial.SerialException as e:
    print(f"Error: Could not connect to Arduino on {ARDUINO_PORT}. Please check port and connection.")
    print(f"Details: {e}")
    exit() # Exit if Arduino connection fails

# --- MediaPipe Setup ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=1, # Detect only one hand
    min_detection_confidence=0.65,
    min_tracking_confidence=0.65
)

# --- Camera Setup ---
cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    print(f"Error: Could not open camera at index {CAMERA_INDEX}. "
          "Please check if camera is connected, not in use by another app, or try a different CAMERA_INDEX.")
    arduino.close() # Ensure Arduino connection is closed
    exit()
print("System Started... Displaying camera feed.")

# --- Finger Counting Function ---
def count_fingers(hand_landmarks):
    tip_ids = [4, 8, 12, 16, 20] # IDs for the tips of the thumb, index, middle, ring, pinky fingers
    fingers = []

    # Thumb check (specific to right hand usually: tip_x < base_x)
    # This logic assumes a right hand being shown. For left hand, it would be opposite.
    # For a robust solution, you might need to determine hand orientation first.
    # For now, let's keep it as-is for simplicity with a common right-hand gesture.
    if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0] - 1].x:
        fingers.append(1) # Thumb is up
    else:
        fingers.append(0) # Thumb is down

    # Other 4 fingers (index, middle, ring, pinky)
    # Check if the tip landmark (e.g., 8 for index) is above its knuckle landmark (e.g., 6)
    for id in range(1, 5): # Iterate through index, middle, ring, pinky
        if hand_landmarks.landmark[tip_ids[id]].y < hand_landmarks.landmark[tip_ids[id] - 2].y:
            fingers.append(1) # Finger is up
        else:
            fingers.append(0) # Finger is down
            
    return fingers.count(1) # Return the total count of fingers that are up

# --- Device States (Global variables to keep track of current state) ---
# These are used for toggling functionality in the Python script
bulb1_state = False  # Corresponds to Arduino's 'bulb' on pin 9
socket_state = False # Corresponds to Arduino's 'socket' on pin 7 (your former bulb2)
fan_state = False    # Corresponds to Arduino's 'fan' on pin 8 (your former motor)
buzzer_state = False # Corresponds to Arduino's 'buzzer' on pin 10
all_state = False    # State for the 'ALL ON/OFF' command

# --- Debounce Variables ---
last_finger_count = 0 # Stores the finger count from the last time a command was sent
last_time_triggered = 0 # Stores the timestamp of the last command sent

# --- Main Program Loop ---
try:
    while True:
        success, img = cap.read() # Read a frame from the camera
        if not success:
            print("Warning: Ignoring empty camera frame (or stream ended).")
            # Try to re-open camera if it got disconnected
            if not cap.isOpened():
                cap = cv2.VideoCapture(CAMERA_INDEX)
                if not cap.isOpened():
                    print("Error: Camera lost and could not be re-opened.")
                    break # Exit loop if camera can't be restored
            time.sleep(0.1) # Small delay to prevent tight loop on failure
            continue

        img = cv2.flip(img, 1) # Flip image horizontally (mirror effect for selfie view)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Convert BGR to RGB for MediaPipe
        results = hands.process(img_rgb) # Process the image for hand landmarks

        current_finger_count = 0 # Reset finger count for the current frame

        if results.multi_hand_landmarks: # If hands are detected
            for handLms in results.multi_hand_landmarks: # Iterate over detected hands
                mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS) # Draw hand landmarks on the image
                current_finger_count = count_fingers(handLms) # Count fingers using our function

                # Display the current finger count on the video feed
                cv2.putText(img, f"Fingers: {current_finger_count}", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3, cv2.LINE_AA)

                # --- Debounce Logic for Gesture Action ---
                # A command is sent only if:
                # 1. The current finger count is different from the last time we sent a command.
                # 2. Enough time has passed since the last command was sent (to prevent rapid flickering).
                if current_finger_count != last_finger_count and (time.time() - last_time_triggered) > DEBOUNCE_TIME:
                    last_time_triggered = time.time() # Update the timestamp of this action
                    
                    # ---------- Device Toggle Logic Based on Finger Count ----------
                    if current_finger_count == 1:
                        bulb1_state = not bulb1_state
                        cmd = "BULB_ON\n" if bulb1_state else "BULB_OFF\n" # Command for Bulb (pin 9)
                        arduino.write(cmd.encode()) # Encode string to bytes and send
                        print(f"Bulb : {'ON' if bulb1_state else 'OFF'}")

                    elif current_finger_count == 2:
                        socket_state = not socket_state
                        cmd = "SOCKET_ON\n" if socket_state else "SOCKET_OFF\n" # Command for Socket (pin 7)
                        arduino.write(cmd.encode())
                        print(f"(Socket): {'ON' if socket_state else 'OFF'}")

                    elif current_finger_count == 3:
                        buzzer_state = not buzzer_state
                        cmd = "BUZZER_ON\n" if buzzer_state else "BUZZER_OFF\n" # Command for Buzzer (pin 10)
                        arduino.write(cmd.encode())
                        print(f"Buzzer: {'ON' if buzzer_state else 'OFF'}")

                    elif current_finger_count == 4:
                        fan_state = not fan_state
                        cmd = "FAN_ON\n" if fan_state else "FAN_OFF\n" # Command for Fan (pin 8)
                        arduino.write(cmd.encode())
                        print(f"Fan: {'ON' if fan_state else 'OFF'}")

                    elif current_finger_count == 5:
                        all_state = not all_state
                        if all_state:
                            # Send ON commands for all devices
                            arduino.write(b"BULB_ON\n")
                            arduino.write(b"SOCKET_ON\n")
                            arduino.write(b"BUZZER_ON\n")
                            arduino.write(b"FAN_ON\n")
                            print("ALL DEVICES: ON")
                            # Update individual states to reflect 'ALL ON'
                            bulb1_state = True
                            socket_state = True
                            buzzer_state = True
                            fan_state = True
                        else:
                            # Send OFF commands for all devices
                            arduino.write(b"BULB_OFF\n")
                            arduino.write(b"SOCKET_OFF\n")
                            arduino.write(b"BUZZER_OFF\n")
                            arduino.write(b"FAN_OFF\n")
                            print("ALL DEVICES: OFF")
                            # Update individual states to reflect 'ALL OFF'
                            bulb1_state = False
                            socket_state = False
                            buzzer_state = False
                            fan_state = False
                            
                    # Update last_finger_count after processing a valid gesture
                    last_finger_count = current_finger_count
                
                # --- Reset last_finger_count if hand is closed (0 fingers) ---
                # This ensures that if you close your hand, the system is ready for a new gesture.
                # Without this, if you close your hand, then open 1 finger, it won't detect it as a 'change'
                # if last_finger_count was, for example, 2.
                if current_finger_count == 0:
                    last_finger_count = 0 # Reset to allow subsequent gesture to be registered

        else: # No hand detected in the frame
            cv2.putText(img, "No hand detected", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3, cv2.LINE_AA)
            # Also reset last_finger_count when no hand is present
            # This makes sure that when a hand reappears, it's considered a new gesture.
            last_finger_count = 0

        cv2.imshow("Gesture Home Automation", img) # Display the processed frame

        if cv2.waitKey(1) & 0xFF == ord('q'): # Press 'q' key to exit the loop
            break

except Exception as e:
    print(f"\nAn unexpected error occurred during the main loop: {e}")

finally:
    # --- Cleanup Section ---
    print("\nShutting down system...")
    if cap.isOpened():
        cap.release() # Release the camera resource
    cv2.destroyAllWindows() # Close all OpenCV windows
    if arduino and arduino.is_open:
        arduino.close() # Close the serial connection to Arduino
    print("Resources released. System shut down successfully.")
