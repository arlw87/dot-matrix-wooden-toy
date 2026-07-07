"""
WAV playback helpers for the Stellar Unicorn.
Loads 16-bit PCM mono WAV files and plays via the built-in speaker.

Uses a pre-allocated buffer to avoid memory fragmentation issues.
"""

import struct
import gc

# Pre-allocate audio buffer EARLY before memory fragments
# 200KB should fit the largest WAV file (~185KB)
# This MUST happen at module import time, before other allocations
gc.collect()  # Clean up before allocation
AUDIO_BUFFER_SIZE = 200000
_audio_buffer = bytearray(AUDIO_BUFFER_SIZE)
_audio_length = 0  # Actual length of data in buffer
_current_sample_rate = 16000


def load_wav(filename):
    """
    Load a WAV file into the pre-allocated buffer.

    Returns: (memoryview of audio data, sample_rate)

    Note: Each call overwrites the previous audio data.
    """
    global _audio_length, _current_sample_rate

    with open(filename, 'rb') as f:
        # Read RIFF header
        riff = f.read(4)
        if riff != b'RIFF':
            raise ValueError("Not a valid WAV file")

        f.read(4)  # File size
        wave = f.read(4)
        if wave != b'WAVE':
            raise ValueError("Not a valid WAV file")

        # Find fmt chunk
        _current_sample_rate = 16000  # Default
        while True:
            chunk_id = f.read(4)
            if len(chunk_id) < 4:
                break
            chunk_size = struct.unpack('<I', f.read(4))[0]

            if chunk_id == b'fmt ':
                fmt_data = f.read(chunk_size)
                audio_format = struct.unpack('<H', fmt_data[0:2])[0]
                num_channels = struct.unpack('<H', fmt_data[2:4])[0]
                _current_sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
                # We expect 16-bit PCM mono
                if audio_format != 1:
                    raise ValueError("Only PCM format supported")
                if num_channels != 1:
                    raise ValueError("Only mono audio supported")
            elif chunk_id == b'data':
                if chunk_size > AUDIO_BUFFER_SIZE:
                    raise ValueError(f"Audio too large: {chunk_size} > {AUDIO_BUFFER_SIZE}")
                # Read directly into pre-allocated buffer
                _audio_length = f.readinto(_audio_buffer)
                # Return a memoryview of just the valid portion
                return memoryview(_audio_buffer)[:_audio_length], _current_sample_rate
            else:
                f.read(chunk_size)  # Skip unknown chunks

    raise ValueError("No data chunk found in WAV file")


# ── Audio gate ────────────────────────────────────────────────────────────────
# When the gate is armed, play() holds the requested sound back instead of
# starting it. release_gate() then starts the held sound. This lets the app
# defer an animation's audio while its trigger button is held down, so the sound
# only begins once the button is released.
_gate_armed = False
_deferred = None   # filename waiting for the gate to open, or None


def arm_gate():
    """Begin deferring the next play() until release_gate() is called."""
    global _gate_armed, _deferred
    _gate_armed = True
    _deferred = None


def release_gate(su):
    """Open the gate and start any sound that play() deferred."""
    global _gate_armed, _deferred
    if not _gate_armed:
        return
    _gate_armed = False
    if _deferred is not None:
        filename = _deferred
        _deferred = None
        _play_now(su, filename)


def disarm_gate():
    """Stop deferring and discard any held sound without playing it."""
    global _gate_armed, _deferred
    _gate_armed = False
    _deferred = None


def play(su, filename):
    """
    Play a WAV file through the Stellar Unicorn speaker.
    Non-blocking - audio plays in background.

    If the audio gate is armed (a trigger button is being held), the sound is
    deferred until release_gate() is called instead of starting immediately.

    Note: Stellar Unicorn expects 16-bit signed PCM at specific sample rate.
    WAV files should be pre-converted to match hardware expectations.
    """
    global _deferred
    if _gate_armed:
        _deferred = filename   # hold until the button is released
        return
    _play_now(su, filename)


def _play_now(su, filename):
    """Load and start a WAV file immediately, bypassing the gate."""
    audio_data, sample_rate = load_wav(filename)
    su.play_sample(audio_data)


def stop(su):
    """Stop any currently playing audio and drop any deferred sound."""
    global _deferred
    _deferred = None
    su.stop_playing()


def is_playing(su):
    """Check if audio is currently playing."""
    return su.is_playing()


def set_volume(su, volume):
    """
    Set the audio volume (0.0 to 1.0).
    PRD specifies fixed moderate volume (~40-50%).
    """
    su.set_volume(volume)
