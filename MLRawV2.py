import cv2
import mediapipe as mp

# Inisialisasi MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Membuka video atau kamera
user_choice = input("Tekan 'c' untuk kamera atau 'f' untuk file video: ").lower()
if user_choice == 'f':  
    path_to_file = 'data/evan2.mp4'
    cap = cv2.VideoCapture(path_to_file)
elif user_choice == 'c':
    cap = cv2.VideoCapture(0)

# Menentukan frame rate
frame_rate = cap.get(cv2.CAP_PROP_FPS)
frame_count = 0
ankle_reference = None
take_off_time = None
landing_time = None
flight_time = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)

    if results.pose_landmarks:
        ankle_current = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE]

        if frame_count == 0:
            # Mengambil posisi ankle pada frame pertama sebagai referensi
            ankle_reference = ankle_current

        if ankle_reference:
            # Deteksi take-off
            take_off = ankle_current.y - ankle_reference.y
            if abs(take_off) > 0.05 and take_off_time is None:
                take_off_time = frame_count / frame_rate
                print(f"Take-off detected at: {take_off_time:.2f}s")

            # Deteksi landing
            if abs(ankle_current.y - ankle_reference.y) < 0.05 and take_off_time is not None:
                landing_time = frame_count / frame_rate
                flight_time = landing_time - take_off_time
                print(f"Landing detected at: {landing_time:.2f}s")
                print(f"Flight time: {flight_time:.2f}s")

                # Hitung tinggi lompatan menggunakan flight time
                height_jump = (flight_time)** 2 * 1.22625
                print(f"Tinggi lompatan: {height_jump:.2f} meter")

                # Reset take-off dan landing time untuk deteksi lompatan berikutnya
                take_off_time = None
                landing_time = None

    frame_count += 1
    cv2.imshow("Pose Detection", frame)

    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
