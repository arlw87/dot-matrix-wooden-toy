# Double-Tap Detection on the KX134 (archived)

This document preserves the two double-tap detection approaches that were
prototyped for the wooden toy, along with the code and the reasons neither was
kept in the shipping firmware. Nothing here is currently wired into `main.py` —
the driver now only measures the X/Y/Z axes. Use this as a reference if you want
to revive tap/knock gestures later.

## Context

- Sensor: SparkFun **KX134-1211** accelerometer on I2C0 (GP4/GP5), address `0x1F`,
  sharing the Qwiic bus with the MCP23017 (`0x20`).
- Interaction goal: **double-knock the wooden enclosure** to trigger something.
- Register map: Kionix KX134-1211 Technical Reference Manual (TRM) Rev 1.0.

The key difficulty: a knock delivered to a **wooden box** reaches the sensor as a
damped, smeared, multi-bounce vibration — not the sharp, clean-edged jerk that
tap engines are designed around.

---

## Approach 1 — Hardware Directional-Tap engine

The KX134 has a built-in Directional-Tap™ finite-state machine. You enable it
with the `TDTE` bit in `CNTL1` and configure it through registers `0x2A–0x31`.
When a tap fires, the `TDTS` field of `INS2` latches until you read `INT_REL`.

### Registers used

| Reg | Addr | Purpose |
|-----|------|---------|
| `CNTL1`  | `0x1B` | `PC1` run, `RES` 16-bit, `GSEL` range, `TDTE` tap-engine enable |
| `ODCNTL` | `0x21` | output data rate (`0x09` = 400 Hz) |
| `INS2`   | `0x17` | `TDTS` at bits[3:2]: `00` none, `01` single, `10` double |
| `INT_REL`| `0x1A` | **read** to release the interrupt latch |
| `TDTRC`  | `0x2A` | report control — bit1 `DTRE` double-tap, bit0 `STRE` single-tap |
| `TDTC`   | `0x2B` | min time between tap 1 start and tap 2 end |
| `TTH`    | `0x2C` | jerk Performance Index (PI) upper bound |
| `TTL`    | `0x2D` | jerk PI lower bound |
| `FTD`    | `0x2E` | first-tap duration window |
| `STD`    | `0x2F` | second-tap duration window |
| `TLT`    | `0x30` | tap latency timer |
| `TWS`    | `0x31` | total tap-event window |

### Configuration that was used

```python
def _init_hardware(self):
    self._write(0x1B, 0x00)                    # CNTL1 standby
    self._write(0x21, 0x09)                    # ODCNTL 400 Hz
    self._write(0x1B, 0x80 | 0x40 | 0x04)      # CNTL1 run | 16-bit | TDTE
    self._read(0x1A)                           # read INT_REL, clear boot latch

def configure_double_tap(self, tth=0xFF, ttl=0x01, window=0xFF):
    # Tap registers are On-The-Fly — writable while running (PC1=1).
    self._write(0x2A, 0x03)   # TDTRC: enable single + double tap reporting
    self._write(0x2B, 0x78)   # TDTC:  0.3 s min between tap 1 start and tap 2 end
    self._write(0x2C, tth)    # TTH:   jerk PI upper bound (0xFF = accept any strength)
    self._write(0x2D, ttl)    # TTL:   jerk PI lower bound (0x01 = lightest taps)
    self._write(0x2E, 0xA2)   # FTD:   Kionix default first-tap duration
    self._write(0x2F, 0x24)   # STD:   Kionix default second-tap duration
    self._write(0x30, 0x28)   # TLT:   0.1 s latency timer
    self._write(0x31, window) # TWS:   total event window (0xFF ≈ 637 ms)
    self._read(0x1A)          # clear any held latch

def poll_double_tap(self):
    """Return True once if a hardware double-tap has fired; clears the latch."""
    ins2  = self._read(0x17)[0]
    fired = (ins2 & 0x0C) == 0x08          # TDTS bits[3:2] == 0b10
    if fired:
        self._read(0x1A)                   # reading INT_REL releases the latch
    return fired

def dump_interrupt_regs(self):
    """Print raw interrupt register bytes — for diagnosing tap detection."""
    ins1 = self._read(0x16)[0]
    ins2 = self._read(0x17)[0]
    ins3 = self._read(0x18)[0]
    print("INS1=0x%02X INS2=0x%02X INS3=0x%02X" % (ins1, ins2, ins3))
```

### Bugs fixed while debugging (all real, all fixed)

1. **Wrong tap register addresses** — they sit at `0x2A–0x31`, not `0x24`/`0x29`.
2. **Wrong `TDTS` bit positions** — double-tap is `INS2` bits[3:2] (mask `0x0C`, value `0x08`).
3. **`TTH` semantics inverted** — PI must be *below* `TTH`; setting `TTH=0x01` made detection impossible. Use `0xFF`.
4. **`INT_REL` was written instead of read** — the latch clears on a *read* (TRM §1.11).
5. **Boot-time latch never cleared** — the wake-up engine latches `INS2` on power-up; read `INT_REL` at the end of init.

### Why it was abandoned

After all five fixes, the register configuration is **correct on paper** — verified
against the TRM:

