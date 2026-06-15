# Product Requirements Document: Dot Matrix Wooden Toy

## 1. Product Overview

### What
An interactive wooden toy featuring a 16x16 RGB LED matrix display behind a wood veneer front. The child presses one of six large buttons, each triggering a unique colourful animation with matching sound effect. A separate Tilt Game mode — entered by double-tapping the toy — lets the child steer a bouncing ball by tilting the toy.

### Who
Children aged approximately 2 years old. The toy is designed to be used unsupervised, so all safety requirements are paramount.

### Why
Toddlers enjoy simple cause-and-effect interactions. Pressing a button with a recognisable symbol and seeing a bright, animated response with sound provides engaging sensory feedback and encourages exploration. The Tilt Game introduces a basic physical-digital interaction (tilt → ball moves) to extend play.

---

## 2. Hardware Summary

| Component | Specification |
|-----------|--------------|
| Display & Controller | Pimoroni Stellar Unicorn — 16x16 RGB LED matrix with Raspberry Pi Pico 2 W |
| Input | 6x arcade push buttons (Heart, Star, Flower, Fish, Rainbow, Sun) |
| Button I/O Expander | MCP23017 I2C GPIO expander (address 0x20, I2C0 on GP4/GP5), port B pins GPB0–GPB5 |
| Accelerometer | SparkFun KX134 Triple Axis Accelerometer (Qwiic/I2C, address 0x1F), shares I2C0 bus |
| Power | 3xAA battery holder with JST-PH connector (NiMH recommended) |
| Power Switch | SPST slide switch |
| Speaker | Built-in 30mm 1W speaker (on Stellar Unicorn) via MAX98357 I2S amplifier |
| Enclosure | Birch plywood box, wood veneer over display window |

**Veneer note:** The wood veneer absorbs green wavelengths more heavily than red, blue, or yellow. Animations must avoid relying on green as a primary colour.

---

## 3. Feature List

### F1: Boot Animation
**As a** user, **I want** the toy to show a brief colourful animation when turned on, **so that** I know it has powered up successfully.

**Acceptance Criteria:**
- On power-on, a colourful animation plays for 1-2 seconds
- After the boot animation completes, the display goes to the idle state (off)
- Boot to idle-ready takes no more than 3 seconds total
- A startup sound (`sounds/startup.wav`) plays during the boot animation

---

### F2: Heart Animation
**As a** child, **I want** to press the heart button and see a beating pink heart with a heartbeat sound, **so that** I can enjoy the animation.

**Acceptance Criteria:**
- Pressing the heart button displays a pink heart shape on the 16x16 grid
- The heart animates with a pulsing "beat" effect (expand/contract)
- `sounds/heartbeat.wav` plays via the built-in speaker
- Animation plays for approximately 5 seconds
- After the animation completes, the final frame holds on screen for 5 seconds (Hold Phase), then returns to Idle
- Colour: pink (e.g. RGB 255, 105, 180) with slight variation per play

---

### F3: Star Animation
**As a** child, **I want** to press the star button and see a bouncing, rotating yellow star with a sparkle sound, **so that** I can enjoy the animation.

**Acceptance Criteria:**
- Pressing the star button displays a yellow star shape on the 16x16 grid
- The star bounces (moves up/down) and rotates during the animation
- `sounds/star.wav` plays via the speaker
- The star occupies roughly 70% of the display area
- Animation plays for approximately 5 seconds
- After the animation completes, the final frame holds on screen for 5 seconds (Hold Phase), then returns to Idle
- Slight variation on each play (e.g. rotation direction, bounce speed, shade of yellow)

---

### F4: Flower Animation
**As a** child, **I want** to press the flower button and see a flower bloom open, **so that** I can enjoy the animation.

**Acceptance Criteria:**
- Pressing the flower button triggers a blooming flower animation
- Petals open outward from the centre of the display (no stem — avoid green)
- Petals use warm colours only (pink, red, orange, yellow) to ensure visibility through the veneer
- `sounds/flower.wav` plays via the speaker
- Animation plays for approximately 5 seconds
- After the animation completes, the final frame (fully open bloom) holds on screen for 5 seconds (Hold Phase), then returns to Idle
- Slight variation on each play (e.g. petal colour, bloom speed, number of petals)

---

### F5: Fish Animation
**As a** child, **I want** to press the fish button and see a fish swim across the screen, **so that** I can enjoy the animation.

