import math
import random

import cv2
import numpy as np


class LightningEffect:
    """Lightning bolts striking the pointing fingertip."""

    DURATION = 1.8

    def __init__(self):
        self.active = False
        self.age = 0.0
        self.regen_timer = 0.0
        self.bolts = []
        self.last_target = None

    def start(self):
        self.active = True
        self.age = 0.0
        self.regen_timer = 0.0
        self.bolts = []
        self.last_target = None

    def stop(self):
        self.active = False
        self.bolts = []

    # --------------------------------------------------
    # JAGGED BOLT GENERATION (midpoint displacement)
    # --------------------------------------------------

    @staticmethod
    def _jagged(start, end, offset, detail):
        points = [start, end]

        for _ in range(detail):
            new_points = []

            for a, b in zip(points[:-1], points[1:]):
                mid_x = (a[0] + b[0]) / 2 + random.uniform(-offset, offset)
                mid_y = (a[1] + b[1]) / 2 + random.uniform(-offset, offset)

                new_points.append(a)
                new_points.append((mid_x, mid_y))

            new_points.append(points[-1])
            points = new_points
            offset /= 2

        return points

    @staticmethod
    def _to_array(points):
        return np.array(
            [(int(x), int(y)) for x, y in points],
            dtype=np.int32
        )

    def _build(self, width, height, target):

        self.bolts = []

        tx, ty = target

        for thickness in (3, 2):

            origin_x = min(max(tx + random.uniform(-220, 220), 0), width - 1)
            origin = (origin_x, 0.0)

            distance = math.hypot(tx - origin[0], ty - origin[1])

            main = self._jagged(
                origin,
                (float(tx), float(ty)),
                distance * 0.18,
                6
            )

            self.bolts.append((self._to_array(main), thickness))

            # Side branches.
            for _ in range(4):

                index = random.randrange(
                    len(main) // 6,
                    len(main) - len(main) // 6
                )

                bx, by = main[index]

                end = (
                    bx + random.uniform(-140, 140),
                    by + random.uniform(60, 220)
                )

                branch = self._jagged((bx, by), end, 28, 4)

                self.bolts.append((self._to_array(branch), 1))

    # --------------------------------------------------
    # RENDER
    # --------------------------------------------------

    def render(self, frame, target, dt):

        if not self.active:
            return frame

        dt = max(0.0, min(dt, 0.05))

        self.age += dt

        if self.age >= self.DURATION:
            self.stop()
            return frame

        h, w = frame.shape[:2]

        if target is not None:
            self.last_target = target

        tx, ty = self.last_target if self.last_target else (w // 2, h // 2)

        # Rebuild the bolts every few frames so they flicker.
        self.regen_timer -= dt

        if self.regen_timer <= 0:
            self._build(w, h, (tx, ty))
            self.regen_timer = random.uniform(0.04, 0.09)

        # Fade out during the last 0.5 s, with random flicker.
        fade = 1.0 - max(0.0, (self.age - (self.DURATION - 0.5)) / 0.5)
        intensity = fade * random.uniform(0.75, 1.0)

        layer = np.zeros_like(frame)

        # Colors are BGR. Blue glow first, white cores on top.
        for points, thickness in self.bolts:
            cv2.polylines(
                layer, [points], False,
                (255, 170, 80), thickness + 4, cv2.LINE_AA
            )

        for points, thickness in self.bolts:
            cv2.polylines(
                layer, [points], False,
                (255, 255, 255), max(1, thickness), cv2.LINE_AA
            )

        # Impact flare and sparks.
        cv2.circle(layer, (tx, ty), 18, (255, 200, 120), -1, cv2.LINE_AA)
        cv2.circle(layer, (tx, ty), 8, (255, 255, 255), -1, cv2.LINE_AA)

        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(10, 40)

            cv2.line(
                layer,
                (tx, ty),
                (int(tx + math.cos(angle) * length),
                 int(ty + math.sin(angle) * length)),
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        glow = cv2.GaussianBlur(layer, (0, 0), 7)

        combined = cv2.add(layer, glow)
        combined = cv2.convertScaleAbs(combined, alpha=intensity)

        frame = cv2.add(frame, combined)

        # Screen flash at the moment of the strike.
        flash = max(0.0, 1.0 - self.age / 0.2)

        if flash > 0:
            value = int(70 * flash)
            frame = cv2.add(frame, np.full_like(frame, value))

        return frame
