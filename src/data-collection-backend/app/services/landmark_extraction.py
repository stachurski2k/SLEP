import logging
import imageio
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Landmark counts per body component (MediaPipe Holistic)
# ---------------------------------------------------------------------------
NUM_POSE_LANDMARKS = 33
NUM_FACE_LANDMARKS = 478
NUM_HAND_LANDMARKS = 21  # per hand (left and right are stored separately)

# ---------------------------------------------------------------------------
# Per-frame row layout (all values are float32, order: x, y, z per landmark)
#
#   Columns 0   – 98   : POSE (33 landmarks × 3)
#   Columns 99  – 1532 : FACE (478 landmarks × 3)
#   Columns 1533– 1595 : LEFT HAND (21 landmarks × 3)
#   Columns 1596– 1658 : RIGHT HAND (21 landmarks × 3)
#
#   Total columns: 1659
# ---------------------------------------------------------------------------

# Slice helpers for extracting individual components from a loaded .npy array
POSE_SLICE       = slice(0,    99)    # landmarks[:, POSE_SLICE]       → (F, 99)
FACE_SLICE       = slice(99,   1533)  # landmarks[:, FACE_SLICE]       → (F, 1434)
LEFT_HAND_SLICE  = slice(1533, 1596)  # landmarks[:, LEFT_HAND_SLICE]  → (F, 63)
RIGHT_HAND_SLICE = slice(1596, 1659)  # landmarks[:, RIGHT_HAND_SLICE] → (F, 63)

LANDMARK_ROW_SIZE = (NUM_POSE_LANDMARKS + NUM_FACE_LANDMARKS + NUM_HAND_LANDMARKS * 2) * 3


class LandmarkExtractionService:
    def __init__(self, model_path: str = "/app/models/holistic_landmarker.task"):
        self.model_path = model_path

    def _extract_landmark_coords(self, landmarks, expected_count: int) -> np.ndarray:
        """
        Flatten landmark coordinates (x, y, z) into a 1-D float32 array.
        If the component was not detected in this frame, returns zeros so that
        every frame row has a consistent, fixed length.
        """
        if landmarks:
            coords = [[lm.x, lm.y, lm.z] for lm in landmarks]
        else:
            coords = [[0.0, 0.0, 0.0]] * expected_count

        return np.array(coords, dtype=np.float32).flatten()

    def extract_from_video(self, video_path: str) -> np.ndarray:
        """
        Process a video file and return a NumPy array of landmarks.
        Shape: (num_frames, LANDMARK_ROW_SIZE)
        """
        base_options = mp_python.BaseOptions(model_asset_path=self.model_path)
        options = vision.HolisticLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
        )

        all_frames_data = []

        with vision.HolisticLandmarker.create_from_options(options) as detector:
            reader = imageio.get_reader(video_path)

            for frame_idx, frame in enumerate(reader):
                mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                result = detector.detect(mp_frame)

                pose_row       = self._extract_landmark_coords(result.pose_landmarks,       NUM_POSE_LANDMARKS)
                face_row       = self._extract_landmark_coords(result.face_landmarks,       NUM_FACE_LANDMARKS)
                left_hand_row  = self._extract_landmark_coords(result.left_hand_landmarks,  NUM_HAND_LANDMARKS)
                right_hand_row = self._extract_landmark_coords(result.right_hand_landmarks, NUM_HAND_LANDMARKS)

                # One row per frame, shape: (LANDMARK_ROW_SIZE,) = (1659,)
                frame_row = np.concatenate([pose_row, face_row, left_hand_row, right_hand_row])
                all_frames_data.append(frame_row)

                if frame_idx % 50 == 0:
                    logger.info(f"Processed {frame_idx} frames")

            reader.close()

        return np.array(all_frames_data, dtype=np.float32)
