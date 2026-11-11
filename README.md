# 🐉 HandAI — Gesture-Controlled Magic System

**Turn your hands into magic.**

HandAI is a Python-based computer vision project that transforms real-world hand gestures into magical abilities and visual effects in real time.

Using your webcam, MediaPipe hand tracking, and custom gesture recognition, you can cast spells, summon shadow clones, launch energy beams, create magical shields, and unleash fire — all through hand movements.

No controllers. No keyboard shortcuts. Just gestures.

---

## ✨ Features

- **Real-Time Hand Tracking:** Detect and track hand landmarks using your webcam.
- **Gesture Recognition:** Recognize multiple hand signs based on finger positions.
- **Spell Sequences:** Combine hand gestures in specific sequences to activate spells.
- **Two-Handed Gestures:** Recognize synchronized gestures using both hands.
- **Face Tracking:** Track facial position for face-aware visual effects.
- **Magical Visual Effects:** Fire, lightning, ice, energy orbs, shields, smoke, and particle animations.
- **Interactive Effects:** Some spells follow hand positions and pointing directions.
- **Real-Time Rendering:** Display visual effects directly on the webcam feed.

---

## 🪄 Spellbook — 9 Spells

| Spell | Gesture Sequence | Effect |
|---|---|---|
| 🔥 FIREBALL | Fist → Fist → Rock Sign | Fire erupts from your mouth |
| ⚡ LIGHTNING | Open Palm → Fist → Pointing | Lightning strikes your fingertip |
| ❄️ ICE BLAST | Thumbs Up → Fist → Open Palm | Ice shards and frost effects |
| 🔵 RASENGAN | Peace → Fist → Open Palm | Spinning energy sphere in your palm |
| 👥 SHADOW CLONE | Double Peace | Summons two translucent clones |
| ☄️ KAMEHAMEHA | Double Fist → Double Palm | Charges and fires an energy beam |
| 🛡️ MANDALA SHIELD | Four Fingers → Open Palm | Creates a rotating magical shield |
| 🕸️ WEB SHOT | Love Sign → Gun Sign | Shoots a web toward the screen edge |
| ✨ HEALING AURA | Three Fingers → Open Palm | Golden light and rising sparkles |

---

## ✋ Hand Gesture Recognition

HandAI supports the following hand signs:

| Gesture | Finger Configuration |
|---|---|
| FIST | All fingers closed |
| OPEN PALM | All five fingers extended |
| PEACE SIGN | Index + Middle |
| POINTING | Index finger |
| THUMBS UP | Thumb only |
| ROCK SIGN | Index + Pinky |
| THREE FINGERS | Index + Middle + Ring |
| FOUR FINGERS | Four fingers, thumb folded |
| SHAKA | Thumb + Pinky |
| LOVE SIGN | Thumb + Index + Pinky |
| GUN SIGN | Thumb + Index |
| PINKY UP | Pinky only |

### Two-Handed Gestures

- DOUBLE FIST
- DOUBLE PALM
- DOUBLE PEACE
- DOUBLE POINT

---

## 🛠️ Technologies

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| OpenCV | Webcam access, image processing, and visual effects |
| MediaPipe | Real-time hand landmark detection |
| NumPy | Mathematical and image operations |

---

## 📂 Project Structure

```text
HandAI/
│
├── main.py                     # Main application
│
├── finger_detection.py         # Hand gesture recognition
├── face_tracking.py             # Face tracking
│
├── spell_engine.py              # Spell sequences and activation
│
├── fire_effects.py              # Fire visual effects
├── lightning_effects.py         # Lightning effects
├── ice_effects.py               # Ice and frost effects
├── rasengan_effects.py          # Rasengan energy effects
├── more_effects.py              # Additional magical effects
│
├── models/                      # Model files
├── backups/                     # Project backups
│
├── test_camera.py               # Camera testing
├── test_dragon_breath.py        # Dragon breath testing
├── test_face_tracking.py        # Face tracking tests
├── test_fire_effects.py         # Fire effect tests
├── test_spell_engine.py         # Spell engine tests
│
├── apply_spells_patch.py        # Spell integration patch
├── apply_more_patch.py          # Additional spell integration
│
├── requirements.txt             # Python dependencies
└── README.md
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/zakbgr/HandAI.git
cd HandAI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

**Linux / Fedora:**

```bash
source .venv/bin/activate
```

**Windows:**

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run HandAI

```bash
python main.py
```

Make sure your webcam is connected and accessible.

---

## 🎮 How to Use

1. Start the application.
2. Allow access to your webcam.
3. Position your hands within the camera frame.
4. Perform one of the recognized hand signs.
5. Complete the required gesture sequence.
6. Watch your spell activate!

### Tips

- Keep your hands visible inside the camera frame.
- Use good lighting for better gesture recognition.
- Hold two-handed gestures simultaneously.
- For Kamehameha, hold Double Fist to charge, then switch to Double Palm.
- For Mandala Shield, hold a fist to dismiss the effect.
- Point your fingers in the desired direction when aiming.

---

## 🧪 Testing

HandAI includes individual testing scripts:

```bash
python test_camera.py
python test_fire_effects.py
python test_dragon_breath.py
python test_face_tracking.py
python test_spell_engine.py
```

These scripts help test individual project components.

---

## 🔮 Future Improvements

Planned possibilities for future development:

- 🔊 Sound effects for every spell.
- 📖 Interactive on-screen spellbook.
- 👤 More advanced face-aware effects.
- 🧙 Custom gesture combinations.
- 🎆 More advanced particle systems.
- 🎥 Improved tracking accuracy and performance.
- 🎮 Customizable gesture-to-spell mapping.
- 🪄 New spells and two-handed abilities.

---

## 🎯 Project Vision

HandAI explores the possibilities of combining artificial intelligence, computer vision, and interactive visual effects to create an immersive gesture-controlled experience.

The idea is to transform ordinary hand movements into extraordinary digital experiences.

**Make computer vision feel like magic.**

---

## 👨‍💻 Author

**Zakbgr**

- GitHub: [@zakbgr](https://github.com/zakbgr)
- Repository: [HandAI](https://github.com/zakbgr/HandAI)

---

⭐ If you like this project, consider giving it a star on GitHub!

