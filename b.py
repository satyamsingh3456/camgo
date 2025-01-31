from flask import Flask, render_template, Response, request, send_file
import cv2
import time
import os
import threading
import atexit

# Initialize the Flask app
app = Flask(__name__)

# Initialize file names and timestamps
timestamp = time.strftime("%Y%m%d-%H%M%S")
filename = f"output_video_{timestamp}.avi"

# File already not exist
while os.path.exists(filename):
    timestamp = time.strftime("%Y%m%d-%H%S")
    filename = f"output_video_{timestamp}.avi"

# Video recording settings
recording = False

def start_recording():
    global recording, filename
    # Create a VideoWriter object to save video
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

    print("Recording video...")

    # Record video in a loop and write frames to video file
    cap = cv2.VideoCapture(0)  # Start with the back camera

    while recording:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Write the frame to the video file
        out.write(frame)

    # Stop video recording
    cap.release()
    out.release()

    print(f"Video saved as {filename}")
    return filename

@app.route('/start_recording', methods=['POST'])
def start_recording_route():
    global recording
    if not recording:
        recording = True
        threading.Thread(target=start_recording).start()
        return "Recording Started", 200
    return "Already Recording", 400

@app.route('/stop_recording', methods=['POST'])
def stop_recording_route():
    global recording
    recording = False
    return "Recording Stopped", 200

@app.route('/download_video')
def download_video():
    video_file = f"output_video_{timestamp}.avi"
    if os.path.exists(video_file):
        return send_file(video_file, as_attachment=True)
    return "File not found", 404

@app.route('/video_feed')
def video_feed():
    def gen_frames():
        cap = cv2.VideoCapture(0)  # Back camera by default
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # Encode frame as JPEG and return it to the browser as a byte stream
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        cap.release()

    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

# Register a function to clean up and stop recording when the application shuts down
atexit.register(lambda: stop_recording())

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)  # Set use_reloader=False to avoid thread duplication issues
