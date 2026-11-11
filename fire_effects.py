
import cv2
import math
import random
import time


class FireParticle:
    def __init__(
        self,
        x,
        y,
        vx,
        vy,
        lifetime,
        radius,
    ):
        self.x = float(x)
        self.y = float(y)

        self.vx = float(vx)
        self.vy = float(vy)

        self.lifetime = lifetime
        self.age = 0.0

        self.radius = radius

    @property
    def alive(self):
        return self.age < self.lifetime


class FireParticleEngine:

    def __init__(self):

        self.particles = []

        self.max_particles = 900

        self.gravity = -35.0

        self.enabled = True

        self.last_update = None

    def clear(self):
        self.particles.clear()

    # --------------------------------------------------
    # CREATE PARTICLES
    # --------------------------------------------------

    def spawn_flame(self, x, y, count=8):

        if not self.enabled:
            return

        available = self.max_particles - len(self.particles)

        for _ in range(min(count, available)):

            self.particles.append(
                FireParticle(
                    x=x + random.uniform(-12, 12),
                    y=y + random.uniform(-5, 5),

                    vx=random.uniform(-65, 65),
                    vy=random.uniform(-240, -100),

                    lifetime=random.uniform(0.35, 0.85),
                    radius=random.uniform(5, 15),
                )
            )

    # --------------------------------------------------
    # FIREBALL BURST
    # --------------------------------------------------

    def burst(
        self,
        x,
        y,
        count=100,
        direction=(0.0, -1.0),
    ):

        if not self.enabled:
            return

        dx, dy = direction

        length = math.hypot(dx, dy)

        if length == 0:
            dx, dy = 0.0, -1.0
            length = 1.0

        dx /= length
        dy /= length

        available = self.max_particles - len(self.particles)

        for _ in range(min(count, available)):

            angle = random.uniform(-0.8, 0.8)

            speed = random.uniform(100, 450)

            # Rotate the direction slightly.
            vx = dx * math.cos(angle) - dy * math.sin(angle)
            vy = dx * math.sin(angle) + dy * math.cos(angle)

            self.particles.append(
                FireParticle(
                    x=x + random.uniform(-8, 8),
                    y=y + random.uniform(-8, 8),

                    vx=vx * speed,
                    vy=vy * speed,

                    lifetime=random.uniform(0.35, 1.0),
                    radius=random.uniform(4, 13),
                )
            )

    # --------------------------------------------------
    # PARTICLE COLORS
    # --------------------------------------------------

    @staticmethod
    def get_color(progress):

        # OpenCV uses BGR, not RGB.

        if progress < 0.25:
            return (0, 220, 255)       # Yellow

        if progress < 0.55:
            return (0, 100, 255)       # Orange

        if progress < 0.80:
            return (0, 45, 220)        # Deep orange

        return (30, 30, 130)           # Dark red

    # --------------------------------------------------
    # UPDATE PARTICLES
    # --------------------------------------------------

    def update(self, dt):

        dt = max(0.0, min(dt, 0.05))

        for particle in self.particles:

            particle.age += dt

            particle.vy += self.gravity * dt

            particle.x += particle.vx * dt
            particle.y += particle.vy * dt

            # Small random flame movement.
            particle.vx += random.uniform(-20, 20) * dt

        self.particles = [
            particle
            for particle in self.particles
            if particle.alive
        ]

    # --------------------------------------------------
    # RENDER FIRE
    # --------------------------------------------------

    def draw(self, frame):
       
        if not self.particles:
            return frame
        
        height, width = frame.shape[:2]

        glow = frame.copy()
        glow[:] = 0
        core = frame.copy()
        core[:] = 0 

        for particle in self.particles:

            if not particle.alive:
                continue

            progress = particle.age / particle.lifetime

            fade = 1.0 - progress

            radius = max(
                1,
                int(particle.radius * fade)
            )

            x = int(particle.x)
            y = int(particle.y)

            if not (0 <= x < width and 0 <= y < height):
                continue

            color = self.get_color(progress)

            # Outer glow.
            cv2.circle(
                glow,
                (x, y),
                radius * 3,
                color,
                -1,
                cv2.LINE_AA,
            )

            # Bright flame core.
            cv2.circle(
                core,
                (x, y),
                radius,
                (0, 180, 255),
                -1,
                cv2.LINE_AA,
            )

        # Blur glow layer.
        glow = cv2.GaussianBlur(
            glow,
            (21, 21),
            0,
        )

        # Composite the glow.
        result = cv2.addWeighted(
            frame, 1.0,
            glow, 0.65,
            0
        )

        result = cv2.addWeighted(
            result, 1.0,
            core, 0.75,
            0
        )

        return result

    # --------------------------------------------------
    # MAIN EFFECT UPDATE
    # --------------------------------------------------

    def render(
        self,
        frame,
        origin=None,
        active=False,
        dt=None,
    ):

        now = time.perf_counter()

        if dt is None:

            if self.last_update is None:
                dt = 1 / 30
            else:
                dt = now - self.last_update

        self.last_update = now

        dt = max(0.0, min(dt, 0.05))

        if active and origin is not None:

            x, y = origin

            self.spawn_flame(
                x,
                y,
                count=8,
            )

        self.update(dt)

        return self.draw(frame)
