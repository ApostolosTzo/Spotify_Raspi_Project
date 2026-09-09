# Spotify Now-Playing Display for Raspberry Pi Pico 2 W + Pico-OLED-1.3

Displays currently playing Spotify track on a 1.3" 64×128 SH1107 OLED with playback controls via onboard buttons.

## Hardware

| Component | Details |
|-----------|---------|
| MCU | Raspberry Pi Pico 2 W (RP2350) with pre-soldered headers |
| Display | Waveshare Pico-OLED-1.3" 64×128 SH1107 (SPI) |
| Buttons | KEY0 (GP15), KEY1 (GP17) - onboard |

## Wiring

Pre-assembled - just plug the display onto the Pico 2 W headers.  
SPI pins (fixed on board): SCK=GP10, MOSI=GP11, CS=GP9, DC=GP8, RST=GP12

## Setup

### 1. Flash MicroPython on Pico 2 W
- Download `.uf2` for **Pico 2 W** (RP2350): https://micropython.org/download/rp2-pico-w/
- Hold BOOTSEL, plug in USB, drag `.uf2` to RPI-RP2 drive

### 2. Create Spotify App
1. Go to https://developer.spotify.com/dashboard
2. Create App: "Pico Spotify Display"
3. Redirect URI: `http://localhost:8888/callback`
4. Copy **Client ID** and **Client Secret**

### 3. Generate Refresh Token (on your computer)
```bash
# Edit get_refresh_token.py with your Client ID/Secret
python get_refresh_token.py
```
- Browser opens → log in → authorize
- Copy the **refresh_token** output

### 4. Deploy Code to Pico
**Via Thonny:**
1. Open Thonny → Interpreter → MicroPython (Raspberry Pi Pico)
2. View → Files → navigate to this folder
3. Upload all `.py` files to device
4. Create `config.py` on device with your credentials:
```python
WIFI_SSID = "your-wifi"
WIFI_PASS = "your-password"
SPOTIFY_CLIENT_ID = "your-client-id"
SPOTIFY_REFRESH_TOKEN = "your-refresh-token"
```
5. Press `Ctrl+D` to reboot

**Via mpremote:**
```bash
pip install mpremote
mpremote connect auto fs cp *.py :
# Then create config.py via Thonny or mpremote repl
```

## Button Controls

| Button | Short Press | Long Press (1s) |
|--------|-------------|-----------------|
| **KEY0** | Cycle display mode | Play / Pause |
| **KEY1** | Next track | Previous track |

## Display Modes (cycle with KEY0)

1. **Now Playing** - Track + Artist + Progress bar + time
2. **Track Focus** - Large track name + artist
3. **Album** - Album name + track
4. **Device** - Active device + volume bar
5. **Status** - WiFi, IP, memory, uptime
6. **Clock** - Large time (when nothing playing)

Auto-reverts to Mode 1 after 30 seconds in other modes.

## Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point, main loop |
| `config.py` | Your credentials (create on device) |
| `config.py.template` | Template for config.py |
| `wifi.py` | WiFi connect/reconnect |
| `spotify.py` | Spotify API (token refresh, polling, controls) |
| `display.py` | SH1107 driver wrapper, rendering |
| `buttons.py` | Button debounce + short/long press |
| `sh1107.py` | SH1107 SPI driver |
| `framebuf2.py` | Large font support (2x scale) |
| `get_refresh_token.py` | Run on computer to get refresh token |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "WiFi failed" | Check SSID/password in config.py |
| "Spotify: 401" | Refresh token invalid → re-run get_refresh_token.py |
| "Spotify: 403" | Need Premium account for playback control |
| Display garbled | Check SPI pins match board (GP8-12) |
| Buttons not working | Verify KEY0=GP15, KEY1=GP17 in config.py |
| Nothing playing shows | Start playback on another Spotify device first |

## Rate Limits

- Polling: 10 seconds (configurable in config.py)
- Spotify allows ~100 requests/30 seconds per user
- Play/Pause/Next use separate endpoints with same limits

## License

MIT - Based on peter-l5/SH1107 and peter-l5/framebuf2