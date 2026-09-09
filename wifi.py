# wifi.py - WiFi connection management with auto-reconnect

import network
import time
from config import WIFI_SSID, WIFI_PASS

class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.connected = False
        self.last_attempt = 0
        self.retry_delay = 5  # seconds
        
    def connect(self, timeout=20):
        """Connect to WiFi with timeout. Returns True if connected."""
        if self.wlan.isconnected():
            self.connected = True
            return True
            
        print(f"Connecting to WiFi: {WIFI_SSID}...")
        self.wlan.connect(WIFI_SSID, WIFI_PASS)
        
        start = time.ticks_ms()
        while not self.wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > timeout * 1000:
                print("WiFi connection timeout")
                return False
            time.sleep_ms(500)
            
        self.connected = True
        self.retry_delay = 5
        ip = self.wlan.ifconfig()[0]
        print(f"WiFi connected: {ip}")
        return True
    
    def ensure_connected(self):
        """Ensure WiFi is connected, reconnect if needed."""
        if self.wlan.isconnected():
            self.connected = True
            return True
            
        if self.connected:
            print("WiFi disconnected, reconnecting...")
            self.connected = False
            
        # Exponential backoff
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_attempt) < self.retry_delay * 1000:
            return False
            
        self.last_attempt = now
        result = self.connect(timeout=15)
        if not result:
            self.retry_delay = min(self.retry_delay * 2, 300)  # Max 5 min
        return result
    
    def get_ip(self):
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        return "0.0.0.0"
    
    def get_rssi(self):
        if self.wlan.isconnected():
            return self.wlan.status('rssi')
        return -100
    
    def disconnect(self):
        self.wlan.disconnect()
        self.connected = False


# Global instance
wifi = WiFiManager()