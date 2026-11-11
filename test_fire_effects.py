
import cv2
import numpy as np
import time

from fire_effects import FireParticleEngine


WIDTH = 960
HEIGHT = 540

fire = FireParticleEngine()

previous_time = time.perf_counter()

print("===== FIRE EFFECT TEST =====")
print("SPACE = Fireball burst")
print("F = Continuous flames")
print("S = Stop flames")
print("C = Clear particles")
print("Q = Quit")

continuous = True

while True:

    now = time.perf_counter()

    dt = now - previous_time
    previous_time = now

    # Dark background.
    frame = np.zeros(
        (HEIGHT, WIDTH, 3),
        dtype=np.uint8,
    )

    # Add a small visual emitter marker.
    cv2.circle(
        frame,
        (WIDTH // 2, HEIGHT - 70),
        8,
        (255, 255, 255),
        -1,
    )

    # Render continuous fire.
    frame = fire.render(
        frame,
        origin=(WIDTH // 2, HEIGHT - 70),
        active=continuous,
        dt=dt,
    )

    cv2.putText(
        frame,
        "HandAI - FIRE PARTICLE ENGINE",
        (25, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    cv2.imshow(
        "HandAI Fire Test",
        frame,
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    elif key == ord("f"):
        continuous = True

    elif key == ord("s"):
        continuous = False

    elif key == ord("c"):
        fire.clear()

    elif key == ord(" "):

        fire.burst(
            WIDTH // 2,
            HEIGHT - 70,
            count=150,
            direction=(0, -1),
        )

cv2.destroyAllWindows()
