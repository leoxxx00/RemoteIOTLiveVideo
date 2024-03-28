from flask import Flask, Response, request
import cv2
import RPi.GPIO as GPIO
import time

app = Flask(__name__)

# Set up GPIO
RELAY_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Function to toggle the relay
def toggle_relay(state):
    GPIO.output(RELAY_PIN, state)

# Function to capture video from the camera
def generate_frames():
    camera = cv2.VideoCapture(0) # Use 0 for the default camera. You can change this if you have multiple cameras.
    
    # Set desired width and height for resizing
    width, height = 320, 240
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Resize the frame
            frame = cv2.resize(frame, (width, height))
            
            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            # Yield the frame in byte format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    camera.release()

# Route to serve video stream
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Main route to render HTML page
@app.route('/')
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IoT Camera Stream</title>
    <style>
        body {
            font-family: 'Courier New', Courier, monospace;
            background-color: #000;
            color: #0f0;
            margin: 0;
            padding: 0;
        }

        h1 {
            color: #0f0;
            text-align: center;
            margin-top: 20px;
        }

        #stream-container {
            text-align: center;
            margin-top: 20px;
        }

        #video-stream {
            width: 320px;
            height: 240px;
            border: 2px solid #0f0;
            border-radius: 5px;
            display: block;
            margin: 0 auto;
        }

        #button-container {
            text-align: center;
            margin-top: 20px;
        }

        button {
            background-color: #0f0;
            color: #000;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            margin: 0 10px;
        }

        button:hover {
            background-color: #080;
        }

        #time {
            text-align: center;
            margin-top: 20px;
            font-size: 18px;
            color: #0f0;
        }
    </style>
    <script>
        function updateTime() {
            var now = new Date();
            document.getElementById('time').innerHTML = now.toLocaleString();
        }

        setInterval(updateTime, 1000); // Update time every second
    </script>
</head>
<body>
    <h1>IoT Camera Stream</h1>
    <div id="stream-container">
        <img id="video-stream" src="/video_feed" alt="Video Stream">
    </div>
    <div id="button-container">
        <form id="relayForm" action="/toggle_relay" method="post">
            <button type="submit" name="action" value="on">Turn On Relay</button>
            <button type="submit" name="action" value="off">Turn Off Relay</button>
        </form>
    </div>
    <div id="time">Fetching time...</div>
</body>
</html>

    """

# Route to handle button press
@app.route('/toggle_relay', methods=['POST'])
def toggle_relay_route():
    if request.form['action'] == 'on':
        toggle_relay(GPIO.HIGH)
    elif request.form['action'] == 'off':
        toggle_relay(GPIO.LOW)
    return '', 204

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

