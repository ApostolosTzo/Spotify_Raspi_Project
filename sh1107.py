# sh1107.py - SH1107 OLED driver for Waveshare Pico-OLED-1.3 (64x128, SPI)
# For landscape use: framebuf 128x64, hardware rotation via SEG_REMAP + COM_SCAN_DIR

import framebuf
import time

class SH1107_SPI:
    def __init__(self, width, height, spi, dc, res=None, cs=None,
                 rotate=0, external_vcc=False, delay_ms=200):
        self.width = width
        self.height = height
        self.spi = spi
        self.dc = dc
        self.cs = cs
        self.res = res
        self.rotate = rotate
        self.pages = height // 8
        self.buffer = bytearray(width * self.pages)
        self.fb = framebuf.FrameBuffer(self.buffer, width, height, framebuf.MONO_VLSB)

        dc.init(dc.OUT, value=0)
        if cs is not None:
            cs.init(cs.OUT, value=1)
        if res is not None:
            res.init(res.OUT, value=1)
            time.sleep_ms(1)
            res(0)
            time.sleep_ms(10)
            res(1)
            time.sleep_ms(delay_ms)

        self._cmd(0xAE)
        self._cmd(0xA8, height - 1)
        self._cmd(0xD3, 0x00)
        self._cmd(0x40)
        self._cmd(0x8D, 0x14)
        self._cmd(0x20, 0x00)
        if rotate == 90 or rotate == 270:
            self._cmd(0xA1)
            self._cmd(0xC8)
        else:
            self._cmd(0xA0)
            self._cmd(0xC0)
        self._cmd(0xDA, 0x12)
        self._cmd(0x81, 0x80)
        self._cmd(0xD9, 0xF1)
        self._cmd(0xDB, 0x40)
        self._cmd(0xD5, 0x80)
        self._cmd(0xA4)
        self._cmd(0xA6)
        self._cmd(0xAF)
        self.fill(0)
        self.show()

    def _cmd(self, *cmd):
        self.dc(0)
        if self.cs is not None:
            self.cs(0)
        self.spi.write(bytearray(cmd))
        if self.cs is not None:
            self.cs(1)

    def _data(self, buf):
        self.dc(1)
        if self.cs is not None:
            self.cs(0)
        self.spi.write(buf)
        if self.cs is not None:
            self.cs(1)

    def show(self):
        for page in range(self.pages):
            self._cmd(0xB0 | page)
            self._cmd(0x02)
            self._cmd(0x10)
            start = page * self.width
            end = start + self.width
            self._data(self.buffer[start:end])

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