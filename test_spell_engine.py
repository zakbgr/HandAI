
from spell_engine import SpellSequenceEngine


engine = SpellSequenceEngine()

clock = 0.0


def send(gesture):

    global clock

    clock += 0.05
    engine.update(gesture, now=clock)

    clock += 0.25
    result = engine.update(gesture, now=clock)

    progress = result["progress"]

    print(
        f"{gesture:15} | "
        f"{progress['spell'] or '-':12} | "
        f"{progress['progress']}/{progress['total']} | "
        f"{result['activated'] or '-'}"
    )

    if result["activated"]:
        print("\n🔥 FIREBALL ACTIVATED!\n")


print("\n===== FIREBALL TEST =====")

send("FIST")
send("OPEN PALM")
send("FIST")
send("OPEN PALM")
send("ROCK SIGN")


print("\n===== HOLD GESTURE TEST =====")

hold_engine = SpellSequenceEngine()

for t in [0.0, 0.1, 0.25, 0.5, 0.75, 1.0]:

    result = hold_engine.update("FIST", now=t)

    print(
        f"Time: {t:.2f}s | "
        f"New gesture event: {result['event']}"
    )


print("\n===== SPELLBOOK TEST =====")

for name, spell in engine.get_spellbook().items():

    print(f"\n{name}")
    print("Sequence:", " -> ".join(spell["sequence"]))
    print("Effect:", spell["effect"])
