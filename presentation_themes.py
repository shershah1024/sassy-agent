from enum import Enum
from typing import Dict, TypedDict
from dataclasses import dataclass

class RgbColor(TypedDict):
    red: float
    green: float
    blue: float

@dataclass
class ThemeColors:
    primary: RgbColor
    secondary: RgbColor
    accent: RgbColor
    background: RgbColor
    text: RgbColor
    textLight: RgbColor
    textDark: RgbColor

THEMES = {
    "MIDNIGHT": ThemeColors(
        # Deep blue with modern accents
        primary={"red": 0.13, "green": 0.17, "blue": 0.23},     # Deep blue
        secondary={"red": 0.0, "green": 0.47, "blue": 0.75},    # Bright blue
        accent={"red": 0.0, "green": 0.8, "blue": 0.6},         # Teal
        background={"red": 0.98, "green": 0.98, "blue": 0.98},  # Almost white
        text={"red": 0.2, "green": 0.2, "blue": 0.25},          # Dark slate
        textLight={"red": 1.0, "green": 1.0, "blue": 1.0},      # White
        textDark={"red": 0.13, "green": 0.17, "blue": 0.23}     # Deep blue
    ),
    "SUNSET": ThemeColors(
        # Modern gradient from purple to orange
        primary={"red": 0.54, "green": 0.23, "blue": 0.51},     # Purple
        secondary={"red": 0.95, "green": 0.42, "blue": 0.24},   # Coral
        accent={"red": 1.0, "green": 0.76, "blue": 0.03},       # Golden
        background={"red": 0.99, "green": 0.98, "blue": 0.96},  # Cream white
        text={"red": 0.25, "green": 0.23, "blue": 0.27},        # Dark purple-grey
        textLight={"red": 1.0, "green": 1.0, "blue": 0.98},     # Warm white
        textDark={"red": 0.2, "green": 0.18, "blue": 0.22}      # Deep purple-grey
    ),
    "FOREST": ThemeColors(
        # Rich greens with earth tones
        primary={"red": 0.13, "green": 0.3, "blue": 0.25},      # Forest green
        secondary={"red": 0.45, "green": 0.6, "blue": 0.35},    # Sage
        accent={"red": 0.85, "green": 0.65, "blue": 0.35},      # Golden brown
        background={"red": 0.98, "green": 0.97, "blue": 0.95},  # Ivory
        text={"red": 0.2, "green": 0.25, "blue": 0.22},         # Dark green-grey
        textLight={"red": 0.95, "green": 0.98, "blue": 0.95},   # Light sage
        textDark={"red": 0.1, "green": 0.15, "blue": 0.12}      # Deep forest
    ),
    "TECH": ThemeColors(
        # Modern tech-inspired theme
        primary={"red": 0.15, "green": 0.15, "blue": 0.18},     # Almost black
        secondary={"red": 0.0, "green": 0.65, "blue": 0.95},    # Electric blue
        accent={"red": 0.95, "green": 0.3, "blue": 0.6},        # Hot pink
        background={"red": 0.97, "green": 0.97, "blue": 0.98},  # Cool white
        text={"red": 0.2, "green": 0.2, "blue": 0.23},          # Dark grey
        textLight={"red": 1.0, "green": 1.0, "blue": 1.0},      # Pure white
        textDark={"red": 0.1, "green": 0.1, "blue": 0.13}       # Deep grey
    ),
    "MINIMAL": ThemeColors(
        # Clean, minimal design
        primary={"red": 0.15, "green": 0.15, "blue": 0.15},     # Almost black
        secondary={"red": 0.4, "green": 0.4, "blue": 0.4},      # Medium grey
        accent={"red": 0.8, "green": 0.2, "blue": 0.3},         # Red accent
        background={"red": 1.0, "green": 1.0, "blue": 1.0},     # Pure white
        text={"red": 0.2, "green": 0.2, "blue": 0.2},           # Dark grey
        textLight={"red": 1.0, "green": 1.0, "blue": 1.0},      # White
        textDark={"red": 0.1, "green": 0.1, "blue": 0.1}        # Almost black
    )
}

class SlideType(Enum):
    TITLE_CENTERED = "TITLE_CENTERED"
    TITLE_LEFT = "TITLE_LEFT"
    TITLE_GRADIENT = "TITLE_GRADIENT"
    TWO_COLUMNS_EQUAL = "TWO_COLUMNS_EQUAL"
    TWO_COLUMNS_LEFT_WIDE = "TWO_COLUMNS_LEFT_WIDE"
    TWO_COLUMNS_RIGHT_WIDE = "TWO_COLUMNS_RIGHT_WIDE"
    IMAGE_CENTERED = "IMAGE_CENTERED"
    QUOTE_CENTERED = "QUOTE_CENTERED"
    QUOTE_SIDE = "QUOTE_SIDE"
    BULLET_POINTS = "BULLET_POINTS"
    NUMBER_POINTS = "NUMBER_POINTS"

@dataclass
class Position:
    left: int
    top: int

@dataclass
class Size:
    width: int
    height: int

@dataclass
class FontStyle:
    bold: bool = False
    fontSize: Dict[str, any] = None
    foregroundColor: Dict[str, any] = None 