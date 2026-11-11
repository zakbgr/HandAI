
import time


class SpellSequenceEngine:

    NEUTRAL_GESTURES = {
        "UNKNOWN GESTURE",
        "NO HAND",
        "",
    }

    def __init__(
        self,
        stable_duration=0.20,
        sequence_timeout=3.0,
        cooldown=2.0,
    ):
        self.stable_duration = stable_duration
        self.sequence_timeout = sequence_timeout
        self.cooldown = cooldown

        self.spells = {
            "FIREBALL": {
                "sequence": ["FIST", "FIST", "ROCK SIGN"],
                "effect": "FIRE",
                "description": "Unleash a fireball!",
            },
            "LIGHTNING": {
                "sequence": ["OPEN PALM", "FIST", "POINTING"],
                "effect": "LIGHTNING",
                "description": "Summon lightning!",
            },
            "ICE BLAST": {
                "sequence": ["THUMBS UP", "FIST", "OPEN PALM"],
                "effect": "ICE",
                "description": "Unleash an ice blast!",
            },
                        "SHADOW CLONE": {
                            "sequence": ["DOUBLE PEACE"],
                            "effect": "CLONE",
                            "description": "Summon shadow clones!",
                        },
                        "KAMEHAMEHA": {
                            "sequence": ["DOUBLE FIST", "DOUBLE PALM"],
                            "effect": "BEAM",
                            "description": "Fire an energy wave!",
                        },
                        "MANDALA SHIELD": {
                            "sequence": ["FOUR FINGERS", "OPEN PALM"],
                            "effect": "SHIELD",
                            "description": "Conjure a magic circle!",
                        },
                        "WEB SHOT": {
                            "sequence": ["LOVE SIGN", "GUN SIGN"],
                            "effect": "WEB",
                            "description": "Shoot a web!",
                        },
                        "HEALING AURA": {
                            "sequence": ["THREE FINGERS", "OPEN PALM"],
                            "effect": "HEAL",
                            "description": "Bathe in golden light!",
                        },
                        "RASENGAN": {
                "sequence": ["PEACE SIGN", "FIST", "OPEN PALM"],
                "effect": "RASENGAN",
                "description": "Hold a spinning chakra sphere in your palm!",
            },
        }

        self.progress = {
            name: 0 for name in self.spells
        }

        self.candidate = None
        self.candidate_since = None
        self.last_emitted = None

        self.last_event_time = None
        self.cooldown_until = 0.0
        self.last_activated = None

    def reset_sequence(self):
        self.progress = {
            name: 0 for name in self.spells
        }
        self.last_event_time = None

    def get_progress(self):

        best = {
            "spell": None,
            "progress": 0,
            "total": 0,
        }

        for name, spell in self.spells.items():

            current = self.progress[name]

            if current > best["progress"]:
                best = {
                    "spell": name,
                    "progress": current,
                    "total": len(spell["sequence"]),
                }

        return best

    def update(self, gesture, now=None):

        if now is None:
            now = time.monotonic()

        gesture = (gesture or "").upper().strip()

        activated = None
        event = False

        # Sequence expiration.
        if (
            self.last_event_time is not None
            and now - self.last_event_time > self.sequence_timeout
        ):
            self.reset_sequence()

        # Stable gesture detection.
        if gesture != self.candidate:
            self.candidate = gesture
            self.candidate_since = now

        stable = (
            self.candidate_since is not None
            and now - self.candidate_since >= self.stable_duration
        )

        if stable:

            if gesture in self.NEUTRAL_GESTURES:
                self.last_emitted = None

            elif gesture != self.last_emitted:

                self.last_emitted = gesture
                event = True

                if now >= self.cooldown_until:

                    self.last_event_time = now

                    for name, spell in self.spells.items():

                        sequence = spell["sequence"]
                        position = self.progress[name]

                        if position < len(sequence):

                            if gesture == sequence[position]:
                                self.progress[name] += 1

                            elif gesture == sequence[0]:
                                self.progress[name] = 1

                    for name, spell in self.spells.items():

                        if self.progress[name] == len(spell["sequence"]):

                            activated = name
                            self.last_activated = name

                            self.cooldown_until = now + self.cooldown

                            self.reset_sequence()
                            break

        remaining = max(
            0.0,
            self.cooldown_until - now,
        )

        return {
            "gesture": gesture,
            "event": event,
            "activated": activated,
            "progress": self.get_progress(),
            "cooldown": round(remaining, 2),
            "ready": remaining <= 0,
        }

    def get_spellbook(self):

        return {
            name: {
                "sequence": spell["sequence"].copy(),
                "effect": spell["effect"],
                "description": spell["description"],
            }
            for name, spell in self.spells.items()
        }
