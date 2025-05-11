from flask import Flask, render_template_string, Response, redirect, url_for
from gpiozero import LED
import cv2

# Flask setup
app = Flask(__name__)

# Initialize Relay on GPIO18 (was GPIO17 before)
relay = LED(18)

# Use 0 for USB webcam or adjust for Pi Camera
camera = cv2.VideoCapture(0)

# HTML Template (Inline)
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Raspberry Pi Relay & Camera</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 20px; }
        img { width: 640px; height: 480px; border: 2px solid #444; }
        .buttons { margin-top: 20px; }
        button { padding: 10px 20px; font-size: 18px; margin: 5px; }
    </style>
</head>
<body>
    <h1>Relay & Camera Control</h1>
    <img src="{{ url_for('video_feed') }}" alt="Camera Feed">
    <div class="buttons">
        <a href="{{ url_for('relay_on') }}"><button>Relay ON</button></a>
        <a href="{{ url_for('relay_off') }}"><button>Relay OFF</button></a>
    </div>
</body>
</html>
"""

# Video stream generator
def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

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
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

