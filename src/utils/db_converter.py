"""
X32/M32 dB conversion utilities
Handles conversion between linear fader values (0.0-1.0) and dB values
"""

import math


def db_to_fader(db: float) -> float:
    """
    Convert dB value to linear fader value (0.0-1.0).
    X32 fader range: -inf dB to +10 dB

    Key points:
    - -inf dB (off) = 0.0
    - -90 dB ~= 0.0 (practical minimum)
    - 0 dB (unity) ~= 0.75
    - +10 dB (max) = 1.0

    Args:
        db: Decibel value (-90 to +10)

    Returns:
        Linear fader value (0.0 to 1.0)
    """
    if db <= -90:
        return 0.0  # -inf dB or below practical minimum
    if db >= 10:
        return 1.0  # Maximum +10 dB

    # X32 uses a specific logarithmic curve for fader values
    if db <= -60:
        # -90 to -60 dB: linear mapping to 0.0-0.025
        return ((db + 90) / 30) * 0.025
    elif db <= -30:
        # -60 to -30 dB: linear mapping to 0.025-0.137
        return 0.025 + ((db + 60) / 30) * 0.112
    elif db <= -10:
        # -30 to -10 dB: linear mapping to 0.137-0.397
        return 0.137 + ((db + 30) / 20) * 0.26
    elif db <= 0:
        # -10 to 0 dB: linear mapping to 0.397-0.75
        return 0.397 + ((db + 10) / 10) * 0.353
    else:
        # 0 to +10 dB: linear mapping to 0.75-1.0
        return 0.75 + (db / 10) * 0.25


def fader_to_db(fader: float) -> float:
    """
    Convert linear fader value (0.0-1.0) to dB value.

    Args:
        fader: Linear fader value (0.0 to 1.0)

    Returns:
        Decibel value (-inf to +10)
    """
    if fader <= 0:
        return -math.inf
    if fader >= 1:
        return 10.0

    # Inverse mapping of db_to_fader
    if fader <= 0.025:
        # 0.0-0.025: -90 to -60 dB
        return -90 + (fader / 0.025) * 30
    elif fader <= 0.137:
        # 0.025-0.137: -60 to -30 dB
        return -60 + ((fader - 0.025) / 0.112) * 30
    elif fader <= 0.397:
        # 0.137-0.397: -30 to -10 dB
        return -30 + ((fader - 0.137) / 0.26) * 20
    elif fader <= 0.75:
        # 0.397-0.75: -10 to 0 dB
        return -10 + ((fader - 0.397) / 0.353) * 10
    else:
        # 0.75-1.0: 0 to +10 dB
        return ((fader - 0.75) / 0.25) * 10


# Common dB presets for quick access
DB_PRESETS = {
    "OFF": -math.inf,   # Fader all the way down
    "MINUS_90": -90,    # Practical minimum
    "MINUS_60": -60,    # Very quiet
    "MINUS_30": -30,    # Quiet
    "MINUS_20": -20,    # Below nominal
    "MINUS_10": -10,    # 10 dB below unity
    "MINUS_6": -6,      # 6 dB below unity
    "MINUS_3": -3,      # 3 dB below unity
    "UNITY": 0,         # Unity gain (0 dB)
    "PLUS_3": 3,        # 3 dB above unity
    "PLUS_6": 6,        # 6 dB above unity
    "PLUS_10": 10,      # Maximum
}


def format_db(db: float) -> str:
    """
    Format dB value for display.

    Args:
        db: Decibel value

    Returns:
        Formatted string (e.g., "0.0 dB", "-∞ dB", "+6.0 dB")
    """
    if math.isinf(db) or db <= -90:
        return "-∞ dB"
    sign = "+" if db > 0 else ""
    return f"{sign}{db:.1f} dB"


def parse_db(input_str: str) -> float | None:
    """
    Parse dB value from string input.
    Accepts formats: "0", "0dB", "0 dB", "+6dB", "-10 dB", "-inf", "-∞"

    Args:
        input_str: String representation of dB value

    Returns:
        Parsed dB value or None if invalid
    """
    normalized = input_str.strip().lower()

    # Check for infinity
    if normalized in ("-inf", "-∞", "-infinity"):
        return -math.inf

    # Remove 'db' suffix and spaces
    cleaned = normalized.replace("db", "").strip()

    # Parse the number
    try:
        value = float(cleaned)
    except ValueError:
        return None

    # Clamp to valid range
    if value <= -90:
        return -math.inf
    if value > 10:
        return 10.0

    return value