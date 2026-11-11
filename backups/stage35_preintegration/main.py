
import cv2
import mediapipe as mp
import threading
import time
import tkinter as tk

from pathlib import Path
from PIL import Image, ImageTk

from finger_detection import GestureRecognizer


# ==========================================================
# CONFIGURATION
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_DIR / "models" / "hand_landmarker.task"

CAMERA_INDEX = 0

FRAME_WIDTH = 960
FRAME_HEIGHT = 540

MAX_HANDS = 2

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]


# ==========================================================
# HAND TRACKING ENGINE
# ==========================================================

class HandTracker:

    def __init__(self):

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"AI model not found: {MODEL_PATH}"
            )

        # Initialize MediaPipe.
        base_options = mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH)
        )

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=MAX_HANDS,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.detector = (
            mp.tasks.vision.HandLandmarker.create_from_options(
                options
            )
        )

        # Initialize our gesture recognition engine.
        self.gesture_recognizer = GestureRecognizer()

    # ------------------------------------------------------
    # DETECT HANDS
    # ------------------------------------------------------

    def detect(self, frame, timestamp_ms):

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        result = self.detector.detect_for_video(
            mp_image,
            timestamp_ms
        )

        return result

    # ------------------------------------------------------
    # DRAW LANDMARKS + RECOGNIZE GESTURES
    # ------------------------------------------------------

    def draw_landmarks(self, frame, result):

        height, width, _ = frame.shape

        hands = result.hand_landmarks

        for hand_index, landmarks in enumerate(hands):

            # Identify hand orientation.
            hand_label = "Unknown"

            if (
                result.handedness
                and hand_index < len(result.handedness)
                and result.handedness[hand_index]
            ):

                hand_label = (
                    result.handedness[hand_index][0].category_name
                )

            # Run finger detection and gesture recognition.
            fingers, gesture = self.gesture_recognizer.update(
                landmarks,
                hand_label
            )

            # --------------------------------------------------
            # DRAW SKELETON
            # --------------------------------------------------

            for start, end in HAND_CONNECTIONS:

                p1 = landmarks[start]
                p2 = landmarks[end]

                x1 = int(p1.x * width)
                y1 = int(p1.y * height)

                x2 = int(p2.x * width)
                y2 = int(p2.y * height)

                cv2.line(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 120),
                    2
                )

            # --------------------------------------------------
            # DRAW LANDMARK POINTS
            # --------------------------------------------------

            for index, point in enumerate(landmarks):

                x = int(point.x * width)
                y = int(point.y * height)

                if index in [4, 8, 12, 16, 20]:

                    color = (0, 100, 255)
                    radius = 7

                else:

                    color = (255, 255, 0)
                    radius = 4

                cv2.circle(
                    frame,
                    (x, y),
                    radius,
                    color,
                    -1
                )

            # --------------------------------------------------
            # DISPLAY GESTURE
            # --------------------------------------------------

            y_offset = 80 + hand_index * 90

            cv2.putText(
                frame,
                f"{hand_label}: {gesture}",
                (20, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 120),
                2
            )

            # --------------------------------------------------
            # DISPLAY FINGER STATES
            # --------------------------------------------------

            finger_text = " ".join(
                f"{name[:1].upper()}:"
                f"{'UP' if value else 'DOWN'}"
                for name, value in fingers.items()
            )

            cv2.putText(
                frame,
                finger_text,
                (20, y_offset + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )

        return frame

    # ------------------------------------------------------
    # RELEASE MODEL
    # ------------------------------------------------------

    def close(self):

        self.detector.close()


# ==========================================================
# DESKTOP APPLICATION
# ==========================================================

class HandAIApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "HandAI - Gesture Recognition System"
        )

        self.root.geometry("1100x760")
        self.root.minsize(850, 650)

        self.root.configure(
            bg="#101820"
        )

        # Thread controls.
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        self.data_lock = threading.Lock()

        self.latest_frame = None

        self.latest_info = {
            "hands": 0,
            "fps": 0,
            "status": "Initializing..."
        }

        self.error_message = None

        self.photo = None

        # Build GUI.
        self.setup_interface()

        # Start background camera thread.
        self.camera_thread = threading.Thread(
            target=self.camera_loop,
            daemon=True
        )

        self.camera_thread.start()

        # Start GUI updates.
        self.update_interface()

        # Window close event.
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

        # Keyboard shortcuts.
        self.root.bind(
            "<KeyPress-p>",
            self.toggle_pause
        )

        self.root.bind(
            "<KeyPress-P>",
            self.toggle_pause
        )

        self.root.bind(
            "<KeyPress-q>",
            self.close_application
        )

        self.root.bind(
            "<KeyPress-Q>",
            self.close_application
        )

    # ======================================================
    # GUI DESIGN
    # ======================================================

    def setup_interface(self):

        # Title.
        title = tk.Label(
            self.root,
            text="HandAI",
            font=("Arial", 28, "bold"),
            fg="#00ff99",
            bg="#101820"
        )

        title.pack(pady=(15, 0))

        subtitle = tk.Label(
            self.root,
            text="Real-Time AI Hand Tracking & Gesture Recognition",
            font=("Arial", 11),
            fg="white",
            bg="#101820"
        )

        subtitle.pack(pady=5)

        # Webcam display.
        self.video_label = tk.Label(
            self.root,
            bg="#000000",
            text="Waiting for camera...",
            fg="white",
            font=("Arial", 14)
        )

        self.video_label.pack(
            padx=20,
            pady=15
        )

        # Statistics.
        stats_frame = tk.Frame(
            self.root,
            bg="#182630"
        )

        stats_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )

        self.hands_label = tk.Label(
            stats_frame,
            text="Hands detected: 0",
            font=("Arial", 13, "bold"),
            fg="#00ff99",
            bg="#182630"
        )

        self.hands_label.pack(
            side="left",
            expand=True,
            pady=15
        )

        self.fps_label = tk.Label(
            stats_frame,
            text="FPS: 0",
            font=("Arial", 13, "bold"),
            fg="#00ff99",
            bg="#182630"
        )

        self.fps_label.pack(
            side="left",
            expand=True,
            pady=15
        )

        # Status.
        self.status_label = tk.Label(
            self.root,
            text="Initializing AI...",
            font=("Arial", 11),
            fg="white",
            bg="#101820"
        )

        self.status_label.pack(pady=5)

        # Buttons.
        buttons_frame = tk.Frame(
            self.root,
            bg="#101820"
        )

        buttons_frame.pack(pady=15)

        self.pause_button = tk.Button(
            buttons_frame,
            text="Pause Detection",
            command=self.toggle_pause,
            width=18,
            bg="#167d5a",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat"
        )

        self.pause_button.pack(
            side="left",
            padx=10
        )

        quit_button = tk.Button(
            buttons_frame,
            text="Exit",
            command=self.close_application,
            width=12,
            bg="#b83232",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat"
        )

        quit_button.pack(
            side="left",
            padx=10
        )

        # Footer.
        footer = tk.Label(
            self.root,
            text="P = Pause/Resume     Q = Quit",
            fg="#aaaaaa",
            bg="#101820",
            font=("Arial", 9)
        )

        footer.pack(pady=5)

    # ======================================================
    # CAMERA + AI PROCESSING
    # ======================================================

    def camera_loop(self):

        camera = None
        tracker = None

        try:

            # Initialize hand tracking.
            tracker = HandTracker()

            # Initialize webcam.
            camera = cv2.VideoCapture(
                CAMERA_INDEX,
                cv2.CAP_V4L2
            )

            if not camera.isOpened():

                raise RuntimeError(
                    "Cannot open webcam. Check camera permissions."
                )

            camera.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                FRAME_WIDTH
            )

            camera.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                FRAME_HEIGHT
            )

            previous_time = time.perf_counter()

            last_timestamp = 0

            fps = 0.0

            while not self.stop_event.is_set():

                success, frame = camera.read()

                if not success:

                    time.sleep(0.01)
                    continue

                # Mirror webcam image.
                frame = cv2.flip(
                    frame,
                    1
                )

                if self.pause_event.is_set():

                    hands_count = 0
                    status = "Detection paused"

                else:

                    # Generate monotonic timestamp.
                    timestamp_ms = max(
                        last_timestamp + 1,
                        time.monotonic_ns() // 1_000_000
                    )

                    last_timestamp = timestamp_ms

                    # Detect hands.
                    result = tracker.detect(
                        frame,
                        timestamp_ms
                    )

                    hands_count = len(
                        result.hand_landmarks
                    )

                    # Draw landmarks and identify gestures.
                    tracker.draw_landmarks(
                        frame,
                        result
                    )

                    status = (
                        "Hand detected"
                        if hands_count > 0
                        else "Show your hand to the camera"
                    )

                # FPS calculation.
                current_time = time.perf_counter()

                delta = current_time - previous_time

                if delta > 0:

                    current_fps = 1.0 / delta

                    fps = (
                        0.85 * fps
                        + 0.15 * current_fps
                    )

                previous_time = current_time

                # Display LIVE indicator.
                cv2.putText(
                    frame,
                    "HandAI | LIVE",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 120),
                    2
                )

                # Share data with GUI thread.
                with self.data_lock:

                    self.latest_frame = frame.copy()

                    self.latest_info = {
                        "hands": hands_count,
                        "fps": round(fps, 1),
                        "status": status
                    }

        except Exception as error:

            with self.data_lock:

                self.error_message = str(error)

        finally:

            if camera is not None:
                camera.release()

            if tracker is not None:
                tracker.close()

    # ======================================================
    # UPDATE GUI
    # ======================================================

    def update_interface(self):

        with self.data_lock:

            frame = (
                self.latest_frame.copy()
                if self.latest_frame is not None
                else None
            )

            info = self.latest_info.copy()

            error = self.error_message

        if error:

            self.status_label.config(
                text=f"ERROR: {error}",
                fg="#ff5555"
            )

        if frame is not None:

            # Resize frame.
            frame = cv2.resize(
                frame,
                (960, 540)
            )

            # Convert BGR to RGB.
            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            image = Image.fromarray(rgb)

            self.photo = ImageTk.PhotoImage(
                image=image
            )

            self.video_label.configure(
                image=self.photo,
                text=""
            )

            self.hands_label.config(
                text=f"Hands detected: {info['hands']}"
            )

            self.fps_label.config(
                text=f"FPS: {info['fps']}"
            )

            if not error:

                self.status_label.config(
                    text=info["status"],
                    fg="#00ff99"
                )

        if not self.stop_event.is_set():

            self.root.after(
                15,
                self.update_interface
            )

    # ======================================================
    # PAUSE / RESUME
    # ======================================================

    def toggle_pause(self, event=None):

        if self.pause_event.is_set():

            self.pause_event.clear()

            self.pause_button.config(
                text="Pause Detection",
                bg="#167d5a"
            )

        else:

            self.pause_event.set()

            self.pause_button.config(
                text="Resume Detection",
                bg="#a36b20"
            )

    # ======================================================
    # CLOSE APPLICATION
    # ======================================================

    def close_application(self, event=None):

        if self.stop_event.is_set():
            return

        self.stop_event.set()

        self.root.destroy()


# ==========================================================
# APPLICATION ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = HandAIApp(root)

    root.mainloop()
