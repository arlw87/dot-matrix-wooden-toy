# Product Requirements Document: Dot Matrix Wooden Toy

## 1. Product Overview

### What
An interactive wooden toy featuring a 16x16 RGB LED matrix display behind a wood veneer front. The child presses one of four large buttons, each triggering a unique colourful animation with matching sound effect.

### Who
Children aged approximately 2 years old. The toy is designed to be used unsupervised, so all safety requirements are paramount.

### Why
Toddlers enjoy simple cause-and-effect interactions. Pressing a button with a recognisable symbol and seeing a bright, animated response with sound provides engaging sensory feedback and encourages exploration.

---

## 2. Hardware Summary

| Component | Specification |
|-----------|--------------|
| Display & Controller | Pimoroni Stellar Unicorn — 16x16 RGB LED matrix with Raspberry Pi Pico 2 W |
| Input | 4x 30mm arcade push buttons (Heart, Star, Moon, Flower) |
| Power | 3.7V 2000mAh LiPo battery with TP4056 USB-C charger module |
| Power Switch | SPST slide switch |
| Speaker | Built-in 30mm 1W speaker (on Stellar Unicorn) via MAX98357 I2S amplifier |
| Enclosure | Birch plywood box (~140x180x40mm), 0.6mm maple/birch veneer over display window |

---

## 3. Feature List

### F1: Boot Animation
**As a** user, **I want** the toy to show a brief colourful animation when turned on, **so that** I know it has powered up successfully.

**Acceptance Criteria:**
- On power-on, a colourful animation plays for 1-2 seconds
- After the boot animation completes, the display goes to the idle state (off)
- Boot to idle-ready takes no more than 3 seconds total

---

### F2: Heart Animation
**As a** child, **I want** to press the heart button and see a beating pink heart with a heartbeat sound, **so that** I can enjoy the animation.

**Acceptance Criteria:**
- Pressing the heart button displays a pink heart shape on the 16x16 grid
- The heart animates with a pulsing "beat" effect (expand/contract)
- A heartbeat "lub-dub" WAV file (`sounds/heartbeat.wav`) plays via the built-in speaker
- Animation plays for approximately 5 seconds
- After the animation completes, the final frame holds on screen for 5 seconds, then returns to idle
- Colour: pink (e.g. RGB 255, 105, 180) with slight variation per play

---

### F3: Star Animation
**As a** child, **I want** to press the star button and see a bouncing, rotating yellow star with a sparkle sound, **so that** I can enjoy the animation.

**Acceptance Criteria:**
- Pressing the star button displays a yellow star shape on the 16x16 grid
- The star bounces (moves up/down) and rotates during the animation
- A sparkle/twinkle WAV file (`sounds/sparkle.wav`) plays via the speaker
- The star occupies roughly 70% of the display area
- Animation plays for approximately 5 seconds
- After the animation completes, the final frame holds on screen for 5 seconds, then returns to idle
- Slight variation on each play (e.g. rotation direction, bounce speed, shade of yellow)

---

### F4: Moon Animation (Night Sky Scene)
**As a** child, **I want** to press the moon button and see a night sky with a moon, stars, and a shooting star, **so that** I can enjoy the animation.

**Acceptance Criteria:**
- Pressing the moon button triggers a night sky scene
- A moon (blue/white) and several stars fade in over the first 1-2 seconds
- After the sky is established, a shooting star crosses the screen
- A gentle chime/twinkling WAV file (`sounds/nightsky.wav`) accompanies the animation
- Animation plays for approximately 5 seconds
- After the animation completes, the final frame (night sky) holds on screen for 5 seconds, then returns to idle
- Slight variation on each play (e.g. shooting star direction, star positions, moon brightness)

---

### F5: Flower Animation
**As a** child, **I want** to press the flower button and see a flower grow and bloom, **so that** I can enjoy the animation.

**Acceptance Criteria:**
- Pressing the flower button triggers a growing flower animation
- A stem grows upward from the bottom of the display
- Petals open outward from the top of the stem, forming a colourful bloom
- A nature-inspired WAV file (`sounds/flower.wav`) accompanies the animation
- Colour: green stem, multicoloured or pink/red petals
- Animation plays for approximately 5 seconds
- After the animation completes, the final frame (bloomed flower) holds on screen for 5 seconds, then returns to idle
- Slight variation on each play (e.g. petal colour, growth speed, number of leaves)

---

### F6: Idle State
**As a** user, **I want** the display to be off when no animation is playing, **so that** the toy looks like a plain wooden box and conserves power.

**Acceptance Criteria:**
- After any animation completes, the final frame holds on screen for 5 seconds
- After the hold period, the display turns off (all LEDs black)
- The display remains off until a button is pressed or the toy enters/exits sleep
- No sound plays during idle or the hold period

---

### F7: Button Interrupt
**As a** child, **I want** to press a different button while an animation is playing and see the new animation start immediately, **so that** I don't have to wait.

