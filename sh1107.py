# sh1107.py - SH1107 OLED driver for Waveshare Pico-OLED-1.3
# 64x128 portrait display. Landscape mode rotates 90 CW for USB-left viewing.

import framebuf
import time

class SH1107_SPI:
    def __init__(self, spi, dc, cs, res, landscape=True, delay_ms=200):
        self.spi = spi
        self.dc = dc
        self.cs = cs
        self.res = res
        self.landscape = landscape
        self.width = 128 if landscape else 64
        self.height = 64 if landscape else 128
        self.buffer = bytearray(1024)
        self.fb = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self._portrait_buf = bytearray(1024)

        dc.init(dc.OUT, value=0)
        cs.init(cs.OUT, value=1)
        res.init(res.OUT, value=1)
        time.sleep_ms(1)
        res(0)
        time.sleep_ms(10)
        res(1)
        time.sleep_ms(delay_ms)

        self._cmd(0xAE)
        self._cmd(0xA8, 0x7F)
        self._cmd(0xD3, 0x00)
        self._cmd(0x40)
        self._cmd(0x8D, 0x14)
        self._cmd(0x20, 0x00)
        self._cmd(0xA1)
        self._cmd(0xC8)
        self._cmd(0xDA, 0x12)
        self._cmd(0x81, 0xFF)
        self._cmd(0xD9, 0xF1)
        self._cmd(0xDB, 0x40)
        self._cmd(0xD5, 0x80)
        self._cmd(0xA4)
        self._cmd(0xA6)
        self._cmd(0xAF)
        self.fb.fill(0)
        self.show()

    def _cmd(self, *cmd):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray(cmd))
        self.cs(1)

    def _data(self, buf):
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)

    def show(self):
        if not self.landscape:
            for page in range(16):
                self._cmd(0xB0 | page)
                self._cmd(0x00)
                self._cmd(0x12)
                self._data(self.buffer[page * 64:(page + 1) * 64])
            return
        for page in range(16):
            self._cmd(0xB0 | page)
            self._cmd(0x00)
            self._cmd(0x12)
            for c in range(64):
                byte = 0
                for b in range(8):
                    lx = page * 8 + b
                    ly = 63 - c
                    byte_idx = (ly >> 3) * 128 + lx
                    if self.buffer[byte_idx] & (1 << (ly & 7)):
                        byte |= (1 << b)
                self._portrait_buf[c] = byte
            self._data(self._portrait_buf[:64])

    def fill(self, c):
        self.fb.fill(c)

    def pixel(self, x, y, c=None):
        if c is None:
            return self.fb.pixel(x, y)
        self.fb.pixel(x, y, c)

    def text(self, s, x, y, c=1):
        self.fb.text(s, x, y, c)

    def rect(self, x, y, w, h, c):
        self.fb.rect(x, y, w, h, c)

    def fill_rect(self, x, y, w, h, c):
        self.fb.fill_rect(x, y, w, h, c)

    def scroll(self, dx, dy):
        self.fb.scroll(dx, dy)

    def contrast(self, value):
        self._cmd(0x81, value)

    def invert(self, value):
        self._cmd(0xA7 if value else 0xA6)

    def poweron(self):
        self._cmd(0xAF)

    def poweroff(self):
        self._cmd(0xAE)
