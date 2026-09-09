# MicroPython SH1107 OLED driver for 64x128 displays (Waveshare Pico-OLED-1.3)
# Based on peter-l5/SH1107 (MIT License), adapted for Pico 2 W + SH1107 64x128 SPI
# SPDX-License-Identifier: MIT

import framebuf
import time
from micropython import const

# SH1107 commands
SET_COL_LOW = const(0x00)
SET_COL_HIGH = const(0x10)
SET_PAGE = const(0xB0)
SET_DISPLAY_ON = const(0xAF)
SET_DISPLAY_OFF = const(0xAE)
SET_DISP_START_LINE = const(0x40)
SET_CONTRAST = const(0x81)
SET_SEG_REMAP = const(0xA1)
SET_MUX_RATIO = const(0xA8)
SET_COM_SCAN_DIR = const(0xC8)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)
SET_MEMORY_MODE = const(0x20)
SET_NOP = const(0xE3)

class SH1107(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc=False, delay_ms=200, rotate=0):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.delay_ms = delay_ms
        self.rotate = rotate % 360
        self.flip_flag = (self.rotate == 180) or (self.rotate == 270)
        self.pages = height // 8
        self.row_width = width
        bufsize = width * self.pages
        self.buffer = bytearray(bufsize)
        super().__init__(self.buffer, width, height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        self.reset()
        self.write_cmd(SET_DISPLAY_OFF)
        self.write_cmd(SET_DISP_CLK_DIV, 0x80)
        self.write_cmd(SET_MUX_RATIO, self.height - 1)
        self.write_cmd(SET_DISP_OFFSET, 0x00)
        self.write_cmd(SET_DISP_START_LINE)
        self.write_cmd(SET_CHARGE_PUMP, 0x14)
        self.write_cmd(SET_MEMORY_MODE, 0x00)
        self.write_cmd(SET_SEG_REMAP)
        self.write_cmd(SET_COM_SCAN_DIR)
        self.write_cmd(SET_COM_PIN_CFG, 0x12 if self.height == 64 else 0x22)
        self.write_cmd(SET_CONTRAST, 0x80)
        self.write_cmd(SET_PRECHARGE, 0xF1)
        self.write_cmd(SET_VCOM_DESEL, 0x40)
        self.write_cmd(0xA4)
        self.write_cmd(0xA6)
        self.write_cmd(SET_DISPLAY_ON)
        self.fill(0)
        self.show()

    def reset(self):
        if hasattr(self, 'res') and self.res is not None:
            self.res(1)
            time.sleep_ms(1)
            self.res(0)
            time.sleep_ms(10)
            self.res(1)
            time.sleep_ms(self.delay_ms)

    def write_cmd(self, *cmd):
        raise NotImplementedError

    def write_data(self, buf):
        raise NotImplementedError

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.rotate in (90, 270):
            x0 = 0
            x1 = self.height - 1
        for page in range(self.pages):
            self.write_cmd(SET_PAGE | page)
            self.write_cmd(SET_COL_LOW | (x0 & 0x0F))
            self.write_cmd(SET_COL_HIGH | ((x0 >> 4) & 0x0F))
            start = page * self.row_width
            end = start + self.row_width
            self.write_data(self.buffer[start:end])

    def poweron(self):
        self.write_cmd(SET_DISPLAY_ON)

    def poweroff(self):
        self.write_cmd(SET_DISPLAY_OFF)

    def contrast(self, value):
        self.write_cmd(SET_CONTRAST, value)

    def invert(self, value):
        self.write_cmd(0xA7 if value else 0xA6)


class SH1107_SPI(SH1107):
    def __init__(self, width, height, spi, dc, res=None, cs=None, rotate=0, external_vcc=False, delay_ms=200):
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        dc.init(dc.OUT, value=0)
        if res is not None:
            res.init(res.OUT, value=1)
        if cs is not None:
            cs.init(cs.OUT, value=1)
        super().__init__(width, height, external_vcc, delay_ms, rotate)

    def write_cmd(self, *cmd):
        self.dc(0)
        if self.cs is not None:
            self.cs(0)
        self.spi.write(bytearray(cmd))
        if self.cs is not None:
            self.cs(1)

    def write_data(self, buf):
        self.dc(1)
        if self.cs is not None:
            self.cs(0)
        self.spi.write(buf)
        if self.cs is not None:
            self.cs(1)


class SH1107_I2C(SH1107):
    def __init__(self, width, height, i2c, res=None, address=0x3C, rotate=0, external_vcc=False, delay_ms=200):
        self.i2c = i2c
        self.address = address
        self.res = res
        if res is not None:
            res.init(res.OUT, value=1)
        super().__init__(width, height, external_vcc, delay_ms, rotate)

    def write_cmd(self, *cmd):
        self.i2c.writeto(self.address, b'\x00' + bytes(cmd))

    def write_data(self, buf):
        self.i2c.writeto(self.address, b'\x40' + buf)