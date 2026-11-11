import shutil
import sys
from pathlib import Path


def norm(text):
    return text.strip().replace(" ", "")


def apply_edits(lines, edits, name):

    plan = []

    for anchor, mode, block in edits:

        hits = [i for i, l in enumerate(lines) if norm(l) == norm(anchor)]

        if len(hits) != 1:
            sys.exit(
                f"Cannot patch {name}: found {len(hits)} matches for: {anchor}\n"
                "Nothing was changed."
            )

        index = hits[0]
        line = lines[index]
        indent = line[:len(line) - len(line.lstrip())]

        position = index + 1 if mode == "after" else index

        plan.append((position, [indent + b if b else "" for b in block]))

    for position, new_lines in sorted(plan, key=lambda item: item[0], reverse=True):
        lines[position:position] = new_lines

    return lines


# ----------------------------------------------------------
# Load files
# ----------------------------------------------------------

FILES = {
    "main": Path("main.py"),
    "finger": Path("finger_detection.py"),
    "engine": Path("spell_engine.py"),
}

for p in list(FILES.values()) + [Path("more_effects.py")]:
    if not p.exists():
        sys.exit(f"Missing file: {p}")

main_lines = FILES["main"].read_text().split("\n")
finger_lines = FILES["finger"].read_text().split("\n")
engine_lines = FILES["engine"].read_text().split("\n")

if any("kame = KamehamehaEffect()" in l for l in main_lines):
    sys.exit("Already patched.")

if not any("lightning = LightningEffect()" in l for l in main_lines):
    sys.exit("Run apply_spells_patch.py first (lightning and ice are missing).")


# ----------------------------------------------------------
# finger_detection.py: new hand signs
# ----------------------------------------------------------

def sign(comment, name, thumb, index, middle, ring, pinky):

    def cond(label, value):
        return ("    " if value else "    not ").replace("    ", "    ", 1) + label

    lines = [comment, "if ("]

    states = [
        ("thumb", thumb), ("index", index), ("middle", middle),
        ("ring", ring), ("pinky", pinky),
    ]

    for i, (label, value) in enumerate(states):
        prefix = "    " if i == 0 else "    and "
        lines.append(prefix + ("" if value else "not ") + label)

    lines += ["):", f'    return "{name}"', ""]

    return lines


finger_block = (
    sign("# Three fingers.", "THREE FINGERS", False, True, True, True, False)
    + sign("# Four fingers.", "FOUR FINGERS", False, True, True, True, True)
    + sign("# Shaka.", "SHAKA", True, False, False, False, True)
    + sign("# Love sign.", "LOVE SIGN", True, True, False, False, True)
    + sign("# Gun sign.", "GUN SIGN", True, True, False, False, False)
    + sign("# Pinky up.", "PINKY UP", False, False, False, False, True)
)

finger_lines = apply_edits(finger_lines, [
    ('return "UNKNOWN GESTURE"', "before", finger_block),
], "finger_detection.py")


# ----------------------------------------------------------
# spell_engine.py: new spells
# ----------------------------------------------------------

def spell(name, sequence, effect, description):
    seq = ", ".join(f'"{g}"' for g in sequence)

    return [
        f'"{name}": {{',
        f'    "sequence": [{seq}],',
        f'    "effect": "{effect}",',
        f'    "description": "{description}",',
        "},",
    ]


engine_block = (
    spell("SHADOW CLONE", ["DOUBLE PEACE"], "CLONE", "Summon shadow clones!")
    + spell("KAMEHAMEHA", ["DOUBLE FIST", "DOUBLE PALM"], "BEAM", "Fire an energy wave!")
    + spell("MANDALA SHIELD", ["FOUR FINGERS", "OPEN PALM"], "SHIELD", "Conjure a magic circle!")
    + spell("WEB SHOT", ["LOVE SIGN", "GUN SIGN"], "WEB", "Shoot a web!")
    + spell("HEALING AURA", ["THREE FINGERS", "OPEN PALM"], "HEAL", "Bathe in golden light!")
)

