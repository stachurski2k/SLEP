import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # wycisza logi TensorFlow/MediaPipe

import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
from tqdm import tqdm

# ── inicjalizacja detektorów ──────────────────────────────────────────────────
mp_pose  = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_face  = mp.solutions.face_mesh

pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,              # wykrywaj obie ręce
    model_complexity=1,
    min_detection_confidence=0.4, # niższy próg = więcej detekcji przy ruchu
    min_tracking_confidence=0.4
)

face = mp_face.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ── ścieżki ───────────────────────────────────────────────────────────────────
DATASET_DIR = Path("Dataset")
OUTPUT_DIR  = Path("Features")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── definicje kluczowych punktów ──────────────────────────────────────────────
FACE_KEY_INDICES = [
    1,              # nos
    152,            # podbródek
    70, 63, 105,    # lewa brew
    300, 293, 334,  # prawa brew
    159, 145,       # lewe oko (góra, dół)
    386, 374,       # prawe oko (góra, dół)
    13, 14,         # usta (góra, dół — otwieranie)
    78, 308,        # usta (lewy, prawy kącik — uśmiech)
    80, 88,         # dolna warga lewa
    310, 318,       # dolna warga prawa
]

POSE_KEY_INDICES = [
    11, 12,  # barki      ← punkt odniesienia do normalizacji
    13, 14,  # łokcie
    15, 16,  # nadgarstki ← fallback gdy ręka niewykryta
]

# ── wymiary wektora ───────────────────────────────────────────────────────────
# pose:        6 pkt × 3 =  18
# lewa ręka:  21 pkt × 3 =  63
# prawa ręka: 21 pkt × 3 =  63
# twarz:      20 pkt × 3 =  60
# ──────────────────────────────
# razem:                  = 204


def extract_landmarks(pose_results, hands_results,
                      face_results) -> np.ndarray:
    """
    Łączy wyniki trzech detektorów w jeden wektor (204,).
    Brakujące landmarki → NaN (preprocessing interpoluje je później).
    """
    landmarks = []

    # ── POSE ─────────────────────────────────────────────────────────────────
    # Pose wykrywa sylwetkę — barki, łokcie, nadgarstki zawsze widoczne
    # gdy osoba stoi przed kamerą. Używamy jako punkt odniesienia
    # do normalizacji przestrzennej w preprocessingu.
    if pose_results.pose_landmarks:
        for idx in POSE_KEY_INDICES:
            lm = pose_results.pose_landmarks.landmark[idx]
            landmarks.extend([lm.x, lm.y, lm.z])
    else:
        landmarks.extend([np.nan] * (len(POSE_KEY_INDICES) * 3))  # 18 NaN

    # ── RĘCE ──────────────────────────────────────────────────────────────────
    # mp_hands zwraca listę wykrytych rąk bez gwarantowanej kolejności.
    # Każda ręka ma etykietę "Left"/"Right" z perspektywy kamery —
    # UWAGA: to lustrzane odbicie względem osoby wykonującej gest.
    # "Right" z kamery = lewa ręka osoby, "Left" z kamery = prawa ręka osoby.
    left_hand  = None
    right_hand = None

    if hands_results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(
            hands_results.multi_hand_landmarks,
            hands_results.multi_handedness
        ):
            label  = handedness.classification[0].label
            coords = np.array(
                [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark],
                dtype=np.float32
            ).flatten()  # (63,)

            # odwracamy etykiety — kamera widzi lustrzanie
            if label == "Right":
                left_hand = coords   # Right z kamery = lewa ręka osoby
            else:
                right_hand = coords  # Left z kamery = prawa ręka osoby

    # jeśli ręka niewykryta → NaN (nie zero!)
    # zero po normalizacji daje fałszywy sygnał "ręka w centrum ciała"
    # NaN zostanie interpolowany z sąsiednich klatek gdzie ręka była widoczna
    landmarks.extend(left_hand  if left_hand  is not None
                     else [np.nan] * 63)
    landmarks.extend(right_hand if right_hand is not None
                     else [np.nan] * 63)

    # ── TWARZ ─────────────────────────────────────────────────────────────────
    # FaceMesh zwraca multi_face_landmarks (lista twarzy) — bierzemy pierwszą.
    # Wybieramy tylko 20 kluczowych punktów zamiast pełnych 468
    # żeby nie zaśmiecać wektora nieistotnymi detalami.
    if face_results.multi_face_landmarks:
        for idx in FACE_KEY_INDICES:
            lm = face_results.multi_face_landmarks[0].landmark[idx]
            landmarks.extend([lm.x, lm.y, lm.z])
    else:
        landmarks.extend([np.nan] * (len(FACE_KEY_INDICES) * 3))  # 60 NaN

    return np.array(landmarks, dtype=np.float32)  # (204,)


# ── główna pętla ──────────────────────────────────────────────────────────────
gesture_dirs = [d for d in DATASET_DIR.iterdir() if d.is_dir()]

for gesture_dir in sorted(gesture_dirs):
    gesture_name       = gesture_dir.name
    output_gesture_dir = OUTPUT_DIR / gesture_name
    output_gesture_dir.mkdir(exist_ok=True)

    print(f"\nProcessing gesture: {gesture_name}")
    video_files = list(gesture_dir.glob("*.mp4"))

    for video_path in tqdm(video_files):
        cap      = cv2.VideoCapture(str(video_path))
        sequence = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # MediaPipe wymaga RGB — OpenCV czyta BGR
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False  # optymalizacja — brak kopii pamięci

            # trzy osobne detekcje na tej samej klatce
            pose_res  = pose.process(rgb)
            hands_res = hands.process(rgb)
            face_res  = face.process(rgb)

            landmarks = extract_landmarks(pose_res, hands_res, face_res)
            sequence.append(landmarks)

        cap.release()

        if not sequence:
            print(f"  ⚠ puste wideo: {video_path.name}")
            continue

        sequence = np.array(sequence, dtype=np.float32)  # (T, 204)

        # diagnostyka NaN — informacja o jakości detekcji
        # wysoki NaN = MediaPipe nie widział rąk w wielu klatkach
        nan_ratio = np.isnan(sequence).mean()
        if nan_ratio > 0.5:
            print(f"  ⚠ {video_path.name}: {nan_ratio:.0%} NaN "
                  f"— słabe wykrycie landmarków")

        output_path = output_gesture_dir / f"{video_path.stem}.npy"
        np.save(str(output_path), sequence)

pose.close()
hands.close()
face.close()

print("\nDONE")