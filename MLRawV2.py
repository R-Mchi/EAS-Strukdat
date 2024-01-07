import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False, min_detection_confidence=0.5)

user_choice = input("Tekan 'c' untuk kamera atau 'f' untuk file video: ").lower()
if user_choice == 'f':  
    path_to_file = 'data/Fikra2.mp4'
    cap = cv2.VideoCapture(path_to_file)
elif user_choice == 'c':
    cap = cv2.VideoCapture(0)

th_take_off = 0.03
th_take_landing = 0.035

frame_rate = cap.get(cv2.CAP_PROP_FPS)
frame_count = 0
ankle_reference = None
take_off_time = None
landing_time = None
flight_time = 0
is_in_air = False  
highest_jump = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)

    if results.pose_landmarks:
        ankle_left_current = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE]
        ankle_right_current = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE]

        if frame_count == 0:
            ankle_left_reference = ankle_left_current
            ankle_right_reference = ankle_right_current

        if ankle_left_reference and ankle_right_reference:
            # Deteksi take-off
            if not is_in_air and (abs(ankle_left_current.y - ankle_left_reference.y) > th_take_off or 
                                  abs(ankle_right_current.y - ankle_right_reference.y) > th_take_off):
                #print(ankle_current.y - ankle_reference.y)
                take_off_time = frame_count / frame_rate
                is_in_air = True
                #print(f"Take-off detected at: {take_off_time:.4f}s")

            if is_in_air and (abs(ankle_left_current.y - ankle_left_reference.y) < th_take_landing and 
                              abs(ankle_right_current.y - ankle_right_reference.y) < th_take_landing):
                landing_time = frame_count / frame_rate
                flight_time = landing_time - take_off_time
                is_in_air = False  
                #print(f"Landing detected at: {landing_time:.4f}s")
                #print(f"Flight time: {flight_time:.4f}s")

                height_jump = (flight_time** 2) * 1.22625 * 100
                if height_jump > highest_jump:
                    highest_jump = height_jump
                

                ankle_left_reference = ankle_left_current
                ankle_right_reference = ankle_right_current
                take_off_time = None
                landing_time = None

    frame_count += 1
    cv2.imshow("Pose Detection", frame)

    if cv2.waitKey(5) & 0xFF == 27:
        break

print(f"Tinggi lompatan: {highest_jump:.4f} cm")
cap.release()
cv2.destroyAllWindows()
