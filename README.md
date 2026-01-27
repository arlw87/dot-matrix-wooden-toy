# Dot Matrix Wooden Toy

An interactive wooden toy for toddlers (~2 years old) featuring a 16x16 RGB LED matrix display behind a wood veneer front. Press a button, see an animation with sound.

## Concept

The child presses one of four large arcade buttons — each showing a symbol (heart, star, moon, flower). The display lights up with a colourful animation and matching sound effect, then holds the final frame before fading to black.

## Hardware

- **Display & Controller**: Pimoroni Stellar Unicorn (16x16 RGB LED matrix, Raspberry Pi Pico 2 W)
- **Input**: 4x 30mm arcade push buttons
- **Power**: 3.7V 2000mAh LiPo with USB-C charging
- **Enclosure**: Birch plywood box with maple/birch veneer over the display window
- **Audio**: Built-in 30mm 1W speaker via I2S amplifier

## Animations

| Button | Animation | Sound |
|--------|-----------|-------|
| Heart (pink) | Beating/pulsing heart | Heartbeat WAV |
| Star (yellow) | Bouncing & rotating star | Sparkle WAV |
| Moon (blue/white) | Night sky with shooting star | Chime WAV |
| Flower (green/pink) | Growing & blooming flower | Nature WAV |

## Key Features

- 5-second animations with 5-second final frame hold
- Button press immediately interrupts current animation
- Slight random variation on each play
- Auto-sleep after 2 minutes of inactivity
- Manual brightness control via built-in hardware buttons
- Boot splash animation on power-on

## Software

- **Language**: MicroPython (Pimoroni firmware)
- **Architecture**: Modular — separate files per animation, shared display/sound/button libraries
- **Audio**: Pre-recorded WAV files (16-bit PCM mono)

## Project Documents

- [`requirements.md`](requirements.md) — Original project requirements
- [`PRD.md`](PRD.md) — Product Requirements Document (features, acceptance criteria, architecture)
- [`project-plan.md`](project-plan.md) — Detailed build guide with bill of materials
- [`project-summary.md`](project-summary.md) — Hardware decision summary

## Status

**Phase**: Pre-build — hardware decisions made, PRD complete, awaiting component delivery and software development.
