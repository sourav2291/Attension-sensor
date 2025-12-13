import cv2
import mediapipe as mp
import numpy as np
import time
import winsound
import sys

# ---------------- GET LOGGED USER ----------------
logged_user = "User"
if len(sys.argv) > 1:
    logged_user = sys.argv[1]

# ---------------- MediaPipe Setup ----------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    refine_landmarks=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
NOSE_TIP = 1
LEFT_CHEEK = 234
RIGHT_CHEEK = 454

def eye_aspect_ratio(points, landmarks, w, h):
    coords = [(int(landmarks[p].x * w), int(landmarks[p].y * h)) for p in points]
    A = np.linalg.norm(np.array(coords[1]) - np.array(coords[5]))
    B = np.linalg.norm(np.array(coords[2]) - np.array(coords[4]))
    C = np.linalg.norm(np.array(coords[0]) - np.array(coords[3]))
    return (A + B) / (2.0 * C)

# ---------------- PARAMETERS ----------------
EAR_THRESHOLD = 0.26
EYE_DISTRACT_TIME = 2
HEAD_SENSITIVITY = 0.06
HEAD_CONFIRM_TIME = 0.3
FACE_MISSING_TIME = 1
MAX_DISTRACTIONS = 10
MAX_SINGLE_DISTRACTION_TIME = 3

FONT = cv2.FONT_HERSHEY_SIMPLEX

# ---------------- STATE ----------------
eye_closed_start = None
head_violation_start = None
face_missing_start = None

distraction_active = False
distraction_start_time = None

distraction_count = 0
total_distracted_time = 0

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# ---------------- UI PANEL FUNCTION ----------------
def draw_info_panel(frame, lines, x=10, y=10, w=320, line_h=28):
    overlay = frame.copy()
    h = line_h * len(lines) + 20

    cv2.rectangle(overlay, (x, y), (x + w, y + h), (25, 25, 25), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    for i, (text, color) in enumerate(lines):
        cv2.putText(frame, text,
                    (x + 12, y + 30 + i * line_h),
                    FONT, 0.6, color, 2)

# ---------------- MAIN LOOP ----------------
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    now = time.time()
    rule_broken = False

    # ---------- FACE NOT PRESENT ----------
    if not results.multi_face_landmarks:
        if face_missing_start is None:
            face_missing_start = now
        elif now - face_missing_start >= FACE_MISSING_TIME:
            rule_broken = True
    else:
        face_missing_start = None
        landmarks = results.multi_face_landmarks[0].landmark

        # ---------- EYE RULE ----------
        ear = (
            eye_aspect_ratio(LEFT_EYE, landmarks, w, h) +
            eye_aspect_ratio(RIGHT_EYE, landmarks, w, h)
        ) / 2

        if ear < EAR_THRESHOLD:
            if eye_closed_start is None:
                eye_closed_start = now
            elif now - eye_closed_start >= EYE_DISTRACT_TIME:
                rule_broken = True
        else:
            eye_closed_start = None

        # ---------- HEAD RULE ----------
        nose_x = landmarks[NOSE_TIP].x
        face_center = (landmarks[LEFT_CHEEK].x + landmarks[RIGHT_CHEEK].x) / 2

        if abs(nose_x - face_center) > HEAD_SENSITIVITY:
            if head_violation_start is None:
                head_violation_start = now
            elif now - head_violation_start >= HEAD_CONFIRM_TIME:
                rule_broken = True
        else:
            head_violation_start = None

    # ---------- DISTRACTION HANDLING ----------
    if rule_broken:
        if not distraction_active:
            distraction_active = True
            distraction_start_time = now
            distraction_count += 1
            winsound.MessageBeep(winsound.MB_ICONHAND)
    else:
        if distraction_active:
            distraction_active = False
            total_distracted_time += now - distraction_start_time

    # ---------- AUTO CLOSE ----------
    if distraction_active and (now - distraction_start_time) >= MAX_SINGLE_DISTRACTION_TIME:
        print("⚠ Distraction exceeded 3 seconds. Closing application.")
        break

    if distraction_count > MAX_DISTRACTIONS:
        break

    # ---------- UI PANEL ----------
    panel_lines = []

    panel_lines.append((f"User : {logged_user}", (255, 255, 255)))

    if distraction_active:
        panel_lines.append(("Status : Distracted", (0, 0, 255)))
        panel_lines.append((f"Distractions : {distraction_count}", (0, 165, 255)))
        panel_lines.append((f"Distraction Time : {now - distraction_start_time:.1f} sec", (0, 0, 255)))
    else:
        panel_lines.append(("Status : Focused", (0, 200, 0)))
        panel_lines.append((f"Distractions : {distraction_count}", (0, 165, 255)))
        panel_lines.append((f"Total Distracted : {int(total_distracted_time)} sec", (200, 200, 255)))

    draw_info_panel(frame, panel_lines)

    cv2.imshow("Strict Attention Monitor", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ---------------- CLEANUP ----------------
cap.release()
cv2.destroyAllWindows()

print("Total Distractions:", distraction_count)
print("Total Distracted Time:", round(total_distracted_time, 2), "sec")
