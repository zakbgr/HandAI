import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class FaceTracker:
    # MediaPipe Face Mesh landmarks:
    # 13 = upper inner lip
    # 14 = lower inner lip
    # 1  = nose area
    UPPER_LIP = 13
    LOWER_LIP = 14
    NOSE = 1

    def __init__(self, model_path="models/face_landmarker.task"):
        base_options = python.BaseOptions(
            model_asset_path=model_path
        )

        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
        )

        self.landmarker = vision.FaceLandmarker.create_from_options(
            options
        )

        self.last_timestamp_ms = -1

    def detect(self, frame, timestamp_ms):
        """
        Returns:
            {
                "mouth": (x, y),
                "nose": (x, y),
                "landmarks": face_landmarks
            }

        Returns None when no face is detected.
        """

        if timestamp_ms <= self.last_timestamp_ms:
            timestamp_ms = self.last_timestamp_ms + 1

        self.last_timestamp_ms = timestamp_ms

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )

        if not result.face_landmarks:
            return None

        landmarks = result.face_landmarks[0]

        height, width = frame.shape[:2]

        upper = landmarks[self.UPPER_LIP]
        lower = landmarks[self.LOWER_LIP]
        nose = landmarks[self.NOSE]

        mouth_x = int(((upper.x + lower.x) / 2) * width)
        mouth_y = int(((upper.y + lower.y) / 2) * height)

        nose_x = int(nose.x * width)
        nose_y = int(nose.y * height)

        return {
            "mouth": (mouth_x, mouth_y),
            "nose": (nose_x, nose_y),
            "landmarks": landmarks,
        }

    def draw_debug(self, frame, face_data):
        if face_data is None:
            cv2.putText(
                frame,
                "FACE NOT DETECTED",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )
            return frame

        mouth_x, mouth_y = face_data["mouth"]
        nose_x, nose_y = face_data["nose"]

        # Mouth marker
        cv2.circle(
            frame,
            (mouth_x, mouth_y),
            8,
            (0, 0, 255),
            -1
        )

        # Nose marker
        cv2.circle(
            frame,
            (nose_x, nose_y),
            5,
            (255, 255, 0),
            -1
        )

        # Line connecting nose to mouth
        cv2.line(
            frame,
            (nose_x, nose_y),
            (mouth_x, mouth_y),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "DRAGON BREATH ORIGIN",
            (mouth_x + 12, mouth_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 100, 255),
            2
        )

        return frame

    def close(self):
        self.landmarker.close()
