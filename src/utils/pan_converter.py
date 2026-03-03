"""
X32/M32 pan (stereo positioning) utilities
Handles conversion between linear pan values and percentage/LR notation
"""

import re


def percent_to_pan(percent: float) -> float:
    """
    Convert percentage pan value to linear (0.0-1.0).
    -100% (full left) = 0.0
    0% (center) = 0.5
    +100% (full right) = 1.0

    Args:
        percent: Pan percentage (-100 to +100)

    Returns:
        Linear pan value (0.0 to 1.0)
    """
    clamped = max(-100.0, min(100.0, percent))
    return (clamped + 100) / 200


def pan_to_percent(pan: float) -> float:
    """
    Convert linear pan value (0.0-1.0) to percentage.

    Args:
        pan: Linear pan value (0.0 to 1.0)

    Returns:
        Pan percentage (-100 to +100)
    """
    clamped = max(0.0, min(1.0, pan))
    return clamped * 200 - 100


def lr_to_pan(lr: str) -> float | None:
    """
    Convert LR notation to linear pan value.
    L50 = 50% left = 0.25
    C = center = 0.5
    R50 = 50% right = 0.75
    L100 = full left = 0.0
    R100 = full right = 1.0

    Args:
        lr: LR notation string (e.g., "L50", "C", "R100")

    Returns:
        Linear pan value (0.0 to 1.0) or None if invalid
    """
    normalized = lr.upper().strip()

    # Handle center
    if normalized in ("C", "CENTER"):
        return 0.5

    # Handle L/R notation
    match = re.match(r"^([LR])(\d+)?$", normalized)
    if not match:
        return None

    side = match.group(1)
    amount = int(match.group(2)) if match.group(2) else 100

    if amount < 0 or amount > 100:
        return None

    if side == "L":
        # Left: L100 = 0.0, L50 = 0.25, L0 = 0.5
        return 0.5 - amount / 200
    else:
        # Right: R0 = 0.5, R50 = 0.75, R100 = 1.0
        return 0.5 + amount / 200


def pan_to_lr(pan: float) -> str:
    """
    Convert linear pan value to LR notation.

    Args:
        pan: Linear pan value (0.0 to 1.0)

    Returns:
        LR notation string
    """
    percent = pan_to_percent(pan)

    if abs(percent) < 0.5:
        return "C"
    elif percent < 0:
        return f"L{round(abs(percent))}"
    else:
        return f"R{round(percent)}"


def format_pan(pan: float) -> str:
    """
    Format pan value for display.

    Args:
        pan: Linear pan value (0.0 to 1.0)

    Returns:
        Formatted string (e.g., "L50", "C", "R75")
    """
    return pan_to_lr(pan)


def parse_pan(input_val: str | float | int) -> float | None:
    """
    Parse pan value from various input formats.
    Accepts: percentage (-100 to 100), LR notation ("L50", "R100"), or linear (0.0-1.0)

    Args:
        input_val: Pan value in various formats

    Returns:
        Linear pan value (0.0 to 1.0) or None if invalid
    """
    if isinstance(input_val, (int, float)):
        num = float(input_val)
        if -100 <= num <= 100:
            # Assume percentage
            return percent_to_pan(num)
        elif 0 <= num <= 1:
            # Assume linear
            return num
        return None

    s = str(input_val).strip()

    # Try LR notation first
    lr_value = lr_to_pan(s)
    if lr_value is not None:
        return lr_value

    # Try parsing as number
    try:
        num = float(s)
        return parse_pan(num)
    except ValueError:
        pass

    return None