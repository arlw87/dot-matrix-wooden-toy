# Dot Matrix Wooden Toy

An interactive toy for children aged ~2 years old built around a Pimoroni Stellar Unicorn (16x16 RGB LED matrix + Raspberry Pi Pico 2 W) housed in a birch plywood enclosure with a wood veneer front.

## Language

### Hardware

**Stellar Unicorn**:
The main board — a Pimoroni 16x16 RGB LED matrix driven by a Raspberry Pi Pico 2 W. The primary display and controller for the toy.
_Avoid_: display board, LED board, matrix board

**Veneer**:
A thin wood surface laminated over the front of the display window. LEDs illuminate through it. Green wavelengths are absorbed more heavily than red, blue, or yellow — animations must account for this.
_Avoid_: laminate, wood panel

**MCP23017**:
An I2C GPIO expander (address 0x20, on I2C0 GP4/GP5) that provides the 6 button input pins (port B, GPB0–GPB5). Required because the Stellar Unicorn's own GPIO pins are consumed by the LED matrix.
_Avoid_: GPIO expander, I2C expander

**KX134**:
A SparkFun Triple Axis Accelerometer Breakout (Kionix KX134-1211) connected via Qwiic (I2C, address 0x1F or 0x1E). Shares the I2C0 bus with the MCP23017 (address 0x20 — no conflict). Has hardware single/double-tap interrupt detection. SparkFun's official library (qwiic_kx13x_py) targets desktop Python; a thin MicroPython port lives in lib/kx134.py.
_Avoid_: accelerometer (use KX134 when being specific about the chip)

### Interactions

**Animation Button**:
One of six physical arcade push buttons wired to the MCP23017 (GPB0–GPB5). Each button has a theme (e.g. Heart, Star) and triggers its corresponding Animation when pressed.
_Avoid_: input button, GPIO button

**Animation**:
A self-contained visual sequence played on the Stellar Unicorn display in response to an Animation Button press. Consists of animated frames followed by a Hold Phase, and is accompanied by a Sound Effect.
_Avoid_: sequence, display sequence, effect

**Hold Phase**:
The 5-second period after an Animation's frames complete where the final frame remains on screen before the display returns to Idle.
_Avoid_: freeze frame, end frame, static phase

**Idle**:
The state where all LEDs are off and the toy is waiting for a button press or Sleep trigger.
_Avoid_: standby, off state, waiting state

**Sleep**:
Low-power mode entered after 2 minutes of Idle with no button press. Exited by pressing any Animation Button.
_Avoid_: standby, power save

**Sound Effect**:
A WAV audio file (16-bit PCM mono) played via the Stellar Unicorn's built-in speaker when an Animation runs.
_Avoid_: sound, audio clip, music

### Animations (confirmed set — v2)

Six Animation Buttons, each with a theme:
- **Heart** — pink/red pulsing heart
- **Star** — yellow bouncing/rotating star
- **Flower** — petals opening outward from the centre of the display (no stem; warm colours only to avoid Veneer green absorption)
- **Fish** — swimming fish (orange/blue)
- **Rainbow** — sweeping arcs of ROYGBIV colour
- **Sun** — yellow/orange pulsing circle with radiating rays

_Dropped from v1 PRD_: Moon, Butterfly (replaced by Fish, Rainbow, Sun).

### Game Mode

**Tilt Game**:
A separate interactive mode where a ball moves across the 16x16 display driven by KX134 tilt (gravity → acceleration → velocity → position), bounces off edges, changes colour based on direction of movement, and leaves a fading pixel trail. Open-ended — no win condition.
_Avoid_: accelerometer game, motion game

**Tap-to-Toggle**:
The entry/exit mechanism for the Tilt Game. A double-tap on the toy body (detected via KX134 hardware double-tap interrupt) toggles between Idle/Animation mode and Tilt Game mode. Fallback if tuning fails: simultaneous long-press of two Animation Buttons.
_Avoid_: shake to enter, button mode switch

**Bounce Sound**:
A short WAV sound effect played each time the Tilt Game ball collides with a display edge. The only audio in Tilt Game mode. Sound brief: a soft thud/click — should feel physical, not musical.
_Avoid_: wall sound, collision sound

**Tilt Activity**:
Any KX134 reading where the Tilt Game ball is moving above a minimum velocity threshold, distinguishing active play from the toy sitting still. Resets the auto-sleep timer.
_Avoid_: movement, shake, gesture

**Animation Mode**:
The default operating mode where the six Animation Buttons are active and pressing one plays its Animation. Contrasted with Tilt Game mode.
_Avoid_: normal mode, button mode, default mode

## Example dialogue

> "The child pressed the Star button during the Hold Phase of the Heart animation — what happens?"
> "The Hold Phase is interrupted immediately. The Heart Animation stops, the display clears, and the Star Animation begins within 100ms."

> "Should the Tilt Game use the same Hold Phase pattern as the Animations?"
> "No — the Tilt Game is a distinct mode with its own entry/exit logic. Hold Phase is specific to Animations."
