
from collections import deque


class GestureRecognizer:

    def __init__(self, history_size=5):

        self.history_size = history_size
        self.history = {}

    # --------------------------------------------------
    # DETECT INDIVIDUAL FINGERS
    # --------------------------------------------------

    def detect_fingers(self, landmarks, handedness):

        # Thumb: compare horizontal positions.
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]

        if handedness.lower() == "right":
            thumb_up = thumb_tip.x < thumb_ip.x - 0.015
        else:
            thumb_up = thumb_tip.x > thumb_ip.x + 0.015

        # Other four fingers.
        finger_pairs = {
            "index": (8, 6),
            "middle": (12, 10),
            "ring": (16, 14),
            "pinky": (20, 18)
        }

        states = {
            "thumb": thumb_up
        }

        for finger, (tip_id, joint_id) in finger_pairs.items():

            tip = landmarks[tip_id]
            joint = landmarks[joint_id]

            states[finger] = tip.y < joint.y - 0.015

        return states

    # --------------------------------------------------
    # SMOOTH FINGER DETECTION
    # --------------------------------------------------

    def smooth_states(self, hand_id, states):

        if hand_id not in self.history:

            self.history[hand_id] = deque(
                maxlen=self.history_size
            )

        history = self.history[hand_id]

        history.append(states.copy())

        smoothed = {}

        for finger in states:

            up_count = sum(
                1 for frame in history
                if frame[finger]
            )

            smoothed[finger] = (
                up_count > len(history) / 2
            )

        return smoothed

    # --------------------------------------------------
    # CLASSIFY GESTURE
    # --------------------------------------------------

    def classify_gesture(self, fingers):

        thumb = fingers["thumb"]
        index = fingers["index"]
        middle = fingers["middle"]
        ring = fingers["ring"]
        pinky = fingers["pinky"]

        # All five fingers extended.
        if all(fingers.values()):
            return "OPEN PALM"

        # All fingers closed.
        if not any(fingers.values()):
            return "FIST"

        # Peace sign.
        if (
            not thumb
            and index
            and middle
            and not ring
            and not pinky
        ):
            return "PEACE SIGN"

        # Pointing.
        if (
            not thumb
            and index
            and not middle
            and not ring
            and not pinky
        ):
            return "POINTING"

        # Thumbs up.
        if (
            thumb
            and not index
            and not middle
            and not ring
            and not pinky
        ):
            return "THUMBS UP"

        # Rock sign.
        if (
            not thumb
            and index
            and not middle
            and not ring
            and pinky
        ):
            return "ROCK SIGN"

        return "UNKNOWN GESTURE"

    # --------------------------------------------------
    # COMPLETE RECOGNITION PIPELINE
    # --------------------------------------------------

    def update(self, landmarks, handedness):

        raw_states = self.detect_fingers(
            landmarks,
            handedness
        )

        stable_states = self.smooth_states(
            handedness,
            raw_states
        )

        gesture = self.classify_gesture(
            stable_states
        )

        return stable_states, gesture
