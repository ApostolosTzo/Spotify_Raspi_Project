# framebuf2.py - Large font support for MicroPython displays
# Standalone functions (no monkey-patching)

def text_large(display, text, x, y, color=1):
    """Draw text using built-in font at normal size (placeholder for future 2x scale)."""
    display.text(text, x, y, color)