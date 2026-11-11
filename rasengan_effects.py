import math
import random

import cv2
import numpy as np


class RasenganEffect:
    """Spinning chakra sphere that follows the palm."""

    def __init__(self):
        self.active = False
        self.age = 0.0
        self.angle = 0.0
        self.position = None
        self.radius = None
        self.sparks = []

    # --------------------------------------------------
    # START / STOP
    # --------------------------------------------------

    def start(self):
        self.active = True
        self.age = 0.0
        self.position = None
        self.radius = None
        self.sparks.clear()

    def stop(self):
        self.active = False
        self.position = None
        self.radius = None
        self.sparks.clear()

    # --------------------------------------------------
    # PALM POSITION FROM HAND LANDMARKS
    # --------------------------------------------------

    @staticmethod
    def palm_from_landmarks(landmarks, width, height):
        ids = (0, 5, 9, 13, 17)

        cx = sum(landmarks[i].x for i in ids) / len(ids) * width
        cy = sum(landmarks[i].y for i in ids) / len(ids) * height

        wrist = landmarks[0]
        middle = landmarks[9]

        dx = (middle.x - wrist.x) * width
        dy = (middle.y - wrist.y) * height

        size = math.hypot(dx, dy)

        # Float the ball slightly above the palm, toward the fingers.
        cx += dx * 0.2
        cy += dy * 0.2

        radius = max(28.0, min(size * 0.55, 120.0))

        return (int(cx), int(cy)), radius

    # --------------------------------------------------
    # SPARKS
    # --------------------------------------------------

    def _update_sparks(self, dt, r):

        while len(self.sparks) < 30:
            self.sparks.append([
                random.uniform(0, 2 * math.pi),   # angle
                r * random.uniform(0.9, 1.1),     # distance
                0.0,                              # age
                random.uniform(0.3, 0.7),         # lifetime
            ])

        for spark in self.sparks:
            spark[0] += 5.0 * dt
            spark[1] += r * 1.3 * dt
            spark[2] += dt

        self.sparks = [s for s in self.sparks if s[2] < s[3]]

    # --------------------------------------------------
    # RENDER
    # --------------------------------------------------

    def render(self, frame, palm, dt):

        if not self.active:
            return frame

        dt = max(0.0, min(dt, 0.05))

        self.age += dt
        self.angle += dt * 9.0

        if palm is None:
            return frame

        center, radius = palm

        # Smooth movement so the ball doesn't jitter.
        if self.position is None:
            self.position = [float(center[0]), float(center[1])]
            self.radius = float(radius)
        else:
            k = 0.45
            self.position[0] += (center[0] - self.position[0]) * k
            self.position[1] += (center[1] - self.position[1]) * k
            self.radius += (radius - self.radius) * 0.25

        # Grow-in animation (0.6 s, ease out).
        grow = min(1.0, self.age / 0.6)
        grow = 1.0 - (1.0 - grow) ** 3

        r = self.radius * grow

        if r < 4:
            return frame

        h, w = frame.shape[:2]

        cx = int(self.position[0])
        cy = int(self.position[1])

        margin = int(r * 2.4) + 4

        x0 = max(0, cx - margin)
        y0 = max(0, cy - margin)
        x1 = min(w, cx + margin)
        y1 = min(h, cy + margin)

        if x1 <= x0 or y1 <= y0:
            return frame

        layer = np.zeros((y1 - y0, x1 - x0, 3), dtype=np.uint8)
        c = (cx - x0, cy - y0)

        # Colors are BGR.

        # Sphere body.
        cv2.circle(layer, c, int(r), (200, 110, 20), -1, cv2.LINE_AA)
        cv2.circle(layer, c, int(r * 0.7), (255, 190, 90), -1, cv2.LINE_AA)
        cv2.circle(layer, c, int(r * 0.4), (255, 250, 220), -1, cv2.LINE_AA)
        cv2.circle(layer, c, int(r * 1.15), (255, 170, 60), 2, cv2.LINE_AA)

        # Rotating rings give the 3D swirling look.
        for i in range(5):
            tilt = (math.degrees(self.angle) * (0.6 + 0.25 * i) + i * 36) % 360
            axes = (
                max(2, int(r)),
                max(2, int(r * (0.25 + 0.12 * i))),
            )
            cv2.ellipse(
                layer, c, axes, tilt, 0, 360,
                (255, 230, 150), 2, cv2.LINE_AA
            )

        # Spiral arms.
        arms = 5

        for k in range(arms):
            base = self.angle * 1.5 + k * 2 * math.pi / arms
            points = []

            for s in range(21):
                t = s / 20
                a = base + t * 2.4
                d = r * (0.15 + 0.85 * t)

                points.append((
                    int(c[0] + math.cos(a) * d),
                    int(c[1] + math.sin(a) * d),
                ))

            cv2.polylines(
                layer,
                [np.array(points, dtype=np.int32)],
                False,
                (255, 245, 200),
                2,
                cv2.LINE_AA
            )

        # Sparks flying off the sphere.
        self._update_sparks(dt, r)

        for angle, dist, age, life in self.sparks:
            fade = 1.0 - age / life
            sx = int(c[0] + math.cos(angle) * dist)
            sy = int(c[1] + math.sin(angle) * dist)
            cv2.circle(
                layer, (sx, sy),
                max(1, int(3 * fade)),
                (255, 240, 200), -1, cv2.LINE_AA
            )

        # Additive glow.
        glow = cv2.GaussianBlur(layer, (0, 0), max(3.0, r * 0.28))

        roi = frame[y0:y1, x0:x1]
        roi = cv2.add(roi, glow)
        roi = cv2.add(roi, layer)

        frame[y0:y1, x0:x1] = roi

        return frame