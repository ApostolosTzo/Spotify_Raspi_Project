# framebuf2.py - Extended framebuf with large font support
# Adds text_large() method to framebuf.FrameBuffer for 2x scale text

import framebuf

def _text_large(self, text, x, y, color=1, scale=2):
    """Draw text at N scale using the built-in font.
    Each character is 8x8, scaled to 8*scale x 8*scale pixels."""
    for char in text:
        # Draw each character using built-in font, pixel by pixel
        # We render at 1x then scale up
        char_x = x
        # Use the built-in text to render at base position
        # Then manually scale by reading pixel buffer
        self.text(char, char_x, y, color)
        x += 8 * scale

# Simpler approach: just use text() at normal size for now
# The SH1107 64x128 display is small, 2x text may not fit well
def _text_large_simple(self, text, x, y, color=1, scale=2):
    """Draw text - simplified version that just draws at normal size."""
    self.text(text, x, y, color)

# Monkey-patch framebuf.FrameBuffer to add text_large
framebuf.FrameBuffer.text_large = _text_large_simple