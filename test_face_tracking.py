import cv2
import time

from face_tracking import FaceTracker


def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Cannot open webcam.")
        return

    tracker = FaceTracker()

    print("Face tracking started.")
    print("Press Q to quit.")

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("ERROR: Cannot read webcam frame.")
                break

            # Mirror the image like a normal selfie camera.
            frame = cv2.flip(frame, 1)

            timestamp_ms = time.monotonic_ns() // 1_000_000

            face_data = tracker.detect(
                frame,
                timestamp_ms
            )

            if face_data is not None:
                print(
                    f"Mouth position: {face_data['mouth']}",
                    end="\r"
                )

            frame = tracker.draw_debug(
                frame,
                face_data
            )

            cv2.imshow(
                "HandAI - Dragon Breath Face Tracking",
                frame
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        tracker.close()
        camera.release()
        cv2.destroyAllWindows()
        print("\nFace tracking stopped.")


if __name__ == "__main__":
    main()
