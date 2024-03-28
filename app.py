from flask import Flask, Response, render_template, request
import cv2
import RPi.GPIO as GPIO

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
    </head>
    <body>
        <h1>IoT Camera Stream</h1>
        <img src="/video_feed" width="320" height="240">
        <form id="relayForm" action="/toggle_relay" method="post">
            <button type="submit" name="action" value="on">Turn On Relay</button>
            <button type="submit" name="action" value="off">Turn Off Relay</button>
        </form>
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