engine_lines = apply_edits(engine_lines, [
    ('"RASENGAN": {', "before", engine_block),
], "spell_engine.py")


# ----------------------------------------------------------
# main.py: wiring
# ----------------------------------------------------------

main_edits = [

    ("from ice_effects import IceBlastEffect", "after", [
        "from more_effects import (",
        "    DOUBLE_GESTURES,",
        "    ShadowCloneEffect,",
        "    KamehamehaEffect,",
        "    MandalaShieldEffect,",
        "    WebShotEffect,",
        "    HealingAuraEffect,",
        "    two_hand_pose,",
        ")",
    ]),

    ("ice = IceBlastEffect()", "after", [
        "clone = ShadowCloneEffect()",
        "kame = KamehamehaEffect()",
        "shield = MandalaShieldEffect()",
        "web = WebShotEffect()",
        "heal = HealingAuraEffect()",
    ]),

    ("index_tip = None", "after", [
        "pose = None",
    ]),

    ('status = "Detection paused"', "after", [
        "clone.stop()",
        "kame.stop()",
        "shield.stop()",
        "web.stop()",
        "heal.stop()",
    ]),

    ("frame_h, frame_w = frame.shape[:2]", "after", [
        "pose = two_hand_pose(result, frame_w, frame_h)",
    ]),

    ('elif activated == "RASENGAN":', "before", [
        'elif activated == "SHADOW CLONE":',
        "",
        "    clone.start()",
        '    status = "SHADOW CLONE JUTSU!"',
        "",
        'elif activated == "KAMEHAMEHA":',
        "",
        "    if pose is not None:",
        "        kame.fire(pose[0], pose[1])",
        "    elif palm is not None:",
        "        kame.fire(",
        "            palm[0],",
        "            IceBlastEffect.direction_from_landmarks(",
        "                result.hand_landmarks[0]",
        "            )",
        "        )",
        '    status = "KAMEHAMEHA!"',
        "",
        'elif activated == "MANDALA SHIELD":',
        "",
        "    shield.start()",
        '    status = "MANDALA SHIELD!"',
        "",
        'elif activated == "WEB SHOT":',
        "",
        "    if palm is not None:",
        "        web.start(",
        "            palm[0],",
        "            WebShotEffect.direction_from_landmarks(",
        "                result.hand_landmarks[0]",
        "            )",
        "        )",
        '    status = "WEB SHOT!"',
        "",
        'elif activated == "HEALING AURA":',
        "",
        "    heal.start()",
        '    status = "HEALING AURA!"',
        "",
    ]),

    ("# Rasengan in the palm.", "before", [
        "# More spell effects.",
        "frame = clone.render(frame, effect_dt)",
        "frame = heal.render(frame, effect_dt)",
        "frame = web.render(frame, effect_dt)",
        "frame = kame.render(frame, pose, gesture, effect_dt)",
        "frame = shield.render(",
        "    frame, palm, effect_dt, gesture, hands_count > 0",
        ")",
        "",
    ]),

    # Two-handed signs in draw_landmarks().
    ('current_gesture = "NO HAND"', "after", [
        "gestures = []",
    ]),

    ("if hand_index == 0:", "before", [
        "gestures.append(gesture)",
    ]),

    ("return frame , current_gesture", "before", [
        "# Two-handed signs: both hands making the same gesture.",
        "if len(gestures) == 2 and gestures[0] == gestures[1]:",
        "    double = DOUBLE_GESTURES.get(gestures[0])",
        "",
        "    if double:",
        "        current_gesture = double",
        "",
    ]),
]

main_lines = apply_edits(main_lines, main_edits, "main.py")


# ----------------------------------------------------------
# Everything checked: back up and write
# ----------------------------------------------------------

for key, new_lines in (
    ("main", main_lines),
    ("finger", finger_lines),
    ("engine", engine_lines),
):
    path = FILES[key]
    shutil.copy(path, str(path) + ".bak_more")
    path.write_text("\n".join(new_lines))

print("Patched main.py, finger_detection.py and spell_engine.py.")
print("Backups saved with the .bak_more extension.")
