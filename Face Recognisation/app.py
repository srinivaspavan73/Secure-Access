from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import cv2
import base64
import os
import sys
print(sys.executable)


app = Flask(__name__)
CORS(app)

def load_known_faces(known_faces_dir):
    known_face_encodings = []
    known_face_names = []

    # Group images by person
    face_images = {}
    for filename in os.listdir(known_faces_dir):
        if filename.endswith((".jpg", ".png")):
            person_name = filename.split('_')[0]
            if person_name not in face_images:
                face_images[person_name] = []
            face_images[person_name].append(filename)

    # Process each person's images
    for person_name, filenames in face_images.items():
        person_encodings = []
        for filename in filenames:
            image_path = os.path.join(known_faces_dir, filename)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)

            if encodings:
                person_encodings.extend(encodings)
            else:
                print(f"No face found in image: {filename}")

        # Use the average of encodings for each person (if multiple images are used)
        if person_encodings:
            average_encoding = np.mean(np.array(person_encodings), axis=0)
            known_face_encodings.append(average_encoding)
            known_face_names.append(person_name)

    return known_face_encodings, known_face_names

# Load the known faces at the start of the app
known_faces_dir = 'D:/backend-flask/known_faces'
known_face_encodings, known_face_names = load_known_faces(known_faces_dir)
@app.route('/process-image', methods=['POST'])
def process_image():
    image_data = request.json['image']
    image_data = base64.b64decode(image_data.split(',')[1])
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Find all face encodings and landmarks in the current image
    face_locations = face_recognition.face_locations(rgb_image)
    unknown_face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
    face_landmarks_list = face_recognition.face_landmarks(rgb_image, face_locations)

    names = []
    orientations = []  # Store face orientations
    for index, unknown_face_encoding in enumerate(unknown_face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, unknown_face_encoding, tolerance=0.5)
        name = "Unknown"
        orientation = "Unknown"  # Default orientation
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
            # Once a face is matched, determine its orientation
            orientation = determine_face_orientation(face_landmarks_list[index])
        
        names.append(name)
        orientations.append(orientation)

    # Extend the response to include face orientations
    return jsonify({"message": "Faces processed", "names": names, "orientations": orientations})

def determine_face_orientation(landmarks):
    print("Determining orientation with landmarks:", landmarks)  # Debugging
    # Calculate the average points for each eye
    left_eye_center = np.mean(landmarks['left_eye'], axis=0)
    right_eye_center = np.mean(landmarks['right_eye'], axis=0)
    nose_tip = np.mean(landmarks['nose_tip'], axis=0)

    # Calculate the eye line vector
    eye_line = right_eye_center - left_eye_center
    eye_line_length = np.linalg.norm(eye_line)
    eye_line_angle = np.arctan2(eye_line[1], eye_line[0]) * 180 / np.pi

    # Calculate the nose tip position relative to the eye line
    nose_eye_line_vector = nose_tip - left_eye_center
    nose_position_angle = np.arctan2(nose_eye_line_vector[1], nose_eye_line_vector[0]) * 180 / np.pi

    # Determine orientation based on angles
    orientation = "Front"
    if eye_line_angle > 10:  # Adjust thresholds based on empirical testing
        orientation = "Up"
    elif eye_line_angle < -10:
        orientation = "Down"

    # Determine left or right based on the nose position relative to the eye line
    # This part assumes that a significant horizontal angle difference indicates turning
    angle_difference = nose_position_angle - eye_line_angle
    if angle_difference < -15:  # These thresholds are indicative; adjust after testing
        orientation += " Right"
    elif angle_difference > 15:
        orientation += " Left"

    return orientation

# New endpoint to initiate verification sequence
@app.route('/start-verification', methods=['POST'])
def start_verification():
    # This endpoint could set up a new verification session
    # For simplicity, it just instructs to capture the initial photo
    return jsonify({"message": "Capture photo", "nextStep": "initial"})

@app.route('/verify-orientation', methods=['POST'])
def verify_orientation():
    image_data = request.json['image']
    step = request.json.get('step', 'initial')
    image_data = base64.b64decode(image_data.split(',')[1])
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Detect faces in the image
    face_locations = face_recognition.face_locations(rgb_image)
    if len(face_locations) == 0:
        # No faces detected, return a specific message
        return jsonify({"message": "No person detected. Please ensure the camera is on and try again.", "nextStep": "initial", "instruction": "No person detected"})
    # Placeholder for actual face recognition and orientation verification
    # Here, we simulate progression through steps
    if step == 'initial':
        next_step = 'right'
        instruction = 'Please turn your face to the right side.'
    elif step == 'right':
        next_step = 'left'
        instruction = 'Please turn your face to the left side.'
    elif step == 'left':
        next_step = 'up'
        instruction = 'Please look up.'
    elif step == 'up':
        next_step = 'down'
        instruction = 'Please look down.'
    elif step == 'down':
        next_step = 'completed'
        instruction = 'Verification completed.'
        
    else:
        # Fallback or restart the process
        next_step = 'initial'
        instruction = 'Please start again.'

    return jsonify({"message": "Step completed", "instruction": instruction, "nextStep": next_step})
if __name__ == '__main__':
    app.run(debug=True) 

