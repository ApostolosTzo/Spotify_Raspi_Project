# display.py - SH1107 display wrapper for Spotify now-playing
# Portrait mode: 64 wide x 128 tall

from machine import Pin, SPI
import time
import sh1107
import framebuf2
from config import DISPLAY_ROTATE, DISPLAY_CONTRAST

SPI_SCK = 10
SPI_MOSI = 11
SPI_CS = 9
SPI_DC = 8
SPI_RST = 12

WIDTH = 64
HEIGHT = 128

class SpotifyDisplay:
    def __init__(self):
        self.spi = SPI(1, baudrate=10_000_000, sck=Pin(SPI_SCK), mosi=Pin(SPI_MOSI))
        self.cs = Pin(SPI_CS, Pin.OUT, value=1)
        self.dc = Pin(SPI_DC, Pin.OUT, value=0)
        self.rst = Pin(SPI_RST, Pin.OUT, value=1)

        self.display = sh1107.SH1107_SPI(
            WIDTH, HEIGHT, self.spi, self.dc, self.rst, self.cs,
            rotate=DISPLAY_ROTATE, delay_ms=200
        )
        self.display.contrast(DISPLAY_CONTRAST)

        self.scroll_offset = 0
        self.scroll_last_update = 0
        self.scroll_speed = 150

    def clear(self):
        self.display.fill(0)

    def show(self):
        self.display.show()

    def _draw_progress_bar(self, x, y, w, h, progress, current_ms, total_ms):
        self.display.rect(x, y, w, h, 1)
        if total_ms > 0:
            fill_w = int((w - 2) * progress)
            if fill_w > 0:
                self.display.fill_rect(x + 1, y + 1, fill_w, h - 2, 1)
        cur_str = self._format_time(current_ms)
        tot_str = self._format_time(total_ms)
        self.display.text(cur_str, x, y - 10, 1)
        self.display.text(tot_str, x + w - len(tot_str) * 8, y - 10, 1)

    def _format_time(self, ms):
        if ms < 0:
            ms = 0
        total_sec = ms // 1000
        m = total_sec // 60
        s = total_sec % 60
        return f"{m}:{s:02d}"

    def _scroll_text_line(self, text, y, max_width=64):
        text_w = len(text) * 8
        if text_w <= max_width:
            self.display.text(text, 0, y, 1)
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, self.scroll_last_update) >= self.scroll_speed:
            self.scroll_last_update = now
            self.scroll_offset = (self.scroll_offset + 1) % (text_w + 10)
        for i, char in enumerate(text):
            char_x = i * 8 - self.scroll_offset
            if -8 < char_x < max_width:
                self.display.text(char, char_x, y, 1)

    def show_now_playing(self, data):
        self.clear()
        track = data.get("track", "")
        artists = data.get("artists", "")
        progress = data.get("progress_ms", 0)
        duration = data.get("duration_ms", 0)
        is_playing = data.get("is_playing", False)

        self._scroll_text_line(track, 0)
        self._scroll_text_line(artists, 16)

        pct = progress / duration if duration > 0 else 0
        self._draw_progress_bar(0, 110, 64, 10, pct, progress, duration)

        if is_playing:
            self.display.fill_rect(56, 100, 2, 6, 1)
            self.display.fill_rect(58, 101, 2, 4, 1)
            self.display.fill_rect(60, 102, 2, 2, 1)
        else:
            self.display.fill_rect(56, 100, 3, 8, 1)
            self.display.fill_rect(60, 100, 3, 8, 1)

        self.show()

    def show_track_focus(self, data):
        self.clear()
        track = data.get("track", "")
        artists = data.get("artists", "")
        self._scroll_text_line(track, 0)
        self.display.text(artists[:8], 0, 40, 1)
        progress = data.get("progress_ms", 0)
        duration = data.get("duration_ms", 0)
        pct = progress / duration if duration > 0 else 0
        self._draw_progress_bar(0, 110, 64, 10, pct, progress, duration)
        self.show()

    def show_album_context(self, data):
        self.clear()
        album = data.get("album", "")
        track = data.get("track", "")
        self.display.text("Album:", 0, 0, 1)
        self._scroll_text_line(album, 16)
        self.display.text("Track:", 0, 48, 1)
        self._scroll_text_line(track, 64)
        self.show()

    def show_device_volume(self, data):
        self.clear()
        device = data.get("device", "Unknown")
        volume = data.get("volume", 0)
        self.display.text("Device:", 0, 0, 1)
        self._scroll_text_line(device, 16)
        self.display.text(f"Vol: {volume}%", 0, 48, 1)
        self.display.rect(0, 64, 64, 10, 1)
        fill = int(62 * volume / 100)
        if fill > 0:
            self.display.fill_rect(1, 65, fill, 8, 1)
        self.show()

    def show_status(self):
        self.clear()
        import gc
        from wifi import wifi
        ip = wifi.get_ip()
        rssi = wifi.get_rssi()
        free_mem = gc.mem_free()
        self.display.text("Status:", 0, 0, 1)
        self.display.text(f"IP:", 0, 16, 1)
        self.display.text(ip[:8], 0, 32, 1)
        self.display.text(f"RSSI:{rssi}", 0, 48, 1)
        self.display.text(f"Mem:{free_mem//1024}K", 0, 64, 1)
        uptime = time.ticks_ms() // 1000
        h = uptime // 3600
        m = (uptime % 3600) // 60
        s = uptime % 60
        self.display.text(f"{h:02d}:{m:02d}:{s:02d}", 0, 80, 1)
        self.show()

    def show_clock(self):
        self.clear()
        uptime = time.ticks_ms() // 1000
        h = uptime // 3600
        m = (uptime % 3600) // 60
        s = uptime % 60
        time_str = f"{h:02d}:{m:02d}"
        x = (64 - len(time_str) * 8) // 2
        self.display.text(time_str, x, 20, 1)
        time_str2 = f"{s:02d}"
        x2 = (64 - len(time_str2) * 8) // 2
        self.display.text(time_str2, x2, 40, 1)
        self.display.text("No playback", 0, 70, 1)
        self.show()

    def show_message(self, line1, line2="", line3=""):
        self.clear()
        y = 10
        self.display.text(line1, 0, y, 1)
        if line2:
            y += 16
            self.display.text(line2, 0, y, 1)
        if line3:
            y += 16
            self.display.text(line3, 0, y, 1)
        self.show()

    def show_error(self, error):
        self.clear()
        self.display.text("Error:", 0, 0, 1)
        words = error.split()
        line = ""
        y = 16
        for word in words:
            test = line + word + " "
            if len(test) * 8 > 64:
                self.display.text(line[:8], 0, y, 1)
                line = word + " "
                y += 12
            else:
                line = test
        if line:
            self.display.text(line[:8], 0, y, 1)
        self.show()


spotify_display = SpotifyDisplay()