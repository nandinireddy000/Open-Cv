from flask import Flask, render_template, Response, jsonify
import cv2
from parking_detector import ParkingDetector
from database_manager import DatabaseManager
import os

app = Flask(__name__)

# Initialize dependencies
db_manager = DatabaseManager()
detector = ParkingDetector(pos_file='source/CarParkPos.txt', db_manager=db_manager)

# Video capture
cap = cv2.VideoCapture('source/carPark.mp4')

def generate_frames():
    global cap
    while True:
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
        success, img = cap.read()
        if not success:
            break
            
        img, _ = detector.process_frame(img)
        
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/slots')
def api_slots():
    slots = db_manager.get_all_slots()
    return jsonify(slots)

@app.route('/api/history')
def api_history():
    history = db_manager.get_history()
    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