**Acceptance Criteria:**
- Pressing the fish button displays a fish swimming across the 16x16 display
- The fish moves horizontally (left to right or right to left) with a gentle body wave
- Colour: bright orange body with blue/teal accents
- `sounds/fish.wav` plays via the speaker — sound brief: a light bubbly/underwater pop
- Animation plays for approximately 5 seconds
- After the animation completes, the final frame holds on screen for 5 seconds (Hold Phase), then returns to Idle
- Slight variation on each play (e.g. swim direction, speed, fin colour)

---

### F6: Rainbow Animation
**As a** child, **I want** to press the rainbow button and see a rainbow sweep across the screen, **so that** I can enjoy the animation.

**Acceptance Criteria:**
- Pressing the rainbow button triggers a sweeping rainbow animation
- Arcs of colour (ROYGBIV) sweep across or build up on the display
- Colour is bold and saturated — should be the most visually striking animation in the set
- `sounds/rainbow.wav` plays via the speaker — sound brief: a bright ascending chime sweep
- Animation plays for approximately 5 seconds
- After the animation completes, the final frame (full rainbow) holds on screen for 5 seconds (Hold Phase), then returns to Idle
- Slight variation on each play (e.g. sweep direction, speed)

---

### F7: Sun Animation
**As a** child, **I want** to press the sun button and see a glowing sun with radiating rays, **so that** I can enjoy the animation.

**Acceptance Criteria:**
- Pressing the sun button displays a central circle with rays radiating outward
- The sun pulses (brightness/size) and rays animate growing outward
- Colour: yellow/orange/white — warm and bright
- `sounds/sun.wav` plays via the speaker — sound brief: a warm bright "ping" or gentle chime
- Animation plays for approximately 5 seconds
- After the animation completes, the final frame holds on screen for 5 seconds (Hold Phase), then returns to Idle
- Slight variation on each play (e.g. pulse speed, number of rays, warmth of orange)

---

### F8: Tilt Game
**As a** child, **I want** to tilt the toy and see a ball roll around on the screen, **so that** I can enjoy physical play.

**Acceptance Criteria:**
- A double-tap on the toy body (detected via KX134 hardware double-tap interrupt) toggles the toy into Tilt Game mode
- A second double-tap exits Tilt Game mode and returns to Idle
- In Tilt Game mode:
  - A single-pixel ball is displayed on the 16x16 grid
  - The ball's velocity is driven by the KX134 X/Y tilt reading (gravity vector → acceleration → velocity → position)
  - The ball bounces elastically off all four display edges
  - The ball's colour shifts based on direction of movement (e.g. HSV hue follows velocity angle)
  - Each pixel the ball passes through leaves a fading trail — trail pixels dim over several frames until black
  - A short `sounds/bounce.wav` plays on each wall collision — sound brief: a soft physical thud/click
  - The six Animation Buttons are ignored entirely while in Tilt Game mode
  - Any Tilt Activity (ball moving above a minimum velocity threshold) resets the auto-sleep timer
  - If the toy is left completely still, auto-sleep applies as normal (2-minute timeout)
- Fallback entry/exit mechanism if double-tap detection proves unreliable: simultaneous long-press (2+ seconds) of any two Animation Buttons

---

### F9: Idle State
**As a** user, **I want** the display to be off when no animation is playing, **so that** the toy looks like a plain wooden box and conserves power.

**Acceptance Criteria:**
- After any animation completes, the final frame holds on screen for 5 seconds (Hold Phase)
- After the Hold Phase, the display turns off (all LEDs black) — this is Idle
- The display remains off until a button is pressed or the toy enters/exits sleep
- No sound plays during Idle or the Hold Phase

---

### F10: Button Interrupt
**As a** child, **I want** to press a different button while an animation is playing and see the new animation start immediately, **so that** I don't have to wait.

**Acceptance Criteria:**
- If a button is pressed during an animation or during the Hold Phase, the current state stops immediately
- The new animation starts within 100ms of the button press
- Any currently playing sound stops and the new animation's sound begins
- Pressing the same button that is currently playing/holding restarts that animation from the beginning

---

### F11: Auto-Sleep
**As a** parent, **I want** the toy to automatically enter a low-power sleep mode after 2 minutes of inactivity, **so that** the battery is conserved if my child walks away.

**Acceptance Criteria:**
- If no button is pressed for 2 minutes after the display goes to Idle, the toy enters Sleep
- In Sleep mode, the display is off and power consumption is minimised
- Pressing any button wakes the toy from Sleep
- On wake, the toy goes to Idle (no boot animation replay), ready for button input
- The 2-minute timer resets each time a button is pressed
- During Tilt Game mode, any Tilt Activity (ball moving above threshold) resets the sleep timer; the toy only sleeps if left completely still for 2 minutes

---

