import math
import random

import cv2
import numpy as np


# Two-handed signs: both hands making the same gesture.
DOUBLE_GESTURES = {
    "FIST": "DOUBLE FIST",
    "OPEN PALM": "DOUBLE PALM",
    "PEACE SIGN": "DOUBLE PEACE",
    "POINTING": "DOUBLE POINT",
}


# ==========================================================
# HELPERS
# ==========================================================

def _clamp_dt(dt):
    return max(0.0, min(dt, 0.05))


def _ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def _unit(dx, dy, default=(0.0, -1.0), min_length=1e-6):
    length = math.hypot(dx, dy)

    if length < min_length:
        return default

    return dx / length, dy / length


def _palm_center(landmarks, width, height):
    ids = (0, 5, 9, 13, 17)

    cx = sum(landmarks[i].x for i in ids) / len(ids) * width
    cy = sum(landmarks[i].y for i in ids) / len(ids) * height

    return cx, cy


def _additive(frame, layer, sigma, glow_gain=0.8):
    glow = cv2.GaussianBlur(layer, (0, 0), sigma)

    frame = cv2.add(frame, cv2.convertScaleAbs(glow, alpha=glow_gain))

    return cv2.add(frame, layer)


def two_hand_pose(result, width, height):
    """Midpoint and pointing direction of two hands, or None."""

    hands = result.hand_landmarks

    if len(hands) < 2:
        return None

    c0 = _palm_center(hands[0], width, height)
    c1 = _palm_center(hands[1], width, height)

    mid = (
        int((c0[0] + c1[0]) / 2),
        int((c0[1] + c1[1]) / 2),
    )

    d0 = _unit(
        hands[0][9].x - hands[0][0].x,
        hands[0][9].y - hands[0][0].y,
    )

    d1 = _unit(
        hands[1][9].x - hands[1][0].x,
        hands[1][9].y - hands[1][0].y,
    )

    direction = _unit(
        d0[0] + d1[0],
        d0[1] + d1[1],
        default=d0,
        min_length=0.2,
    )

    return mid, direction


# ==========================================================
# SHADOW CLONE JUTSU  (DOUBLE PEACE)
# ==========================================================