- `TDTE` enabled, tap ODR default 400 Hz (`CNTL3` reset `0xA8` → `OTDT`=`101`),
- all tap axes enabled (`INC3` default `0x3F`),
- thresholds maximally permissive (`TTH=0xFF`, `TTL=0x01`).

Yet `INS1/INS2/INS3` read `0x00` **permanently**, even on hard knocks. Because
tap status is *latched* until `INT_REL` is read, a real detection would persist
across the 500 ms diagnostic dumps — it never did. The engine simply never fires.

The most likely cause: the Directional-Tap FSM wants a sharp jerk **on the sensor**
with clean start/end edges inside tight `FTD`/`STD`/`TLT`/`TDTC` windows. A knock
transmitted through a **wooden enclosure** arrives smeared and damped and never
satisfies those timing windows, no matter how permissive the amplitude thresholds.

A next step that was never completed: add a `WHO_AM_I` (`0x13`, expect `0x46`)
check and read-back verification of `CNTL1`/`CNTL3`/`ODCNTL`/`TDTRC` to confirm
the writes land — but the wooden-box physics likely make this engine a dead end
regardless.

---

## Approach 2 — Software double-tap from the jerk signal

Instead of the opaque hardware FSM, detect knocks in software from the **jerk**
(the frame-to-frame change in acceleration) that the main loop already samples.
This is fully tunable, testable, and independent of the sensor's FSM quirks.

### Algorithm

- Each poll, read `(x, y, z)` in g and compute `jerk = |Δx| + |Δy| + |Δz|`.
- A `jerk` above `threshold_g` is a **knock**.
- A **refractory** window after each knock debounces the enclosure's ring so one
  physical knock counts once.
- Two knocks within `max_gap_ms` = a **double-tap**; it fires exactly once and
  does not chain into a third.

### Code

```python
# Defaults
_TAP_THRESHOLD_G   = 0.5   # jerk (|Δx|+|Δy|+|Δz| in g) that counts as a knock
_TAP_MAX_GAP_MS    = 600   # longest gap between the two knocks of a double-tap
_TAP_REFRACTORY_MS = 90    # ignore further knocks this soon after one (debounce ring)

def poll_double_tap_sw(self, debug=False):
    """Call every main-loop iteration. Returns True once per double-tap."""
    x, y, z = self.read_xyz()
    now  = time.ticks_ms()
    jerk = abs(x - self._prev_x) + abs(y - self._prev_y) + abs(z - self._prev_z)
    self._prev_x, self._prev_y, self._prev_z = x, y, z

    if jerk < self._tap_thresh:
        return False

    # Debounce: ignore the ringing of a knock we already counted.
    if (self._last_tap_ms is not None
            and time.ticks_diff(now, self._last_tap_ms) < self._tap_refract):
        return False

    gap = (time.ticks_diff(now, self._last_tap_ms)
           if self._last_tap_ms is not None else -1)
    is_double = self._armed and gap <= self._tap_max_gap
    self._last_tap_ms = now

    if debug:
        kind = "2nd (double!)" if is_double else ("2nd (too late)" if self._armed else "1st")
        print("knock %s jerk=%.3fg gap=%dms" % (kind, jerk, gap))

    if is_double:
        self._armed = False       # consume — need two fresh knocks next time
        return True
    self._armed = True            # first knock; wait for the second
    return False
```

State initialised in `__init__`:

```python
self._tap_thresh  = _TAP_THRESHOLD_G
self._tap_max_gap = _TAP_MAX_GAP_MS
self._tap_refract = _TAP_REFRACTORY_MS
self._prev_x = self._prev_y = self._prev_z = 0.0
self._last_tap_ms = None     # timestamp of the last accepted knock
self._armed       = False    # a first knock is waiting for its pair
```

### Tuning (which knob does what)

| Value | Default | More sensitive | Effect |
|-------|---------|----------------|--------|
| `threshold_g`   | `0.5` | **lower** (`0.3`, `0.2`) | jerk needed to register a knock — the main dial |
| `max_gap_ms`    | `600` | **raise** (`800`)        | longest gap allowed between the two knocks |
| `refractory_ms` | `90`  | **lower** (`60`)         | min spacing / ring debounce — too low double-counts one knock |

Poll at ~100 Hz (the loop's `time.sleep_ms(10)` cadence) so fast knocks register.
With `debug=True` the detector prints each knock's jerk and gap, which is how you
pick a `threshold_g` just below your typical knock jerk.

### Why it was abandoned

Approach discontinued at the user's request ("this is not working") in favour of a
different interaction model. The algorithm itself is sound and unit-tested; the
practical problem was tuning `threshold_g` for the wooden enclosure so that real
knocks register reliably without ordinary handling of the toy causing false taps.

---

## Reviving either approach

Both used the same `KX134` driver in `lib/kx134.py`. The driver retained the
measurement primitives (`read_xy()`, `read_xyz()`); only the tap-specific code was
removed. To bring back:

- **Hardware**: re-add the tap register constants + `configure_double_tap()` /
  `poll_double_tap()` / `dump_interrupt_regs()`, and OR `TDTE` (`0x04`) back into
  the `CNTL1` run-mode write in `_init_hardware()`.
- **Software**: re-add the tap state to `__init__`, plus `configure_software_tap()`
  and `poll_double_tap_sw()`, then poll it every iteration in `main.py`.
