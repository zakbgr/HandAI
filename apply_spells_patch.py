import shutil
import sys
from pathlib import Path

path = Path("main.py")
lines = path.read_text().split("\n")

if any("lightning = LightningEffect()" in line for line in lines):
    sys.exit("main.py is already patched.")

# (anchor line, where to insert, lines to insert)
EDITS = [
    ("from rasengan_effects import RasenganEffect", "after", [
        "from lightning_effects import LightningEffect",
        "from ice_effects import IceBlastEffect",
    ]),
    ("rasengan = RasenganEffect()", "after", [
        "lightning = LightningEffect()",
        "ice = IceBlastEffect()",
    ]),
    ("palm = None", "after", [
        "index_tip = None",
    ]),
    ('status = "Detection paused"', "after", [
        "lightning.stop()",
        "ice.stop()",
    ]),
    ("frame_h, frame_w = frame.shape[:2]", "after", [
        "index_tip = (",
        "    int(result.hand_landmarks[0][8].x * frame_w),",
        "    int(result.hand_landmarks[0][8].y * frame_h)",
        ")",
    ]),
    ('elif activated == "RASENGAN":', "before", [
        'elif activated == "LIGHTNING":',
        "",
        "    lightning.start()",
        '    status = "LIGHTNING STRIKE!"',
        "",
        'elif activated == "ICE BLAST":',
        "",
        "    if palm is not None:",
        "        ice.start(",
        "            palm[0],",
        "            IceBlastEffect.direction_from_landmarks(",
        "                result.hand_landmarks[0]",
        "            )",
        "        )",
        '    status = "ICE BLAST!"',
        "",
    ]),
    ("# Rasengan in the palm.", "before", [
        "# Lightning and ice effects.",
        "frame = lightning.render(frame, index_tip, effect_dt)",
        "frame = ice.render(frame, effect_dt)",
        "",
    ]),
]

plan = []

for anchor, mode, block in EDITS:

    hits = [i for i, l in enumerate(lines) if l.strip() == anchor]

    if len(hits) != 1:
        sys.exit(
            f"Cannot patch: found {len(hits)} matches for: {anchor}\n"
            "Nothing was changed."
        )

    index = hits[0]
    line = lines[index]
    indent = line[:len(line) - len(line.lstrip())]

    position = index + 1 if mode == "after" else index

    plan.append((position, [indent + b if b else "" for b in block]))

# Apply from the bottom up so earlier positions stay valid.
for position, new_lines in sorted(plan, key=lambda item: item[0], reverse=True):
    lines[position:position] = new_lines

shutil.copy("main.py", "main.py.bak_spells")
path.write_text("\n".join(lines))

print("main.py patched. Backup saved as main.py.bak_spells")
