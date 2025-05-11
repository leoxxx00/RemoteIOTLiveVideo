from flask import Flask, render_template_string, Response, redirect, url_for
from gpiozero import LED
import cv2
import threading
import time

# Flask app setup
app = Flask(__name__)

# Initialize Relay on GPIO18
relay = LED(18)

# Open the camera with V4L2 for better performance on Linux (Raspberry Pi)
camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

# Check if camera opened successfully
if not camera.isOpened():
    raise RuntimeError("❌ Cannot open camera")

# Set resolution and reduce buffering
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
camera.set(cv2.CAP_PROP_FPS, 30)
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Shared frame and lock
lock = threading.Lock()
current_frame = None

# Background thread to continuously grab the latest frame
def capture_frames():
    global current_frame
    while True:
        camera.grab()  # Grab latest frame
        success, frame = camera.retrieve()  # Decode latest frame
        if success:
            with lock:
                current_frame = frame
        else:
            time.sleep(0.1)  # If fail, avoid CPU overuse

# Start background capture thread
t = threading.Thread(target=capture_frames, daemon=True)
t.start()

# HTML Template for UI
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Raspberry Pi Relay & Camera</title>
    <meta http-equiv="Cache-Control" content="no-store" />
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 20px; }
        img { width: 640px; height: 480px; border: 2px solid #444; }
        .buttons { margin-top: 20px; }
        button { padding: 10px 20px; font-size: 18px; margin: 5px; }
    </style>
</head>
<body>
    <h1>Relay & Live Camera Control</h1>
    <img src="{{ url_for('video_feed') }}" alt="Camera Feed">
    <div class="buttons">
        <a href="{{ url_for('relay_on') }}"><button>Relay ON</button></a>
        <a href="{{ url_for('relay_off') }}"><button>Relay OFF</button></a>
    </div>
</body>
</html>
"""

# Frame generator for MJPEG stream
def generate_frames():
    global current_frame
    while True:
        with lock:
            if current_frame is None:
                continue
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', current_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            frame_bytes = buffer.tobytes()
        # Yield in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Flask routes
@app.route('/')
def index():
    return render_template_string(html_template)

@app.route('/relay/on')
def relay_on():
    relay.on()
    return redirect(url_for('index'))

@app.route('/relay/off')
def relay_off():
    relay.off()
    return redirect(url_for('index'))

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Start the Flask app
if __name__ == '__main__':
    print("✅ Flask app running. Visit http://<raspberry-pi-ip>:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
