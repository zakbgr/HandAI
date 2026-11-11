import math
import random

import cv2
import numpy as np


class IceBlastEffect:
    """Ice shard burst from the palm with a frost vignette."""

    DURATION = 2.6
    EMIT_TIME = 0.5

    def __init__(self):
        self.active = False
        self.age = 0.0
        self.origin = (0, 0)
        self.direction = (0.0, -1.0)
        self.shards = []
        self.snow = []
        self._frost = None

    # --------------------------------------------------
    # DIRECTION OF THE HAND (wrist -> middle finger base)
    # --------------------------------------------------

    @staticmethod
    def direction_from_landmarks(landmarks):
        wrist = landmarks[0]
        middle = landmarks[9]

        dx = middle.x - wrist.x
        dy = middle.y - wrist.y

        length = math.hypot(dx, dy) or 1.0

        return (dx / length, dy / length)

    # --------------------------------------------------
    # START / STOP
    # --------------------------------------------------

    def start(self, origin, direction):
        self.active = True
        self.age = 0.0
        self.origin = (int(origin[0]), int(origin[1]))
        self.direction = direction
        self.shards = []
        self.snow = []

        self._spawn(70)

    def stop(self):
        self.active = False
        self.shards = []
        self.snow = []

    # --------------------------------------------------
    # PARTICLES
    # --------------------------------------------------

    def _spawn(self, count):

        base = math.atan2(self.direction[1], self.direction[0])
        ox, oy = self.origin

        for _ in range(count):

            angle = base + random.uniform(-0.9, 0.9)
            speed = random.uniform(250, 750)

            self.shards.append({
                "x": ox + random.uniform(-10, 10),
                "y": oy + random.uniform(-10, 10),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "angle": angle,
                "length": random.uniform(14, 38),
                "age": 0.0,
                "life": random.uniform(0.9, 1.8),
            })

        for _ in range(count // 2):

            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 220)

            self.snow.append({
                "x": float(ox),
                "y": float(oy),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "radius": random.randint(1, 3),
                "age": 0.0,
                "life": random.uniform(1.0, 2.2),
            })

    def _update(self, dt):

        drag = max(0.0, 1.0 - 2.0 * dt)

        for s in self.shards:
            s["age"] += dt
            s["vx"] *= drag
            s["vy"] *= drag
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt

        for p in self.snow:
            p["age"] += dt
            p["vx"] *= max(0.0, 1.0 - 0.8 * dt)
            p["vy"] = p["vy"] * max(0.0, 1.0 - 0.8 * dt) + 30 * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt

        self.shards = [s for s in self.shards if s["age"] < s["life"]]
        self.snow = [p for p in self.snow if p["age"] < p["life"]]

    # --------------------------------------------------
    # FROST VIGNETTE (built once per frame size)
    # --------------------------------------------------

    def _build_frost(self, shape):

        h, w = shape[:2]

        if self._frost is not None and self._frost.shape[:2] == (h, w):
            return

        yy, xx = np.ogrid[:h, :w]

        distance = np.sqrt(
            ((xx - w / 2) / (w / 2)) ** 2
            + ((yy - h / 2) / (h / 2)) ** 2
        )

        mask = np.clip((distance - 0.55) / 0.8, 0, 1) ** 1.5

        noise = cv2.resize(
            np.random.rand(h // 12 + 2, w // 12 + 2).astype(np.float32),
            (w, h),
            interpolation=cv2.INTER_CUBIC
        )

        mask = np.clip(mask * (0.6 + 0.8 * noise), 0, 1)

        frost = np.zeros((h, w, 3), dtype=np.float32)
        frost[..., 0] = 255 * mask
        frost[..., 1] = 190 * mask
        frost[..., 2] = 90 * mask

        self._frost = frost.astype(np.uint8)

    # --------------------------------------------------
    # RENDER
    # --------------------------------------------------

    def render(self, frame, dt):

        if not self.active:
            return frame

        dt = max(0.0, min(dt, 0.05))

        self.age += dt

        if self.age >= self.DURATION:
            self.stop()
            return frame

        if self.age < self.EMIT_TIME:
            self._spawn(12)

        self._update(dt)

        # Frost creeping in from the edges, then melting away.
        self._build_frost(frame.shape)

        fade_in = min(1.0, self.age / 0.4)
        fade_out = min(1.0, (self.DURATION - self.age) / 1.0)
        alpha = 0.8 * fade_in * fade_out

        frame = cv2.add(
            frame,
            cv2.convertScaleAbs(self._frost, alpha=alpha)
        )

        layer = np.zeros_like(frame)

        # Expanding shockwave ring.
        ring_t = self.age / 0.5

        if ring_t < 1.0:
            cv2.circle(
                layer,
                self.origin,
                int(40 + 380 * ring_t),
                (255, 230, 170),
                max(1, int(8 * (1.0 - ring_t))),
                cv2.LINE_AA
            )

        # Ice shards (colors are BGR).
        for s in self.shards:

            fade = 1.0 - s["age"] / s["life"]

            ca = math.cos(s["angle"])
            sa = math.sin(s["angle"])

            x, y, length = s["x"], s["y"], s["length"]
            half = length * 0.2

            points = np.array([
                (x + ca * length, y + sa * length),
                (x - sa * half, y + ca * half),
                (x - ca * length * 0.4, y - sa * length * 0.4),
                (x + sa * half, y - ca * half),
            ], dtype=np.int32)

            color = (
                int(255 * fade),
                int(235 * fade),
                int(190 * fade),
            )

            cv2.fillConvexPoly(layer, points, color, cv2.LINE_AA)

            cv2.polylines(
                layer, [points], True,
                (int(255 * fade),) * 3, 1, cv2.LINE_AA
            )

        # Snow sparkles.
        for p in self.snow:

            fade = 1.0 - p["age"] / p["life"]

            cv2.circle(
                layer,
                (int(p["x"]), int(p["y"])),
                p["radius"],
                (int(255 * fade),) * 3,
                -1,
                cv2.LINE_AA
            )

        glow = cv2.GaussianBlur(layer, (0, 0), 5)

        frame = cv2.add(frame, cv2.convertScaleAbs(glow, alpha=0.8))
        frame = cv2.add(frame, layer)

        return frame
