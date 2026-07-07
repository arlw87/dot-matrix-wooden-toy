# Dot Matrix Wooden Toy - Detailed Build Guide

## Bill of Materials

### Electronics

| Item | Qty | Supplier | Est. Price | Notes |
|------|-----|----------|------------|-------|
| Pimoroni Stellar Unicorn (Pico 2 W) | 1 | [The Pi Hut](https://thepihut.com/products/pico-2-w-unicorn) / [Pimoroni](https://shop.pimoroni.com/products/space-unicorns) | £39.00 | 16x16 RGB LED matrix, fully assembled |
| 30mm Arcade Buttons (mixed colours) | 6 | [Amazon UK](https://amazon.co.uk) / eBay UK | £12-15 | Get heart=red, star=yellow, sun=orange, etc. |
| 3.7V 2000mAh LiPo Battery | 1 | [The Pi Hut](https://thepihut.com) / Pimoroni | £8-10 | JST-PH connector required |
| LiPo Charger Module (TP4056 with protection) | 1 | Amazon UK / The Pi Hut | £3-5 | USB-C charging preferred |
| Slide Switch (SPST) | 1 | Amazon UK / eBay | £1-2 | Power on/off |
| Silicone Wire (22 AWG, various colours) | 1 set | Amazon UK | £5-8 | Flexible, easy to work with |
| JST-PH 2-pin connector | 2 | Amazon UK | £2-3 | For battery connection |
| Heat Shrink Tubing | 1 set | Amazon UK | £3-4 | Various sizes |

**Electronics Subtotal: ~£75-85**

### Wood & Materials

| Item | Qty | Supplier | Est. Price | Notes |
|------|-----|----------|------------|-------|
| 12mm Birch Plywood (600x300mm) | 1 | Local timber merchant / B&Q | £8-12 | For enclosure |
| 0.6mm Maple or Birch Veneer | 1 sheet | eBay UK / Craft suppliers | £5-8 | Light colours diffuse LEDs best |
| Wood Glue (PVA) | 1 | B&Q / Screwfix | £3-5 | Child-safe when cured |
| Food-Safe Wood Oil/Wax | 1 | Amazon UK | £6-10 | Non-toxic finish |
| Felt Pads | 1 pack | Amazon UK | £2-3 | For base/corners |
| M3 Brass Inserts | 8 | Amazon UK | £3-5 | For securing back panel |
| M3 x 8mm Screws | 8 | Amazon UK | £2-3 | For back panel |

**Wood & Materials Subtotal: ~£30-45**

### Tools Required

#### Power Tools (Builder has these)
- Mitre saw - for cutting plywood panels
- Track saw - for precise cuts
- Jigsaw - for curved cuts if desired
- Drill - for holes

#### Additional Tools Needed
| Item | Est. Price | Notes |
|------|------------|-------|
| 30mm Forstner Bit | £8-12 | For button holes (or 28mm depending on buttons) |
| Hole Saw Set | £15-25 | Alternative to Forstner bits |
| Soldering Iron + Solder | £20-30 | If not already owned |
| Wire Strippers | £8-12 | If not already owned |

#### Hand Tools
- Clamps (at least 4)
- Sandpaper (120, 180, 240 grit)
- Square and measuring tools
- Craft knife (for veneer)

---

## Design Decisions

### Display: Pimoroni Stellar Unicorn
**Why this over alternatives?**

| Option | Pros | Cons | Verdict |
|--------|------|------|---------||
| **Stellar Unicorn** | All-in-one, no wiring, battery connector, MicroPython ready, 16x16 grid | Fixed size, higher cost | **RECOMMENDED** |
| WS2812B 16x16 Matrix + Arduino | Cheaper (~£20), flexible size | Requires wiring, separate microcontroller, more complex | Good for v2 |
| Unicorn HAT HD + Pi Zero | Mature library | Retired product, slower boot, higher power | Not recommended |

### Input: Arcade Buttons vs RFID

| Option | Pros | Cons | Verdict |
|--------|------|------|---------||
| **Arcade Buttons** | Immediate feedback, no loose parts, intuitive, cheap | Buttons protrude slightly | **RECOMMENDED** |
| RFID Cards | Cool interaction, unlimited "buttons" | Cards can be lost, complex wiring, less intuitive for 2yr old | Not for prototype |

### Power: LiPo Battery with USB Charging
- **Safe**: Protection circuit prevents overcharge/discharge
- **Rechargeable**: USB-C charging via TP4056 module
- **Capacity**: 2000mAh gives 3-4 hours of play
- **Child-safe**: Battery is fully enclosed in wood

---

## Enclosure Dimensions

```
        FRONT VIEW                    SIDE VIEW
    +-------------------+           +----------------+
    |  o o o            |           |                |
    |  BUTTONS          |           |   ~40mm        |
    |  o o o            |           |   depth        |
    |                   |           |                |
    |  +-----------+    |           +----------------+
    |  |           |    |
    |  |  DISPLAY  |    |           TOP VIEW
    |  |  (veneer) |    |           +----------------+
    |  |  ~100mm   |    |           | [charging      |
    |  |           |    |           |  port]         |
    |  +-----------+    |           |                |
    |                   |           |  [ON/OFF]      |
    +-------------------+           +----------------+
         ~140mm
```

### Cutting List

| Part | Dimensions | Qty | Material |
|------|------------|-----|----------|
| Front Panel | 140 x 180 x 12mm | 1 | Birch Plywood |
| Back Panel | 140 x 180 x 6mm | 1 | Birch Plywood (thinner) |
| Side Panels | 180 x 40 x 12mm | 2 | Birch Plywood |
| Top/Bottom Panels | 116 x 40 x 12mm | 2 | Birch Plywood |
| Display Window Veneer | 110 x 110mm | 1 | 0.6mm Maple/Birch |

---

## Build Steps

### Phase 1: Prepare Electronics

#### Step 1.1: Test the Stellar Unicorn
1. Unbox the Stellar Unicorn and connect via USB
2. It comes pre-loaded with demo animations - verify it works
3. Install Thonny IDE on your computer
4. Download Pimoroni's MicroPython UF2 from their GitHub if needed
5. Test modifying a simple animation

#### Step 1.2: Wire the Arcade Buttons
The Stellar Unicorn has GPIO pins accessible. You'll wire buttons to these.

```
Button Wiring (active low with internal pull-up):

Button 1 (Heart)  ---- GPIO Pin --+-- Button ---- GND
Button 2 (Star)   ---- GPIO Pin --+
Button 3 (Sun)    ---- GPIO Pin --+
Button 4 (Moon)   ---- GPIO Pin --+
Button 5 (Fish)   ---- GPIO Pin --+
Button 6 (Tree)   ---- GPIO Pin --+

Note: Use the Qwiic/STEMMA connectors or solder to test pads
```

Available GPIO pins on Stellar Unicorn (check Pimoroni documentation):
- The 9 built-in buttons can be remapped or bypassed
- Additional GPIO available via the Qwiic connector or rear test pads

#### Step 1.3: Prepare Power Circuit
```
LiPo Battery --> TP4056 Charger Module --> Slide Switch --> Stellar Unicorn
                      |                                       (JST-PH port)
                      |
                USB-C charging port (accessible from outside)
```

**Important**: The Stellar Unicorn's JST-PH port accepts up to 5.5V. A 3.7V LiPo (4.2V fully charged) is safe.

---

### Phase 2: Build Enclosure

#### Step 2.1: Cut Wood Panels
1. Mark out all pieces on the plywood
2. Use track saw for straight cuts
3. Sand all edges (120 grit -> 180 grit -> 240 grit)

#### Step 2.2: Cut Button Holes in Front Panel
```
Button Layout (example - 2 rows of 3):

    +--------------------------------+
    |   o        o        o          |  <- 30mm holes
    |  Heart    Star     Sun         |    Forstner bit
    |                                |
    |   o        o        o          |
    |  Moon    Fish     Tree         |
    |                                |
    |   +----------------------+     |
    |   |                      |     |  <- Display cutout
    |   |    Display Window    |     |    (jigsaw)
    |   |      ~95 x 95mm      |     |
    |   |                      |     |
    |   +----------------------+     |
    |                                |
    +--------------------------------+
```

1. Mark button positions (ensure spacing for small hands)
2. Use 30mm (or 28mm - check your buttons) Forstner bit
3. Drill from the front face for clean holes
4. Cut display window with jigsaw (round corners for safety)

#### Step 2.3: Prepare Display Window
1. Cut veneer to size (slightly larger than window)
2. **Test light diffusion**: Hold veneer against LED matrix, power on
3. If too dim: sand veneer thinner or use thinner veneer
4. If hotspots visible: add opal acrylic diffuser sheet behind veneer

#### Step 2.4: Assemble Box
1. Dry-fit all pieces first
2. Glue and clamp sides to bottom
3. Glue front panel (ensure button holes align)
4. Leave back panel removable (brass inserts + screws)

#### Step 2.5: Install Brass Inserts
1. Drill pilot holes in box edges for M3 inserts
2. Use soldering iron to heat-press inserts into place
3. Test fit back panel with screws

---

### Phase 3: Final Assembly

#### Step 3.1: Install Electronics
1. Mount Stellar Unicorn behind display window
   - Use small wood blocks or hot glue to position
   - Ensure ~5-10mm gap between LEDs and veneer for diffusion
2. Mount arcade buttons in holes
   - Buttons typically snap-fit or screw in place
3. Mount TP4056 charger with USB port accessible (drill hole in side/back)
4. Mount slide switch in accessible location
5. Connect all wiring

#### Step 3.2: Attach Veneer
1. Apply thin layer of wood glue around window frame
2. Press veneer in place from inside
3. Clamp and let dry
4. Trim excess with craft knife

#### Step 3.3: Finishing
1. Sand entire exterior (240 grit)
2. Apply food-safe wood oil/wax
3. Let cure according to product instructions
4. Attach felt pads to bottom corners

#### Step 3.4: Button Labels
Options for adding symbols to buttons:
- Paint/engrave symbols on button caps
- Use vinyl stickers under clear button caps
- 3D printed button cap toppers (if you gain access to printer)

---

### Phase 4: Software

#### Step 4.1: Set Up Development Environment
1. Install Thonny IDE (easiest for MicroPython)
2. Connect Stellar Unicorn via USB
3. Download Pimoroni's examples from GitHub

#### Step 4.2: Basic Animation Code Structure

```python
# main.py - Dot Matrix Toy
import time
from stellar import StellarUnicorn
from picographics import PicoGraphics, DISPLAY_STELLAR_UNICORN
import machine

# Initialize display
su = StellarUnicorn()
graphics = PicoGraphics(display=DISPLAY_STELLAR_UNICORN)

# Set up button pins (adjust pin numbers based on your wiring)
button_pins = {
    'heart': machine.Pin(X, machine.Pin.IN, machine.Pin.PULL_UP),
    'star': machine.Pin(X, machine.Pin.IN, machine.Pin.PULL_UP),
    'sun': machine.Pin(X, machine.Pin.IN, machine.Pin.PULL_UP),
    'moon': machine.Pin(X, machine.Pin.IN, machine.Pin.PULL_UP),
    'fish': machine.Pin(X, machine.Pin.IN, machine.Pin.PULL_UP),
    'tree': machine.Pin(X, machine.Pin.IN, machine.Pin.PULL_UP),
}

# Colours
RED = graphics.create_pen(255, 0, 0)
YELLOW = graphics.create_pen(255, 255, 0)
ORANGE = graphics.create_pen(255, 165, 0)
BLUE = graphics.create_pen(0, 100, 255)
GREEN = graphics.create_pen(0, 255, 0)
WHITE = graphics.create_pen(255, 255, 255)
BLACK = graphics.create_pen(0, 0, 0)

def clear():
    graphics.set_pen(BLACK)
    graphics.clear()

def draw_heart(scale=1.0):
    """Draw a heart shape"""
    clear()
    graphics.set_pen(RED)
    heart = [
        "  **  **  ",
        " ******** ",
        " ******** ",
        "  ******  ",
        "   ****   ",
        "    **    ",
    ]

def animate_heart():
    """Beating heart animation"""
    for _ in range(5):
        draw_heart(scale=1.0)
        su.update(graphics)
        time.sleep(0.3)
        draw_heart(scale=0.8)
        su.update(graphics)
        time.sleep(0.3)

def main():
    su.set_brightness(0.5)

    while True:
        if button_pins['heart'].value() == 0:
            animate_heart()
        elif button_pins['star'].value() == 0:
            animate_star()
        time.sleep(0.05)

if __name__ == '__main__':
    main()
```

#### Step 4.3: Animation Ideas

| Button | Animation | Description |
|--------|-----------|-------------|
| Heart (Red) | Beating heart | Pulses larger/smaller |
| Star (Yellow) | Spinning star | Rotates and sparkles |
| Sun (Orange) | Rising sun | Rises with rays extending |
| Moon (Blue/White) | Moon phases | Cycles through phases |
| Fish (Blue) | Swimming fish | Fish swims across screen |
| Tree (Green) | Growing tree | Tree grows from seed |

#### Step 4.4: Helpful Libraries/Resources
- **PicoGraphics**: Pimoroni's graphics library for shapes, text, sprites
- **Pimoroni GitHub examples**: Pre-made animations to modify
- **Sprite sheets**: Create simple 16x16 pixel art sprites

---

## Testing & Troubleshooting

### Common Issues

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| LEDs not visible through veneer | Veneer too thick | Sand thinner or use 0.4mm veneer |
| Hotspots visible | LEDs too close to veneer | Add 5-10mm spacer, add diffuser |
| Buttons not responding | Wiring loose, wrong GPIO | Check connections, verify pin numbers |
| Battery drains fast | Brightness too high | Reduce brightness in code |
| Won't charge | Charger wired wrong | Check polarity, verify connections |

### Test Points
1. **Before enclosure**: Test all buttons and animations on bench
2. **After mounting display**: Check light diffusion looks good
3. **After full assembly**: Test all functions, charging, power switch

---

## Safety Checklist

### Electrical Safety
- [ ] All wires secured with heat shrink
- [ ] No exposed metal contacts
- [ ] Battery protected by enclosure
- [ ] Charger has overcharge protection
- [ ] No pinch points for wires

### Physical Safety
- [ ] All edges sanded smooth (no splinters)
- [ ] No small detachable parts
- [ ] Buttons firmly secured
- [ ] Back panel screws recessed/covered
- [ ] Corners rounded or padded
- [ ] Non-toxic finish fully cured

### Operational Safety
- [ ] Cannot overheat (tested running for 30+ minutes)
- [ ] Auto-sleep after inactivity (optional but recommended)
- [ ] Brightness comfortable (not too bright for eyes)

---

## Future Enhancements (v2)

Once the prototype works, consider:
- **Sound effects**: Use the built-in speaker for sounds with each animation
- **More buttons**: Add additional symbols/animations
- **WiFi features**: Update animations remotely
- **Light sensor**: Auto-adjust brightness based on room light
- **Sleep mode**: Turn off after inactivity to save battery
- **Custom enclosure shape**: Animal shape, house shape, etc.

---

## Sources & References

### Products
- [Pimoroni Stellar Unicorn](https://shop.pimoroni.com/products/space-unicorns)
- [The Pi Hut - Stellar Unicorn](https://thepihut.com/products/pico-2-w-unicorn)
- [Proto-PIC - WS2812B Matrix](https://proto-pic.co.uk/product/16x16-rgb-led-matrix-flexible-ws2812b-neopixel)

### Tutorials & Guides
- [Busy Button Box - Instructables](https://www.instructables.com/Busy-Button-Box-Montessori-style-Electronic-Board-/) - Similar toddler toy project
- [DIY Wood Veneer Light - Instructables](https://www.instructables.com/DIY-Wood-Veneer-Light/) - Veneer light diffusion
- [ArClock Wooden LED Display - Hackster.io](https://www.hackster.io/news/arclock-a-wooden-led-display-1182d64bf472) - LEDs through wood
- [Adafruit NeoMatrix Library](https://learn.adafruit.com/adafruit-neopixel-uberguide/neomatrix-library)

### Software
- [FastLED Library](https://fastled.io/) - For Arduino alternative
- [Pimoroni PicoGraphics](https://github.com/pimoroni/pimoroni-pico) - For Stellar Unicorn
