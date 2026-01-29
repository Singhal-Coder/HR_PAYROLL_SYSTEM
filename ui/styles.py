# Color Palette (Professional Blue/Grey Theme)
BACKGROUND_MAIN = "#f4f6f9"  # Light Grey for content
SIDEBAR_BG = "#2c3e50"       # Dark Blue for Sidebar
SIDEBAR_ACTIVE = "#34495e"   # Slightly lighter for active button
TEXT_WHITE = "#ffffff"
TEXT_DARK = "#2c3e50"
ACCENT_COLOR = "#3498db"     # Highlight color
SUCCESS_COLOR = "#2ecc71"
ERROR_COLOR = "#e74c3c"

# Fonts
FONT_HEADER = ("Segoe UI", 20, "bold") # Windows standard, Linux falls back to Helvetica (Segoe UI not available)
FONT_SUBHEADER = ("Segoe UI", 14, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 11, "bold")

# Button Styles
BTN_STYLE_SIDEBAR = {
    "font": ("Segoe UI", 12),
    "bg": SIDEBAR_BG,
    "fg": TEXT_WHITE,
    "activebackground": SIDEBAR_ACTIVE,
    "activeforeground": TEXT_WHITE,
    "bd": 0,
    "relief": "flat",
    "anchor": "w",
    "padx": 20,
    "pady": 10,
    "cursor": "hand2"
}