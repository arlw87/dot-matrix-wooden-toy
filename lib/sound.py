"""
WAV playback helpers for the Stellar Unicorn.
Loads 16-bit PCM mono WAV files and plays via the built-in speaker.
"""

import struct

# Cache for loaded WAV data to avoid reloading from flash
_wav_cache = {}


def load_wav(filename):
    """
    Load a WAV file and return audio data as a bytearray.
    Caches the result to avoid repeated flash reads.

    Returns: (audio_data, sample_rate)
    """
    if filename in _wav_cache:
        return _wav_cache[filename]

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
        sample_rate = 16000  # Default
        while True:
            chunk_id = f.read(4)
            if len(chunk_id) < 4:
                break
            chunk_size = struct.unpack('<I', f.read(4))[0]

            if chunk_id == b'fmt ':
                fmt_data = f.read(chunk_size)
                audio_format = struct.unpack('<H', fmt_data[0:2])[0]
                num_channels = struct.unpack('<H', fmt_data[2:4])[0]
                sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
                # We expect 16-bit PCM mono
                if audio_format != 1:
                    raise ValueError("Only PCM format supported")
                if num_channels != 1:
                    raise ValueError("Only mono audio supported")
            elif chunk_id == b'data':
                audio_data = bytearray(f.read(chunk_size))
                _wav_cache[filename] = (audio_data, sample_rate)
                return audio_data, sample_rate
            else:
                f.read(chunk_size)  # Skip unknown chunks

    raise ValueError("No data chunk found in WAV file")


def play(su, filename):
    """
    Play a WAV file through the Stellar Unicorn speaker.
    Non-blocking - audio plays in background.
    """
    audio_data, sample_rate = load_wav(filename)
    su.play_sample(audio_data, sample_rate)


def stop(su):
    """Stop any currently playing audio."""
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
