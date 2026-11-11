import cv2
import time

from face_tracking import FaceTracker
from fire_effects import FireParticleEngine


def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Cannot open webcam.")
        return

    face_tracker = FaceTracker()
    fire = FireParticleEngine()

    fire_active = False
    previous_time = time.monotonic()

    print("\n🐉 DRAGON BREATH TEST")
    print("-----------------------")
    print("F     = Toggle continuous fire")
    print("SPACE = Fire burst")
    print("S     = Stop fire")
    print("Q     = Quit")

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("ERROR: Cannot read webcam.")
                break

            frame = cv2.flip(frame, 1)

            current_time = time.monotonic()
            dt = min(current_time - previous_time, 0.05)
            previous_time = current_time

            timestamp_ms = time.monotonic_ns() // 1_000_000

            face_data = face_tracker.detect(
                frame,
                timestamp_ms
            )

            if face_data is not None:
                mouth_position = face_data["mouth"]

                frame = face_tracker.draw_debug(
                    frame,
                    face_data
                )

                # Fire originates at the detected mouth.
                frame = fire.render(
                    frame,
                    origin=mouth_position,
                    active=fire_active,
                    dt=dt
                )

                status = "FIRE ACTIVE" if fire_active else "READY"

            else:
                status = "NO FACE - FIRE PAUSED"

            cv2.putText(
                frame,
                f"DRAGON BREATH: {status}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 150, 255),
                2
            )

            cv2.imshow("HandAI - Dragon Breath", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("f"):
                fire_active = not fire_active
                print("Fire:", "ON" if fire_active else "OFF")

            elif key == ord(" "):
                if face_data is not None:
                    x, y = face_data["mouth"]
                    fire.burst(x, y, count=120)
                    print("🔥 DRAGON BREATH BURST!")

            elif key == ord("s"):
                fire_active = False
                fire.clear()
                print("Fire stopped.")

    finally:
        face_tracker.close()
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