**Acceptance Criteria:**
- If a button is pressed during an animation or during the post-animation hold phase, the current state stops immediately
- The new animation starts within 100ms of the button press
- Any currently playing sound stops and the new animation's sound begins
- Pressing the same button that is currently playing/holding restarts that animation from the beginning

---

### F8: Auto-Sleep
**As a** parent, **I want** the toy to automatically enter a low-power sleep mode after 2 minutes of inactivity, **so that** the battery is conserved if my child walks away.

**Acceptance Criteria:**
- If no button is pressed for 2 minutes, the toy enters sleep mode
- The 2-minute idle timer starts after the display goes black (i.e. after the post-animation hold phase ends)
- In sleep mode, the display is off and power consumption is minimised
- Pressing any button wakes the toy from sleep
- On wake, the toy goes to idle state (no boot animation replay), ready for button input
- The 2-minute timer resets each time a button is pressed

---

### F9: Brightness Control
**As a** parent, **I want** to adjust the display brightness using the built-in buttons on the Stellar Unicorn, **so that** I can make it comfortable for my child's eyes or dim it for darker rooms.

**Acceptance Criteria:**
- The Stellar Unicorn's built-in brightness up/down buttons adjust display brightness
- Brightness has a sensible default (e.g. 50%)
- Brightness setting persists until power-off (does not need to persist across reboots)
- There is a minimum brightness floor (not fully off via brightness button, to avoid confusion with "broken")

---

### F10: Animation Variation
**As a** child, **I want** the animation to look slightly different each time I press the same button, **so that** it stays interesting.

**Acceptance Criteria:**
- Each animation introduces small random variations per play, such as:
  - Slight colour shift (e.g. pink hue varies +-10%)
  - Speed variation (e.g. beat rate, bounce speed, growth speed varies +-15%)
  - Positional variation (e.g. star positions in night sky, shooting star angle)
- Variations are subtle — the animation remains clearly recognisable each time
- The core shape, colour family, and sound are consistent

---

## 4. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Boot time | Power-on to idle-ready in under 3 seconds |
| Button responsiveness | Animation starts within 100ms of button press |
| Animation frame rate | Minimum 15 fps for smooth animation |
| Battery life | 3-4 hours of continuous play on a full charge |
| Speaker volume | Fixed at a moderate, child-safe level (~40-50% of max) |
| Brightness default | 50%, adjustable via hardware buttons |
| Auto-sleep timeout | 2 minutes of inactivity |
| Safety | No exposed electronics, no overheating, non-toxic materials |
| Flash storage | All WAV files + code + firmware must fit within 4MB flash |

---

## 5. Software Architecture

### Language
MicroPython (Pimoroni firmware for Stellar Unicorn)

### File Structure
```
main.py                  — Boot sequence, main loop, button polling, sleep logic
animations/
  __init__.py            — Animation registry / lookup
  heart.py               — Heart animation frames + triggers heartbeat sound
  star.py                — Star animation frames + triggers sparkle sound
  moon.py                — Moon/night sky animation frames + triggers chime sound
  flower.py              — Flower animation frames + triggers nature sound
  boot.py                — Boot splash animation
sounds/
  heartbeat.wav          — Heartbeat "lub-dub" sound effect
  sparkle.wav            — Sparkle/twinkle sound effect
  nightsky.wav           — Gentle chime/twinkling sound effect
  flower.wav             — Nature-inspired chime sound effect
  boot.wav               — Boot splash sound (optional)
lib/
  display.py             — Shared display helpers (clear screen, draw sprite, etc.)
  sound.py               — WAV playback helpers (load WAV into bytearray, play via play_sample(), stop)
  buttons.py             — Button GPIO setup, debouncing, press detection
  sleep.py               — Auto-sleep timer, sleep/wake logic
```

### Audio Format Requirements
- WAV files must be **16-bit PCM, mono**
- Sample rate should be appropriate for Pico 2 W memory constraints (e.g. 16kHz or 22.05kHz)
- Total size of all WAV files must fit within the Pico 2 W's 4MB flash alongside MicroPython firmware and code
- Files are loaded into bytearrays and played via the Stellar Unicorn's `play_sample()` method

### Key Design Decisions
- **Each animation is self-contained**: exposes a `play(su, graphics)` function that handles both display and sound, yielding periodically to allow interrupt checking
- **Post-animation hold**: after the animation frames complete, the final frame remains on display for 5 seconds before returning to idle
- **Interrupt mechanism**: the main loop checks for button presses between animation frames and during the hold phase; if detected, the current animation returns early
- **Variation**: each animation's `play()` accepts or generates random parameters on each call
- **Sound playback**: WAV files are loaded from flash and played via `play_sample()`; playback is stopped on interrupt
- **Shared utilities**: common operations (clear screen, basic shapes, WAV loading) live in `lib/` to avoid duplication

---

## 6. Out of Scope (v1)

The following are explicitly **not** included in the initial prototype:
- WiFi features (remote animation updates, clock display)
- RFID card input
- Adjustable volume (fixed in software)
- More than 4 animations
- Persistent settings across reboots
- Parent/settings mode
- Games or interactive sequences beyond single-button-press → animation
