
import cv2

camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

if not camera.isOpened():
    print("ERROR: Cannot open webcam")
    exit()

print("Webcam connected successfully!")

while True:

    success, frame = camera.read()

    if not success:
        print("Failed to capture frame")
        break

    print("Frame:", frame.shape)

    cv2.imshow("HandAI - Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()

print("Camera test completed!")
