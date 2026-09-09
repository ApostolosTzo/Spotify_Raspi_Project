# spotify.py - Spotify API client with token refresh and playback polling

import urequests
import ujson
import time
from config import SPOTIFY_CLIENT_ID, SPOTIFY_REFRESH_TOKEN, SPOTIFY_POLL_INTERVAL
from wifi import wifi

TOKEN_URL = "https://accounts.spotify.com/api/token"
PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"
PLAY_URL = "https://api.spotify.com/v1/me/player/play"
PAUSE_URL = "https://api.spotify.com/v1/me/player/pause"
NEXT_URL = "https://api.spotify.com/v1/me/player/next"
PREV_URL = "https://api.spotify.com/v1/me/player/previous"

class SpotifyClient:
    def __init__(self):
        self.access_token = None
        self.token_expiry = 0
        self.last_poll = 0
        self.last_data = None
        self.last_error = None
        
    def _refresh_token(self):
        """Refresh access token using refresh token."""
        print("Refreshing Spotify access token...")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = "grant_type=refresh_token&refresh_token={}&client_id={}".format(
            SPOTIFY_REFRESH_TOKEN, SPOTIFY_CLIENT_ID
        )
        
        try:
            resp = urequests.post(TOKEN_URL, headers=headers, data=data)
            if resp.status_code == 200:
                token_data = resp.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expiry = time.ticks_add(time.ticks_ms(), expires_in * 1000)
                print("Token refreshed successfully")
                resp.close()
                return True
            else:
                print(f"Token refresh failed: {resp.status_code} - {resp.text}")
                resp.close()
                return False
        except Exception as e:
            print(f"Token refresh error: {e}")
            return False
    
    def _ensure_token(self):
        """Ensure we have a valid access token."""
        if self.access_token is None or time.ticks_diff(self.token_expiry, time.ticks_ms()) < 60000:
            return self._refresh_token()
        return True
    
    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def get_currently_playing(self):
        """Get currently playing track. Returns dict or None."""
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_poll) < SPOTIFY_POLL_INTERVAL * 1000:
            return self.last_data
            
        if not wifi.ensure_connected():
            self.last_error = "WiFi not connected"
            return self.last_data
            
        if not self._ensure_token():
            self.last_error = "Token refresh failed"
            return self.last_data
            
        self.last_poll = now
        
        try:
            resp = urequests.get(PLAYING_URL, headers=self._auth_headers())
            
            if resp.status_code == 204:
                # No content - nothing playing
                self.last_data = {"playing": False}
                resp.close()
                return self.last_data
                
            if resp.status_code == 401:
                # Token expired, force refresh and retry once
                resp.close()
                self.access_token = None
                if self._ensure_token():
                    return self.get_currently_playing()
                self.last_error = "Auth failed after refresh"
                return self.last_data
                
            if resp.status_code == 429:
                # Rate limited
                retry_after = int(resp.headers.get("Retry-After", "30"))
                print(f"Rate limited, waiting {retry_after}s")
                resp.close()
                self.last_error = f"Rate limited ({retry_after}s)"
                return self.last_data
                
            if resp.status_code != 200:
                print(f"Spotify API error: {resp.status_code} - {resp.text}")
                resp.close()
                self.last_error = f"API error: {resp.status_code}"
                return self.last_data
                
            data = resp.json()
            resp.close()
            
            # Parse relevant fields
            self.last_data = self._parse_playing(data)
            self.last_error = None
            return self.last_data
            
        except Exception as e:
            print(f"Spotify request error: {e}")
            self.last_error = str(e)
            return self.last_data
    
    def _parse_playing(self, data):
        """Parse Spotify API response into simplified dict."""
        if not data:
            return {"playing": False}
            
        item = data.get("item")
        if not item:
            return {"playing": False}
            
        track = item.get("name", "Unknown")
        artists = ", ".join([a["name"] for a in item.get("artists", [])])
        album = item.get("album", {}).get("name", "")
        progress = data.get("progress_ms", 0)
        duration = item.get("duration_ms", 0)
        is_playing = data.get("is_playing", False)
        device = data.get("device", {}).get("name", "")
        volume = data.get("device", {}).get("volume_percent", 0)
        
        return {
            "playing": True,
            "track": track,
            "artists": artists,
            "album": album,
            "progress_ms": progress,
            "duration_ms": duration,
            "is_playing": is_playing,
            "device": device,
            "volume": volume,
        }
    
    def play(self):
        """Resume playback."""
        if not self._ensure_token():
            return False
        try:
            resp = urequests.put(PLAY_URL, headers=self._auth_headers())
            result = resp.status_code in (200, 204)
            resp.close()
            return result
        except Exception as e:
            print(f"Play error: {e}")
            return False
    
    def pause(self):
        """Pause playback."""
        if not self._ensure_token():
            return False
        try:
            resp = urequests.put(PAUSE_URL, headers=self._auth_headers())
            result = resp.status_code in (200, 204)
            resp.close()
            return result
        except Exception as e:
            print(f"Pause error: {e}")
            return False
    
    def next_track(self):
        """Skip to next track."""
        if not self._ensure_token():
            return False
        try:
            resp = urequests.post(NEXT_URL, headers=self._auth_headers())
            result = resp.status_code in (200, 204)
            resp.close()
            return result
        except Exception as e:
            print(f"Next track error: {e}")
            return False
    
    def prev_track(self):
        """Skip to previous track."""
        if not self._ensure_token():
            return False
        try:
            resp = urequests.post(PREV_URL, headers=self._auth_headers())
            result = resp.status_code in (200, 204)
            resp.close()
            return result
        except Exception as e:
            print(f"Prev track error: {e}")
            return False


# Global instance
spotify = SpotifyClient()