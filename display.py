# display.py - SH1107 display wrapper for Spotify now-playing

from machine import Pin, SPI
import time
import sh1107
import framebuf2  # patches framebuf with text_large
from config import DISPLAY_ROTATE, DISPLAY_CONTRAST

# Pico-OLED-1.3 SPI pins (Waveshare default)
SPI_SCK = 10
SPI_MOSI = 11
SPI_CS = 9
SPI_DC = 8
SPI_RST = 12

# Display dimensions (portrait 64x128, rotated 90 or 270 for landscape)
WIDTH = 128
HEIGHT = 64

class SpotifyDisplay:
    def __init__(self):
        # Initialize SPI
        self.spi = SPI(1, baudrate=10_000_000, sck=Pin(SPI_SCK), mosi=Pin(SPI_MOSI))
        self.cs = Pin(SPI_CS, Pin.OUT, value=1)
        self.dc = Pin(SPI_DC, Pin.OUT, value=0)
        self.rst = Pin(SPI_RST, Pin.OUT, value=1)
        
        # Initialize SH1107
        self.display = sh1107.SH1107_SPI(
            WIDTH, HEIGHT, self.spi, self.dc, self.rst, self.cs,
            rotate=DISPLAY_ROTATE, delay_ms=200
        )
        self.display.contrast(DISPLAY_CONTRAST)
        
        # Scrolling state
        self.scroll_offset = 0
        self.scroll_text = ""
        self.scroll_last_update = 0
        self.scroll_speed = 150  # ms per step
        
    def clear(self):
        self.display.fill(0)
        
    def show(self):
        self.display.show()
        
    def _draw_progress_bar(self, x, y, w, h, progress, current_ms, total_ms):
        """Draw progress bar with time labels."""
        # Background
        self.display.rect(x, y, w, h, 1)
        # Fill
        if total_ms > 0:
            fill_w = int((w - 2) * progress)
            if fill_w > 0:
                self.display.fill_rect(x + 1, y + 1, fill_w, h - 2, 1)
        # Time labels
        cur_str = self._format_time(current_ms)
        tot_str = self._format_time(total_ms)
        self.display.text(cur_str, x, y - 10, 1)
        self.display.text(tot_str, x + w - len(tot_str) * 8, y - 10, 1)
        
    def _format_time(self, ms):
        """Format ms as M:SS or MM:SS"""
        if ms < 0:
            ms = 0
        total_sec = ms // 1000
        m = total_sec // 60
        s = total_sec % 60
        return f"{m}:{s:02d}"
    
    def _scroll_text_line(self, text, y, max_width=128):
        """Draw scrolling text if wider than screen, else static."""
        text_w = len(text) * 8
        if text_w <= max_width:
            self.display.text(text, 0, y, 1)
            return
            
        now = time.ticks_ms()
        if time.ticks_diff(now, self.scroll_last_update) >= self.scroll_speed:
            self.scroll_last_update = now
            self.scroll_offset = (self.scroll_offset + 1) % (text_w + 20)
            
        # Draw visible portion
        for i, char in enumerate(text):
            char_x = i * 8 - self.scroll_offset
            if -8 < char_x < max_width:
                self.display.text(char, char_x, y, 1)
    
    def show_now_playing(self, data):
        """Show full now-playing screen (Mode 1)."""
        self.clear()
        
        track = data.get("track", "")
        artists = data.get("artists", "")
        progress = data.get("progress_ms", 0)
        duration = data.get("duration_ms", 0)
        is_playing = data.get("is_playing", False)
        
        # Track name (scrolling if needed)
        self._scroll_text_line(track, 0)
        
        # Artist name (scrolling if needed)
        self._scroll_text_line(artists, 12)
        
        # Progress bar at bottom
        pct = progress / duration if duration > 0 else 0
        self._draw_progress_bar(0, 50, 128, 12, pct, progress, duration)
        
        # Play/pause indicator
        if is_playing:
            # Playing arrow (simplified)
            self.display.fill_rect(120, 55, 2, 6, 1)
            self.display.fill_rect(122, 56, 2, 4, 1)
            self.display.fill_rect(124, 57, 2, 2, 1)
        else:
            # Pause bars
            self.display.fill_rect(120, 54, 3, 8, 1)
            self.display.fill_rect(124, 54, 3, 8, 1)
            
        self.show()
    
    def show_track_focus(self, data):
        """Mode 2: Large track name, small artist."""
        self.clear()
        track = data.get("track", "")
        artists = data.get("artists", "")
        
        # Large track name (2x scale, scrolls)
        self._scroll_text_line(track, 0, 128)
        
        # Small artist
        self.display.text(artists[:16], 0, 32, 1)
        
        # Progress
        progress = data.get("progress_ms", 0)
        duration = data.get("duration_ms", 0)
        pct = progress / duration if duration > 0 else 0
        self._draw_progress_bar(0, 50, 128, 12, pct, progress, duration)
        
        self.show()
    
    def show_album_context(self, data):
        """Mode 3: Album + context."""
        self.clear()
        album = data.get("album", "")
        track = data.get("track", "")
        
        self.display.text("Album:", 0, 0, 1)
        self._scroll_text_line(album, 10)
        self.display.text("Track:", 0, 30, 1)
        self._scroll_text_line(track, 40)
        
        self.show()
    
    def show_device_volume(self, data):
        """Mode 4: Device name + volume."""
        self.clear()
        device = data.get("device", "Unknown")
        volume = data.get("volume", 0)
        
        self.display.text("Device:", 0, 0, 1)
        self._scroll_text_line(device, 10)
        
        # Volume bar
        self.display.text(f"Vol: {volume}%", 0, 30, 1)
        self.display.rect(0, 42, 128, 10, 1)
        fill = int(126 * volume / 100)
        if fill > 0:
            self.display.fill_rect(1, 43, fill, 8, 1)
            
        self.show()
    
    def show_status(self):
        """Mode 5: System status."""
        self.clear()
        import gc
        from wifi import wifi
        
        ip = wifi.get_ip()
        rssi = wifi.get_rssi()
        free_mem = gc.mem_free()
        
        self.display.text("Status:", 0, 0, 1)
        self.display.text(f"IP: {ip}", 0, 12, 1)
        self.display.text(f"RSSI: {rssi} dBm", 0, 22, 1)
        self.display.text(f"Free: {free_mem//1024} KB", 0, 32, 1)
        
        uptime = time.ticks_ms() // 1000
        h = uptime // 3600
        m = (uptime % 3600) // 60
        s = uptime % 60
        self.display.text(f"Up: {h:02d}:{m:02d}:{s:02d}", 0, 42, 1)
        
        self.show()
    
    def show_clock(self):
        """Mode 6: Large clock (when nothing playing)."""
        self.clear()
        # This would need RTC - showing uptime instead
        uptime = time.ticks_ms() // 1000
        h = uptime // 3600
        m = (uptime % 3600) // 60
        s = uptime % 60
        
        # Large time
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        x = (128 - len(time_str) * 16) // 2
        self.display.text_large(time_str, x, 20, 1, scale=2)
        
        self.display.text("No playback", 30, 50, 1)
        self.show()
    
    def show_message(self, line1, line2="", line3=""):
        """Show simple message (connecting, error, etc.)"""
        self.clear()
        self.display.text(line1, 0, 10, 1)
        if line2:
            self.display.text(line2, 0, 25, 1)
        if line3:
            self.display.text(line3, 0, 40, 1)
        self.show()
    
    def show_error(self, error):
        self.clear()
        self.display.text("Error:", 0, 0, 1)
        # Wrap error text
        words = error.split()
        line = ""
        y = 12
        for word in words:
            test = line + word + " "
            if len(test) * 8 > 128:
                self.display.text(line, 0, y, 1)
                line = word + " "
                y += 12
            else:
                line = test
        if line:
            self.display.text(line, 0, y, 1)
        self.show()


# Global instance
spotify_display = SpotifyDisplay()