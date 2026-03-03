"""
Icon converter utility for X32/M32 mixer
Provides mapping between icon names and their numeric values (1-74)
"""

ICON_MAP = {
    "none": 1,
    "kick_back": 2,
    "kick_front": 3,
    "snare_top": 4,
    "snare_bottom": 5,
    "high_tom": 6,
    "mid_tom": 7,
    "floor_tom": 8,
    "hi_hat": 9,
    "ride": 10,
    "drum_kit": 11,
    "cowbell": 12,
    "bongos": 13,
    "congas": 14,
    "tambourine": 15,
    "vibraphone": 16,
    "electric_bass": 17,
    "acoustic_bass": 18,
    "contrabass": 19,
    "les_paul_guitar": 20,
    "ibanez_guitar": 21,
    "washburn_guitar": 22,
    "acoustic_guitar": 23,
    "bass_amp": 24,
    "guitar_amp": 25,
    "amp_cabinet": 26,
    "piano": 27,
    "organ": 28,
    "harpsichord": 29,
    "keyboard": 30,
    "synthesizer_1": 31,
    "synthesizer_2": 32,
    "synthesizer_3": 33,
    "keytar": 34,
    "trumpet": 35,
    "trombone": 36,
    "saxophone": 37,
    "clarinet": 38,
    "violin": 39,
    "cello": 40,
    "male_vocal": 41,
    "female_vocal": 42,
    "choir": 43,
    "hand_sign": 44,
    "talk_a": 45,
    "talk_b": 46,
    "large_diaphragm_mic": 47,
    "condenser_mic_left": 48,
    "condenser_mic_right": 49,
    "handheld_mic": 50,
    "wireless_mic": 51,
    "podium_mic": 52,
    "headset_mic": 53,
    "xlr_jack": 54,
    "trs_plug": 55,
    "trs_plug_left": 56,
    "trs_plug_right": 57,
    "rca_plug_left": 58,
    "rca_plug_right": 59,
    "reel_to_reel": 60,
    "fx": 61,
    "computer": 62,
    "monitor_wedge": 63,
    "left_speaker": 64,
    "right_speaker": 65,
    "speaker_array": 66,
    "speaker_on_pole": 67,
    "amp_rack": 68,
    "controls": 69,
    "faders": 70,
    "mixbus": 71,
    "matrix": 72,
    "routing": 73,
    "smiley": 74,
}

ICON_DISPLAY_NAMES = {
    1: "None",
    2: "Kick Back",
    3: "Kick Front",
    4: "Snare Top",
    5: "Snare Bottom",
    6: "High Tom",
    7: "Mid Tom",
    8: "Floor Tom",
    9: "Hi-Hat",
    10: "Ride",
    11: "Drum Kit",
    12: "Cowbell",
    13: "Bongos",
    14: "Congas",
    15: "Tambourine",
    16: "Vibraphone",
    17: "Electric Bass",
    18: "Acoustic Bass",
    19: "Contrabass",
    20: "Les Paul Guitar",
    21: "Ibanez Guitar",
    22: "Washburn Guitar",
    23: "Acoustic Guitar",
    24: "Bass Amp",
    25: "Guitar Amp",
    26: "Amp Cabinet",
    27: "Piano",
    28: "Organ",
    29: "Harpsichord",
    30: "Keyboard",
    31: "Synthesizer 1",
    32: "Synthesizer 2",
    33: "Synthesizer 3",
    34: "Keytar",
    35: "Trumpet",
    36: "Trombone",
    37: "Saxophone",
    38: "Clarinet",
    39: "Violin",
    40: "Cello",
    41: "Male Vocal",
    42: "Female Vocal",
    43: "Choir",
    44: "Hand Sign",
    45: "Talk A",
    46: "Talk B",
    47: "Large Diaphragm Mic",
    48: "Condenser Mic Left",
    49: "Condenser Mic Right",
    50: "Handheld Mic",
    51: "Wireless Mic",
    52: "Podium Mic",
    53: "Headset Mic",
    54: "XLR Jack",
    55: "TRS Plug",
    56: "TRS Plug Left",
    57: "TRS Plug Right",
    58: "RCA Plug Left",
    59: "RCA Plug Right",
    60: "Reel to Reel",
    61: "FX",
    62: "Computer",
    63: "Monitor Wedge",
    64: "Left Speaker",
    65: "Right Speaker",
    66: "Speaker Array",
    67: "Speaker on a Pole",
    68: "Amp Rack",
    69: "Controls",
    70: "Faders",
    71: "MixBus",
    72: "Matrix",
    73: "Routing",
    74: "Smiley",
}


def get_icon_value(icon) -> int | None:
    """
    Convert an icon name or number to its integer value (1-74).

    Args:
        icon: Icon name (e.g., 'kick_front', 'piano') or number (1-74)

    Returns:
        Integer icon value (1-74) or None if invalid
    """
    if isinstance(icon, int):
        if 1 <= icon <= 74:
            return icon
        return None

    icon_str = str(icon).strip()

    # Try numeric value first
    try:
        val = int(icon_str)
        if 1 <= val <= 74:
            return val
        return None
    except ValueError:
        pass

    # Try name lookup (case-insensitive, normalize separators)
    normalized = icon_str.lower().replace(" ", "_").replace("-", "_")
    return ICON_MAP.get(normalized)


def get_icon_name(value: int) -> str:
    """Get the display name for an icon value."""
    return ICON_DISPLAY_NAMES.get(value, f"Unknown ({value})")


def get_available_icons() -> list:
    """Return a list of all available icon names."""
    return list(ICON_MAP.keys())