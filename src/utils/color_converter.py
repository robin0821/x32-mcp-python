"""
X32/M32 channel color utilities
Handles color mapping for channel strip colors
"""

# X32 Color Map
# The X32 uses integer values 0-15 for channel colors
X32_COLORS: dict[str, int] = {
    "OFF": 0,       # Off/Black (no color)
    "RED": 1,       # Red
    "GREEN": 2,     # Green
    "YELLOW": 3,    # Yellow
    "BLUE": 4,      # Blue
    "MAGENTA": 5,   # Magenta
    "CYAN": 6,      # Cyan
    "WHITE": 7,     # White
    "OFF_INV": 8,   # Off Inverted
    "RED_INV": 9,   # Red Inverted
    "GREEN_INV": 10,  # Green Inverted
    "YELLOW_INV": 11, # Yellow Inverted
    "BLUE_INV": 12,   # Blue Inverted
    "MAGENTA_INV": 13, # Magenta Inverted
    "CYAN_INV": 14,   # Cyan Inverted
    "WHITE_INV": 15,  # White Inverted
}


def get_color_value(color_name: str) -> int | None:
    """
    Get color value from name (case-insensitive).

    Args:
        color_name: Color name (e.g., 'red', 'blue-inv', '3')

    Returns:
        Color integer value (0-15) or None if invalid
    """
    upper_name = color_name.upper().replace(" ", "_").replace("-", "_")

    # Check direct match
    if upper_name in X32_COLORS:
        return X32_COLORS[upper_name]

    # Check without _INV suffix for inverted colors (e.g. 'blue' -> 'BLUE_INV' handled separately)
    inv_name = f"{upper_name}_INV"
    if inv_name in X32_COLORS:
        return X32_COLORS[inv_name]

    # Try parsing as number
    try:
        num = int(color_name)
        if 0 <= num <= 15:
            return num
    except ValueError:
        pass

    return None


def get_color_name(value: int) -> str | None:
    """
    Get color name from value.

    Args:
        value: Color integer value (0-15)

    Returns:
        Color name or None if invalid
    """
    for name, val in X32_COLORS.items():
        if val == value:
            return name.lower().replace("_", "-")
    return None


def get_available_colors() -> list[str]:
    """
    Get list of available color names.

    Returns:
        Array of color names
    """
    return [name.lower().replace("_", "-") for name in X32_COLORS.keys()]


def format_color(value: int) -> str:
    """
    Format color for display.

    Args:
        value: Color integer value

    Returns:
        Formatted color string
    """
    name = get_color_name(value)
    return name or f"Color {value}"