### F12: Brightness Control
**As a** parent, **I want** to adjust the display brightness using the built-in buttons on the Stellar Unicorn, **so that** I can make it comfortable for my child's eyes or dim it for darker rooms.

**Acceptance Criteria:**
- The Stellar Unicorn's built-in brightness up/down buttons adjust display brightness
- Default brightness is 100%
- Brightness setting persists until power-off (does not need to persist across reboots)
- There is a minimum brightness floor (not fully off via brightness button, to avoid confusion with "broken")

---

### F13: Animation Variation
**As a** child, **I want** the animation to look slightly different each time I press the same button, **so that** it stays interesting.

**Acceptance Criteria:**
- Each animation introduces small random variations per play, such as:
  - Slight colour shift
  - Speed variation (e.g. beat rate, bounce speed, bloom speed varies ±15%)
  - Positional variation (e.g. swim direction, sweep direction)
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
| Speaker volume | Fixed at a moderate, child-safe level (~45% of max) |
| Brightness default | 100%, adjustable via hardware buttons |
| Auto-sleep timeout | 2 minutes of inactivity |
| Safety | No exposed electronics, no overheating, non-toxic materials |
| Flash storage | All WAV files + code + firmware must fit within 4MB flash |

---

## 5. Software Architecture

### Language
MicroPython (Pimoroni firmware for Stellar Unicorn)

### File Structure
```
main.py                  — Boot sequence, main loop, button polling, sleep logic, mode management
animations/
  __init__.py            — Animation registry / lookup
  heart.py               — Heart animation + triggers heartbeat sound
  star.py                — Star animation + triggers star sound
  flower.py              — Flower bloom animation + triggers flower sound
  fish.py                — Fish swim animation + triggers fish sound
  rainbow.py             — Rainbow sweep animation + triggers rainbow sound
  sun.py                 — Sun pulse animation + triggers sun sound
  boot.py                — Boot splash animation
games/
  tilt.py                — Tilt Game: ball physics, trail rendering, bounce sound, KX134 polling
sounds/
  heartbeat.wav          — Heartbeat "lub-dub" sound effect
  star.wav               — Sparkle/twinkle sound effect
  flower.wav             — Nature-inspired chime sound effect
  fish.wav               — Bubbly/underwater pop sound effect
  rainbow.wav            — Bright ascending chime sweep sound effect
  sun.wav                — Warm bright "ping" sound effect
  bounce.wav             — Soft thud/click for Tilt Game ball wall collision
  startup.wav            — Boot splash sound
lib/
  display.py             — Shared display helpers (clear screen, draw pixel, etc.)
  sound.py               — WAV playback helpers (load WAV, play via play_sample(), stop)
  buttons.py             — MCP23017 I2C button polling, debouncing, press detection
  sleep.py               — Auto-sleep timer, sleep/wake logic
  kx134.py              — Minimal MicroPython KX134 driver (read X/Y axes, configure double-tap interrupt)
```

### Audio Format Requirements
- WAV files must be **16-bit PCM, mono**
- Sample rate: 16kHz or 22.05kHz (Pico 2 W memory constraints)
- Total size of all WAV files must fit within the Pico 2 W's 4MB flash alongside MicroPython firmware and code
- Files are loaded into bytearrays and played via the Stellar Unicorn's `play_sample()` method

### Key Design Decisions
- **Each animation is self-contained**: exposes a `play(su, graphics, check_interrupt)` function that handles both display and sound, yielding periodically to allow interrupt checking
- **Tilt Game is a separate mode**: `games/tilt.py` exposes a `run(su, graphics, kx134)` function; `main.py` manages switching between animation mode and Tilt Game mode
- **Mode state**: `main.py` tracks whether the toy is in Animation Mode or Tilt Game mode; double-tap interrupt from KX134 triggers mode toggle
- **Button isolation**: while in Tilt Game mode, button polling is suspended entirely
- **KX134 driver**: `lib/kx134.py` is a thin MicroPython port of the SparkFun qwiic_kx13x_py register map, using `machine.I2C` directly
- **Post-animation Hold Phase**: after animation frames complete, the final frame remains on display for 5 seconds before returning to Idle
- **Interrupt mechanism**: main loop checks for button presses between animation frames and during the Hold Phase; if detected, the current animation returns early
- **Shared utilities**: common operations (clear screen, pixel drawing, WAV loading) live in `lib/`

---

## 6. Out of Scope (v1)

- WiFi features (remote animation updates, clock display)
- RFID card input
- Adjustable volume (fixed in software)
- Persistent settings across reboots
- Parent/settings mode
- Multiple simultaneous Tilt Game balls or game difficulty levels
