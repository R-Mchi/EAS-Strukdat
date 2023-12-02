import cv2
import mediapipe as mp
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

#SCALE = 0.1223021582733813  # Skala konversi dari piksel ke cm

tinggi_badan = float(input("Masukkan tinggi badan: "))

user_choice = input("Tekan 'c' untuk kamera atau 'f' untuk file video: ").lower()

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
if user_choice == 'f':  
    path_to_file = 'Fikra.mp4'
    cap = cv2.VideoCapture(path_to_file)
elif user_choice == 'c':
    cap = cv2.VideoCapture(0)

reference_left_coords = None
reference_right_coords = None
reference_left_foot = None
reference_right_foot = None
jump_start_frame = None
jump_end_frame = None
max_jump_height = 0
max_jump_time = 0
deteksi_awal = True
height_pixel = None

jump_heights = []
jump_durations = []

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (720, 1280))
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    results = pose.process(frame_rgb)
    if deteksi_awal:
        nose_landmark = results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
        right_ankle_landmark = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE]
        left_ankle_landmark = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE]
        nose_y = int(nose_landmark.y * frame.shape[0])
        heel_y = int(left_ankle_landmark.y * frame.shape[0])
        
        jarak_heel_x = abs(right_ankle_landmark.x - left_ankle_landmark.x) * frame.shape[1]
        jarak_heel_y = abs(right_ankle_landmark.y - left_ankle_landmark.y) * frame.shape[0]
        jarak_heel =((jarak_heel_x**2 + jarak_heel_y**2)**0.5)/2

        hypotenusa = abs(heel_y - nose_y)

        height_pixel = (hypotenusa**2 - jarak_heel**2)**0.5

        #height_pixel = abs(heel_y - nose_y)
        SCALE = (tinggi_badan/height_pixel)/2.53
        print(SCALE)
        deteksi_awal = False

        

    if results.pose_landmarks:
        left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER] 
        left_foot_index = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_FOOT_INDEX]
        right_foot_index = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX]

        left_foot_coords = (int(left_foot_index.x * frame.shape[1]), int(left_foot_index.y * frame.shape[0]))
        right_foot_coords = (int(right_foot_index.x * frame.shape[1]), int(right_foot_index.y * frame.shape[0]))
        
        
        left_coords = (int(left_shoulder.x * frame.shape[1]), int(left_shoulder.y * frame.shape[0]))
        right_coords = (int(right_shoulder.x * frame.shape[1]), int(right_shoulder.y * frame.shape[0]))
    
        cm_distance=0
        jump_duration=0

        if reference_left_coords is None or reference_right_coords is None:
            reference_left_coords = left_coords
            reference_right_coords = right_coords
        else:
            reference_mid = ((reference_left_coords[0] + reference_right_coords[0]) // 2, 
                             (reference_left_coords[1] + reference_right_coords[1]) // 2)
            current_mid = ((left_coords[0] + right_coords[0]) // 2, 
                           (left_coords[1] + right_coords[1]) // 2)

            cv2.line(frame, reference_left_coords, reference_right_coords, (255, 0, 0), 2)
            cv2.line(frame, reference_mid, current_mid, (0, 0, 255), 2)
            
            pixel_distance = abs(reference_mid[1] - current_mid[1])
            cm_distance = pixel_distance * SCALE
            label = f"{cm_distance:.2f} cm"
            cv2.putText(frame, label, (current_mid[0] + 10, (reference_mid[1] + current_mid[1]) // 2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
        if reference_left_foot is None or reference_right_foot is None:
                reference_left_foot = left_foot_coords
                reference_right_foot = right_foot_coords
                jump_start_frame = None
                jump_end_frame = None
        else:
            # Check if both feet are off the ground
            if (left_foot_coords[1] < reference_left_foot[1] and right_foot_coords[1] < reference_right_foot[1]) and jump_start_frame is None:
                jump_start_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)  # Get the current frame number

            # Check if feet have returned to the ground
            if jump_start_frame is not None and (left_foot_coords[1] >= reference_left_foot[1] and right_foot_coords[1] >= reference_right_foot[1]):
                jump_end_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)  # Get the current frame number
                jump_duration = (jump_end_frame - jump_start_frame) / cap.get(cv2.CAP_PROP_FPS)  # Calculate jump duration in seconds
                jump_start_frame = None  # Reset jump start frame for the next jump
                jump_durations.append(jump_duration)

        jump_heights.append(jump_duration)
        if jump_duration > max_jump_time:
            max_jump_time = jump_duration

        cv2.putText(frame, f"Jump Duration: {max_jump_time:.2f} sec", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        jump_heights.append(cm_distance)
        if cm_distance > max_jump_height:
            max_jump_height = cm_distance
        
        cv2.putText(frame, f"Max Jump Height: {max_jump_height:.2f} cm", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.line(frame, left_coords, right_coords, (0, 255, 0), 2)

    cv2.imshow('MediaPipe Pose Detection with Reference Line', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break   

cap.release()

peaks, _ = find_peaks(jump_heights)
peak_heights = np.array(jump_heights)[peaks]
#plt.plot(jump_heights)
plt.plot(peaks, peak_heights, marker='o', linestyle='-', color='r')
#for i, peak_height in zip(peaks, peak_heights):
#    plt.annotate(f'({i}, {peak_height:.2f})', xy=(i, peak_height), textcoords="offset points", xytext=(-5,10), ha='center')
plt.xlabel('Frame')
plt.ylabel('Jump Height (cm)')
plt.title('Jump Height per Frame with Peaks Connected')
plt.show()

cv2.destroyAllWindows()