# Product Suggestions for Toy Construction

## Diffuser Layer (between LEDs and wood veneer)

| Product | Thickness | Price | Notes |
|---------|-----------|-------|-------|
| [Adafruit Black LED Diffusion Acrylic](https://www.adafruit.com/product/4594) | 2.6mm | ~$5 | Great for matrices, sharpens pixels, reduces glare - 12"x12" sheet |
| [TAP Plastics LED Light Panel](https://www.tapplastics.com/product/plastics/plastic-sheets/led_ligh_panel/598) | 0.5mm | Varies | Flexible, 65% light transmission, reduces hot spots |
| [Amazon - SIMIHUI Diffusion Film](https://www.amazon.com/SIMIHUI-Diffusion-Backlight-Ultra-Thin-Advertising/dp/B07HQMK5HF) | Ultra-thin | ~$10 | PET film, 20 pieces per bag |
| [Amazon - Cosyhat Polycarbonate Sheets](https://www.amazon.com/Cosyhat-Polycarbonate-Diffuser-Translucent-Thickness-150x150mm/dp/B0F1ZYPWRX) | 1-3mm | ~$15 | 150x150mm, good size for 16x16 matrix |

### Budget DIY Options
- **Window privacy film** - frosted window film from hardware stores (very thin, cheap)
- **Baking paper/parchment** - surprisingly effective, very thin
- **Thin white acrylic** - 1-2mm from local plastics supplier

### Recommendation
For the Stellar Unicorn 16x16 matrix: TAP Plastics 0.5mm or SIMIHUI ultra-thin film

**Layer order:** LEDs → thin diffuser → wood veneer

---

## Wood Veneer

| Product | Thickness | Notes |
|---------|-----------|-------|
| Microwood maple veneer | 0.1mm | Paper-backed, ideal for LED projects |
| Unglued maple veneer | 0.1-0.3mm | Light colored, even grain |

### Tips
- Thinner veneer = brighter LEDs showing through
- Maple works best (light color, even grain)
- Use contact adhesive or water-free paper glue
- Test LED colors through veneer before final assembly (wood absorbs blue/yellow more than red)

### Tutorials
- [Wooden LED Gaming Display (Instructables)](https://www.instructables.com/Wooden-LED-Gaming-Display-Powered-by-Raspberry-Pi-/)
- [ArClock - Wood Veneer Display (Instructables)](https://www.instructables.com/ArClock-a-Smart-Display-Wrapped-in-Real-Wood/)
- [Wood Block LED Clock (Instructables)](https://www.instructables.com/Wood-Block-LED-Clock/)

---

## Arcade Buttons (for toddler use)

| Type | Size | Notes |
|------|------|-------|
| Large dome buttons | 60mm | Best for toddlers - easy to press, satisfying click |
| Standard arcade buttons | 30mm | Smaller alternative |
| Extra-large dome buttons | 100mm | Very easy but bulky |

### Suggested Colors
| Button | Animation | Color |
|--------|-----------|-------|
| Heart | Heart | Red/Pink |
| Star | Star | Yellow |
| Butterfly | Butterfly | Blue/Purple |
| Flower | Flower | Green |

### Where to Buy
- Amazon: "60mm arcade button" or "large dome push button"
- AliExpress (cheaper, slower shipping)
- Pimoroni shop
- Adafruit

### Wiring
```
Button Terminal 1 ──── GPx (GP0, GP1, GP2, or GP3)
Button Terminal 2 ──── GND
```
No resistors needed - code uses internal pull-ups.

---

## Hardware

### Main Board
- Pimoroni Stellar Unicorn (16x16 RGB LED matrix with Pico 2 W)

### GPIO Pin Assignments
| GPIO | Button |
|------|--------|
| GP0 | Heart |
| GP1 | Star |
| GP2 | Butterfly |
| GP3 | Flower |

---

## Battery Power

### Recommended: 3xAA Battery Holder

| Product | Dimensions | Price | Notes |
|---------|------------|-------|-------|
| [Pimoroni 3xAA Holder](https://shop.pimoroni.com/en-us/products/3-x-aa-battery-holder-with-switch-and-jst-ph-connector) | ~58 x 48 x 15mm | ~£3 | **Recommended** - JST-PH connector, switch, guaranteed compatible |
| [Adafruit 3xAA Holder #4779](https://www.adafruit.com/product/4779) | 78 x 48 x 18mm | ~$3 | JST-PH connector, switch, well documented |

### Why 3xAA (not 4xAA)?
- 3xAA alkaline = 4.5V fresh, 2.7V depleted
- 3xAA NiMH = 3.6V fresh, 3.0V depleted
- 4xAA = 6V (alkaline) - **too high, may damage board**
- Stellar Unicorn expects LiPo range (~3.3-4.5V)

### Voltage Behavior
| Voltage | LED Behavior |
|---------|--------------|
| 3.6V+ | Optimal - full brightness, accurate colors |
| 2.9-3.6V | Works but blue LEDs start fading |
| <2.9V | Noticeably dim, color shift |
| ~2.5V | May not boot reliably |

### Battery Type Comparison
| Type | Pros | Cons |
|------|------|------|
| NiMH rechargeable | Rechargeable, safer for toddler toy, flat discharge curve | Lower starting voltage (3.6V) |
| Alkaline | Higher starting voltage (4.5V), gradual dimming warning | Not rechargeable, ongoing cost |

### Safety Notes (vs LiPo)
- **No fire/swelling risk** - safe if toddler drops/throws toy
- **No charging circuit needed** - simpler build
- **Easy battery replacement** - no soldering to swap batteries

### Connection
Stellar Unicorn has JST-PH battery connector - Pimoroni holder plugs directly in, no soldering required.
