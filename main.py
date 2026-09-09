# main.py - Main entry point for Spotify Now-Playing Display

import time
import gc
from wifi import wifi
from spotify import spotify
from display import spotify_display
from buttons import buttons

# Display modes
MODE_NOW_PLAYING = 0
MODE_TRACK_FOCUS = 1
MODE_ALBUM = 2
MODE_DEVICE = 3
MODE_STATUS = 4
MODE_CLOCK = 5
MODE_COUNT = 6

current_mode = MODE_NOW_PLAYING
last_mode_change = 0
AUTO_REVERT_MS = 30000  # Return to now-playing after 30s

def handle_buttons(actions):
    """Process button actions and update mode/playback."""
    global current_mode, last_mode_change
    
    if actions.get("key0_short"):
        # Cycle display mode
        current_mode = (current_mode + 1) % MODE_COUNT
        last_mode_change = time.ticks_ms()
        print(f"Mode: {current_mode}")
        
    elif actions.get("key0_long"):
        # Play/Pause toggle
        data = spotify.last_data or {}
        if data.get("playing") and data.get("is_playing"):
            spotify.pause()
        else:
            spotify.play()
            
    elif actions.get("key1_short"):
        # Next track
        spotify.next_track()
        
    elif actions.get("key1_long"):
        # Previous track
        spotify.prev_track()

def render_display(data):
    """Render current mode."""
    global current_mode, last_mode_change
    
    # Auto-revert to now-playing after timeout (except mode 0 and 5)
    if current_mode not in (MODE_NOW_PLAYING, MODE_CLOCK):
        if time.ticks_diff(time.ticks_ms(), last_mode_change) > AUTO_REVERT_MS:
            current_mode = MODE_NOW_PLAYING
    
    if not data or not data.get("playing"):
        # Nothing playing - show clock or message
        if current_mode == MODE_CLOCK:
            spotify_display.show_clock()
        else:
            spotify_display.show_message("Nothing playing", "Press KEY1 for next")
        return
    
    # Render based on mode
    if current_mode == MODE_NOW_PLAYING:
        spotify_display.show_now_playing(data)
    elif current_mode == MODE_TRACK_FOCUS:
        spotify_display.show_track_focus(data)
    elif current_mode == MODE_ALBUM:
        spotify_display.show_album_context(data)
    elif current_mode == MODE_DEVICE:
        spotify_display.show_device_volume(data)
    elif current_mode == MODE_STATUS:
        spotify_display.show_status()
    elif current_mode == MODE_CLOCK:
        spotify_display.show_clock()

def main():
    print("=== Spotify Now-Playing Display ===")
    print("Starting up...")
    
    # Show boot message
    spotify_display.show_message("Connecting WiFi...")
    
    # Connect WiFi
    if not wifi.connect(timeout=30):
        spotify_display.show_error("WiFi failed\nCheck config.py")
        while True:
            time.sleep(10)
            if wifi.connect(timeout=15):
                break
    
    spotify_display.show_message("WiFi OK", "Connecting Spotify...")
    
    # Initial Spotify fetch
    data = spotify.get_currently_playing()
    if spotify.last_error:
        spotify_display.show_error(f"Spotify: {spotify.last_error}")
        time.sleep(3)
    
    print("Entering main loop...")
    last_gc = time.ticks_ms()
    
    while True:
        try:
            # Ensure WiFi
            wifi.ensure_connected()
            
            # Poll Spotify
            data = spotify.get_currently_playing()
            
            # Poll buttons
            actions = buttons.poll()
            if actions:
                handle_buttons(actions)
            
            # Render display
            render_display(data)
            
            # Periodic garbage collection
            if time.ticks_diff(time.ticks_ms(), last_gc) > 60000:
                gc.collect()
                last_gc = time.ticks_ms()
                
            # Small delay to prevent tight loop
            time.sleep_ms(100)
            
        except Exception as e:
            print(f"Main loop error: {e}")
            spotify_display.show_error(str(e))
            time.sleep(5)


if __name__ == "__main__":
    main()