class ShadowCloneEffect:
    """Two translucent clones appear beside you in clouds of smoke."""

    DURATION = 2.4
    OFFSET = 230

    def __init__(self):
        self.active = False
        self.age = 0.0
        self.puffs = []
        self.start_poof = False
        self.end_poof = False

    def start(self):
        self.active = True
        self.age = 0.0
        self.puffs = []
        self.start_poof = False
        self.end_poof = False

    def stop(self):
        self.active = False
        self.puffs = []

    def _poof(self, x, y):
        for _ in range(26):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 170)

            # x, y, vx, vy, radius, age, life
            self.puffs.append([
                x + random.uniform(-25, 25),
                y + random.uniform(-60, 60),
                math.cos(angle) * speed,
                math.sin(angle) * speed - 30,
                random.uniform(25, 55),
                0.0,
                random.uniform(0.5, 0.9),
            ])

    def render(self, frame, dt):

        if not self.active:
            return frame

        dt = _clamp_dt(dt)
        self.age += dt

        if self.age >= self.DURATION:
            self.stop()
            return frame

        h, w = frame.shape[:2]

        positions = [
            (w // 2 - self.OFFSET, h // 2),
            (w // 2 + self.OFFSET, h // 2),
        ]

        if not self.start_poof:
            self.start_poof = True

            for x, y in positions:
                self._poof(x, y)

        if not self.end_poof and self.age > self.DURATION - 0.5:
            self.end_poof = True

            for x, y in positions:
                self._poof(x, y)

        reach = self.OFFSET * _ease_out(self.age / 0.4)
        fade = min(1.0, (self.DURATION - self.age) / 0.4)
        alpha = 0.45 * fade

        tint = np.zeros_like(frame)
        tint[:] = (45, 15, 0)

        out = frame

        for sign in (-1, 1):
            matrix = np.float32([[1, 0, sign * reach], [0, 1, 0]])

            clone = cv2.warpAffine(
                frame, matrix, (w, h),
                borderMode=cv2.BORDER_REPLICATE
            )

            clone = cv2.add(clone, tint)

            out = cv2.addWeighted(out, 1.0 - alpha, clone, alpha, 0)

        # Smoke puffs.
        layer = np.zeros_like(out)
        alive = []

        for p in self.puffs:

            p[5] += dt

            if p[5] >= p[6]:
                continue

            p[0] += p[2] * dt
            p[1] += p[3] * dt

            progress = p[5] / p[6]
            radius = int(p[4] * (0.6 + 0.8 * progress))
            shade = int(200 * (1.0 - progress))

            cv2.circle(
                layer, (int(p[0]), int(p[1])), radius,
                (shade, shade, shade), -1, cv2.LINE_AA
            )

            alive.append(p)

        self.puffs = alive

        return _additive(out, layer, 6, 0.6)


# ==========================================================
# KAMEHAMEHA  (DOUBLE FIST -> DOUBLE PALM)
# ==========================================================

class KamehamehaEffect:
    """Charge an energy orb between both hands, then fire a beam."""

    BEAM_DURATION = 1.7

    def __init__(self):
        self.charge = 0.0
        self.beam_age = None
        self.origin = (0, 0)
        self.direction = (0.0, -1.0)
        self.angle = 0.0

    @property
    def active(self):
        return self.beam_age is not None

    def fire(self, origin, direction):
        self.beam_age = 0.0
        self.origin = (int(origin[0]), int(origin[1]))
        self.direction = direction
        self.charge = 0.0

    def stop(self):
        self.beam_age = None
        self.charge = 0.0

    def _draw_orb(self, frame, center, radius, strength):

        layer = np.zeros_like(frame)

        r = int(radius)
        flicker = 1.0 + 0.08 * math.sin(self.angle * 3)

        cv2.circle(layer, center, int(r * 1.3 * flicker),
                   (255, 150, 40), -1, cv2.LINE_AA)
        cv2.circle(layer, center, int(r * 0.85),
                   (255, 215, 140), -1, cv2.LINE_AA)
        cv2.circle(layer, center, int(r * 0.45),
                   (255, 255, 255), -1, cv2.LINE_AA)

        layer = cv2.convertScaleAbs(layer, alpha=0.4 + 0.6 * strength)

        return _additive(frame, layer, max(3.0, r * 0.35), 0.9)

    def render(self, frame, pose, gesture, dt):

        dt = _clamp_dt(dt)
        self.angle += dt * 10.0

        h, w = frame.shape[:2]

        # Charging phase.
        if self.beam_age is None:

            if gesture == "DOUBLE FIST" and pose is not None:
                self.charge = min(1.0, self.charge + dt / 1.2)
            else:
                self.charge = max(0.0, self.charge - dt * 1.5)

            if self.charge > 0.03 and pose is not None:
                frame = self._draw_orb(
                    frame,
                    pose[0],
                    14 + 46 * self.charge,
                    self.charge
                )

            return frame

        # Beam phase.
        self.beam_age += dt

        if self.beam_age >= self.BEAM_DURATION:
            self.stop()
            return frame

        age = self.beam_age

        ox, oy = self.origin
        dx, dy = self.direction

        reach = math.hypot(w, h) * min(1.0, age / 0.15)
        end = (int(ox + dx * reach), int(oy + dy * reach))

        fade = min(1.0, (self.BEAM_DURATION - age) / 0.4)
        pulse = 1.0 + 0.12 * math.sin(age * 60)

        width = int(max(6, 70 * fade * pulse))

        layer = np.zeros_like(frame)

        cv2.line(layer, self.origin, end, (255, 150, 40),
                 width, cv2.LINE_AA)
        cv2.line(layer, self.origin, end, (255, 215, 140),
                 max(2, int(width * 0.6)), cv2.LINE_AA)
        cv2.line(layer, self.origin, end, (255, 255, 255),
                 max(1, int(width * 0.3)), cv2.LINE_AA)

        cv2.circle(layer, self.origin, int(width * 0.9),
                   (255, 215, 140), -1, cv2.LINE_AA)
        cv2.circle(layer, self.origin, int(width * 0.45),
                   (255, 255, 255), -1, cv2.LINE_AA)

        # Small screen shake while the beam fires.
        shake = 6.0 * fade

        matrix = np.float32([
            [1, 0, random.uniform(-shake, shake)],
            [0, 1, random.uniform(-shake, shake)],
        ])

        frame = cv2.warpAffine(
            frame, matrix, (w, h),
            borderMode=cv2.BORDER_REPLICATE
        )

        return _additive(frame, layer, 12, 1.0)


# ==========================================================
# MANDALA SHIELD  (FOUR FINGERS -> OPEN PALM)
# ==========================================================

class MandalaShieldEffect:
    """Rotating magic circle that follows your palm until you make a fist."""

    def __init__(self):
        self.active = False
        self.age = 0.0
        self.angle = 0.0
        self.position = None
        self.radius = None
        self.sparks = []
        self.fist_for = 0.0
        self.lost_for = 0.0

    def start(self):
        self.active = True
        self.age = 0.0
        self.position = None
        self.radius = None
        self.sparks = []
        self.fist_for = 0.0
        self.lost_for = 0.0

    def stop(self):
        self.active = False
        self.sparks = []

    @staticmethod
    def _polygon(layer, c, radius, sides, rotation, color, thickness):

        points = np.array([
            (
                int(c[0] + math.cos(rotation + 2 * math.pi * k / sides) * radius),
                int(c[1] + math.sin(rotation + 2 * math.pi * k / sides) * radius),
            )
            for k in range(sides)
        ], dtype=np.int32)

        cv2.polylines(layer, [points], True, color, thickness, cv2.LINE_AA)

    def render(self, frame, palm, dt, gesture, has_hand):

        if not self.active:
            return frame

        dt = _clamp_dt(dt)

        self.age += dt
        self.angle += dt * 1.6

        # Dismiss with a held fist, or when the hand disappears.
        self.fist_for = self.fist_for + dt if gesture == "FIST" else 0.0
        self.lost_for = 0.0 if has_hand else self.lost_for + dt

        if self.fist_for > 0.4 or self.lost_for > 1.0:
            self.stop()
            return frame

        if palm is None:
            return frame

        center, radius = palm

        if self.position is None:
            self.position = [float(center[0]), float(center[1])]
            self.radius = float(radius)
        else:
            self.position[0] += (center[0] - self.position[0]) * 0.45
            self.position[1] += (center[1] - self.position[1]) * 0.45
            self.radius += (radius - self.radius) * 0.25

        r = self.radius * 1.7 * _ease_out(self.age / 0.5)

        if r < 10:
            return frame

        c = (int(self.position[0]), int(self.position[1]))

        gold = (60, 190, 255)
        orange = (30, 120, 255)

        layer = np.zeros_like(frame)

        # Concentric circles.
        cv2.circle(layer, c, int(r), orange, 3, cv2.LINE_AA)
        cv2.circle(layer, c, int(r * 0.92), gold, 1, cv2.LINE_AA)
        cv2.circle(layer, c, int(r * 0.62), orange, 2, cv2.LINE_AA)
        cv2.circle(layer, c, int(r * 0.30), gold, 1, cv2.LINE_AA)

        # Rune ticks around the ring.
        for i in range(36):
            a = self.angle + i * math.pi / 18

            r1 = r * 0.92
            r2 = r * (0.98 if i % 3 else 1.06)

            cv2.line(
                layer,
                (int(c[0] + math.cos(a) * r1), int(c[1] + math.sin(a) * r1)),
                (int(c[0] + math.cos(a) * r2), int(c[1] + math.sin(a) * r2)),
                gold, 2, cv2.LINE_AA
            )

        # Counter-rotating geometry.
        self._polygon(layer, c, r * 0.88, 3, -self.angle * 1.3, gold, 2)
        self._polygon(layer, c, r * 0.88, 3, -self.angle * 1.3 + math.pi / 3, gold, 2)
        self._polygon(layer, c, r * 0.60, 4, self.angle * 1.8, orange, 2)
        self._polygon(layer, c, r * 0.60, 4, self.angle * 1.8 + math.pi / 4, orange, 2)

        # Sparks flying off the ring.
        for _ in range(4):
            a = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 220)

            # x, y, vx, vy, age, life
            self.sparks.append([
                c[0] + math.cos(a) * r,
                c[1] + math.sin(a) * r,
                math.cos(a) * speed + random.uniform(-40, 40),
                math.sin(a) * speed + random.uniform(-40, 40),
                0.0,
                random.uniform(0.3, 0.8),
            ])

        alive = []

        for s in self.sparks:
            s[4] += dt

            if s[4] >= s[5]:
                continue

            s[0] += s[2] * dt
            s[1] += s[3] * dt

            fade = 1.0 - s[4] / s[5]

            cv2.circle(
                layer, (int(s[0]), int(s[1])),
                max(1, int(3 * fade)),
                gold, -1, cv2.LINE_AA
            )

            alive.append(s)

        self.sparks = alive[:200]

        return _additive(frame, layer, 5, 0.9)


# ==========================================================
# HEALING AURA  (THREE FINGERS -> OPEN PALM)
# ==========================================================

class HealingAuraEffect:
    """Golden light and sparkles rise up the screen."""

    DURATION = 3.2

    def __init__(self):
        self.active = False
        self.age = 0.0
        self.particles = []
        self._glow = None

    def start(self):
        self.active = True
        self.age = 0.0
        self.particles = []

    def stop(self):
        self.active = False
        self.particles = []

    def _build_glow(self, shape):

        h, w = shape[:2]

        if self._glow is not None and self._glow.shape[:2] == (h, w):
            return

        gradient = (np.linspace(0.0, 1.0, h, dtype=np.float32) ** 3)[:, None]

        glow = np.zeros((h, w, 3), dtype=np.float32)
        glow[..., 0] = 40 * gradient
        glow[..., 1] = 150 * gradient
        glow[..., 2] = 255 * gradient

        self._glow = glow.astype(np.uint8)

    def render(self, frame, dt):

        if not self.active:
            return frame

        dt = _clamp_dt(dt)
        self.age += dt

        if self.age >= self.DURATION:
            self.stop()
            return frame

        h, w = frame.shape[:2]

        # Warm light rising from the bottom of the screen.
        self._build_glow(frame.shape)

        alpha = (
            0.6
            * min(1.0, self.age / 0.5)
            * min(1.0, (self.DURATION - self.age) / 0.8)
        )

        frame = cv2.add(
            frame,
            cv2.convertScaleAbs(self._glow, alpha=alpha)
        )

        # Rising sparkles.
        if self.age < self.DURATION - 0.8:
            for _ in range(10):

                # x, y, vx, vy, radius, age, life, phase
                self.particles.append([
                    random.uniform(0, w),
                    h + 5.0,
                    random.uniform(-20, 20),
                    random.uniform(-190, -70),
                    random.uniform(2, 5),
                    0.0,
                    random.uniform(1.4, 2.6),
                    random.uniform(0, 2 * math.pi),
                ])

        layer = np.zeros_like(frame)
        alive = []

        for p in self.particles:

            p[5] += dt

            if p[5] >= p[6]:
                continue

            p[0] += (p[2] + 25 * math.sin(p[7] + p[5] * 4)) * dt
            p[1] += p[3] * dt

            progress = p[5] / p[6]
            fade = math.sin(math.pi * progress)

            color = (int(90 * fade), int(220 * fade), int(255 * fade))

            x, y = int(p[0]), int(p[1])
            radius = max(1, int(p[4]))

            cv2.circle(layer, (x, y), radius, color, -1, cv2.LINE_AA)

            # Little sparkle cross.
            cv2.line(layer, (x - radius * 2, y), (x + radius * 2, y),
                     color, 1, cv2.LINE_AA)
            cv2.line(layer, (x, y - radius * 2), (x, y + radius * 2),
                     color, 1, cv2.LINE_AA)

            alive.append(p)

        self.particles = alive[:400]

        return _additive(frame, layer, 4, 0.8)


# ==========================================================
# WEB SHOT  (LOVE SIGN -> GUN SIGN)
# ==========================================================

class WebShotEffect:
    """A web strand shoots from your hand and splats on the screen edge."""

    DURATION = 2.2

    def __init__(self):
        self.active = False
        self.age = 0.0
        self.origin = (0, 0)
        self.direction = (0.0, -1.0)

    @staticmethod
    def direction_from_landmarks(landmarks):
        wrist = landmarks[0]
        tip = landmarks[8]

        return _unit(tip.x - wrist.x, tip.y - wrist.y)

    def start(self, origin, direction):
        self.active = True
        self.age = 0.0
        self.origin = (int(origin[0]), int(origin[1]))
        self.direction = direction

    def stop(self):
        self.active = False

    def render(self, frame, dt):

        if not self.active:
            return frame

        dt = _clamp_dt(dt)
        self.age += dt

        if self.age >= self.DURATION:
            self.stop()
            return frame

        h, w = frame.shape[:2]

        ox, oy = self.origin
        dx, dy = self.direction

        # Distance from the hand to the screen edge in this direction.
        candidates = []

        if dx > 1e-6:
            candidates.append((w - 1 - ox) / dx)
        elif dx < -1e-6:
            candidates.append((0 - ox) / dx)

        if dy > 1e-6:
            candidates.append((h - 1 - oy) / dy)
        elif dy < -1e-6:
            candidates.append((0 - oy) / dy)

        positives = [c for c in candidates if c > 0]

        reach = max(80.0, min(positives) - 30) if positives else 300.0

        travel = reach * min(1.0, self.age / 0.12)

        fade = min(1.0, (self.DURATION - self.age) / 0.5)
        white = (int(255 * fade),) * 3

        layer = np.zeros_like(frame)

        # Wobbling strand that settles quickly.
        amplitude = 8.0 * max(0.0, 1.0 - self.age / 0.6)

        points = []

        for i in range(25):
            t = i / 24
            wave = math.sin(t * math.pi * 3 + self.age * 25) * amplitude

            points.append((
                int(ox + dx * travel * t - dy * wave),
                int(oy + dy * travel * t + dx * wave),
            ))

        cv2.polylines(
            layer,
            [np.array(points, dtype=np.int32)],
            False, white, 2, cv2.LINE_AA
        )

        # Web splat at the end of the strand.
        if self.age > 0.12:

            grow = _ease_out((self.age - 0.12) / 0.25)
            radius = 95 * grow

            ex = int(ox + dx * travel)
            ey = int(oy + dy * travel)

            base = 0.3

            for k in range(8):
                a = base + 2 * math.pi * k / 8

                cv2.line(
                    layer, (ex, ey),
                    (int(ex + math.cos(a) * radius),
                     int(ey + math.sin(a) * radius)),
                    white, 1, cv2.LINE_AA
                )

            for ring in (0.35, 0.65, 1.0):
                rr = radius * ring

                for k in range(8):
                    a1 = base + 2 * math.pi * k / 8
                    a2 = base + 2 * math.pi * (k + 1) / 8
                    am = (a1 + a2) / 2

                    p1 = (int(ex + math.cos(a1) * rr), int(ey + math.sin(a1) * rr))
                    pm = (int(ex + math.cos(am) * rr * 0.86), int(ey + math.sin(am) * rr * 0.86))
                    p2 = (int(ex + math.cos(a2) * rr), int(ey + math.sin(a2) * rr))

                    cv2.polylines(
                        layer,
                        [np.array([p1, pm, p2], dtype=np.int32)],
                        False, white, 1, cv2.LINE_AA
                    )

        return _additive(frame, layer, 3, 0.5)
