# buttons.py - Button handling for Pico-OLED-1.3 (KEY0=GP15, KEY1=GP17)

from machine import Pin
import time
from config import KEY0_PIN, KEY1_PIN

class Buttons:
    def __init__(self):
        self.key0 = Pin(KEY0_PIN, Pin.IN, Pin.PULL_UP)
        self.key1 = Pin(KEY1_PIN, Pin.IN, Pin.PULL_UP)
        
        self.key0_last = 1
        self.key1_last = 1
        self.key0_press_time = 0
        self.key1_press_time = 0
        self.key0_long_triggered = False
        self.key1_long_triggered = False
        self.debounce_ms = 50
        self.long_press_ms = 800
        
    def poll(self):
        """Poll buttons, return dict of actions detected."""
        now = time.ticks_ms()
        actions = {}
        
        # KEY0
        key0_state = self.key0.value()
        if key0_state == 0 and self.key0_last == 1:
            # Press detected
            self.key0_press_time = now
            self.key0_long_triggered = False
        elif key0_state == 1 and self.key0_last == 0:
            # Release detected
            press_duration = time.ticks_diff(now, self.key0_press_time)
            if press_duration >= self.debounce_ms:
                if press_duration >= self.long_press_ms:
                    actions["key0_long"] = True
                else:
                    actions["key0_short"] = True
            self.key0_press_time = 0
        elif key0_state == 0 and not self.key0_long_triggered:
            # Held down - check for long press
            if time.ticks_diff(now, self.key0_press_time) >= self.long_press_ms:
                actions["key0_long"] = True
                self.key0_long_triggered = True
        self.key0_last = key0_state
        
        # KEY1
        key1_state = self.key1.value()
        if key1_state == 0 and self.key1_last == 1:
            self.key1_press_time = now
            self.key1_long_triggered = False
        elif key1_state == 1 and self.key1_last == 0:
            press_duration = time.ticks_diff(now, self.key1_press_time)
            if press_duration >= self.debounce_ms:
                if press_duration >= self.long_press_ms:
                    actions["key1_long"] = True
                else:
                    actions["key1_short"] = True
            self.key1_press_time = 0
        elif key1_state == 0 and not self.key1_long_triggered:
            if time.ticks_diff(now, self.key1_press_time) >= self.long_press_ms:
                actions["key1_long"] = True
                self.key1_long_triggered = True
        self.key1_last = key1_state
        
        return actions


# Global instance
buttons = Buttons()