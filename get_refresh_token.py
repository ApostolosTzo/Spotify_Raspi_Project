# get_refresh_token.py - Run on YOUR COMPUTER to generate Spotify refresh token
# Run: python get_refresh_token.py
# Requires: pip install requests flask

import os
import sys
import json
import base64
import hashlib
import secrets
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import webbrowser

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# ==== CONFIGURE THESE FROM SPOTIFY DEVELOPER DASHBOARD ====
CLIENT_ID = "YOUR_CLIENT_ID_HERE"
CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"
REDIRECT_URI = "http://localhost:8888/callback"
# ===========================================================

SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/callback"):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if "code" in params:
                auth_code = params["code"][0]
                self.server.auth_code = auth_code
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                <html><body style='font-family:sans-serif;text-align:center;padding:50px'>
                <h1>Success!</h1>
                <p>Authorization code received.</p>
                <p>You can close this window.</p>
                </body></html>
                """)
            elif "error" in params:
                self.server.auth_error = params["error"][0]
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f"Error: {params['error'][0]}".encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress log output

def generate_pkce():
    """Generate PKCE code verifier and challenge."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    return code_verifier, code_challenge

def start_callback_server(port=8888):
    server = HTTPServer(("localhost", port), CallbackHandler)
    server.auth_code = None
    server.auth_error = None
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

def get_auth_url(code_challenge):
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
        "show_dialog": "true",
    }
    return f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}"

def exchange_code_for_tokens(code, code_verifier):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code_verifier": code_verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post("https://accounts.spotify.com/api/token", data=data, headers=headers)
    return resp.json()

def main():
    print("=" * 60)
    print("Spotify Refresh Token Generator")
    print("=" * 60)
    
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        print("\nERROR: Edit this file and set CLIENT_ID and CLIENT_SECRET")
        print("Get them from: https://developer.spotify.com/dashboard")
        return
    
    # Generate PKCE
    code_verifier, code_challenge = generate_pkce()
    
    # Start local server
    server = start_callback_server()
    print(f"\nCallback server running on http://localhost:8888/callback")
    
    # Open browser
    auth_url = get_auth_url(code_challenge)
    print(f"\nOpening browser for Spotify authorization...")
    print(f"If browser doesn't open, go to:\n{auth_url}")
    webbrowser.open(auth_url)
    
    # Wait for callback
    print("Waiting for authorization... (check browser)")
    import time
    for _ in range(120):  # 60 second timeout
        time.sleep(0.5)
        if server.auth_code:
            break
        if server.auth_error:
            print(f"\nAuthorization error: {server.auth_error}")
            return
    else:
        print("\nTimeout waiting for authorization")
        return
    
    server.shutdown()
    
    # Exchange code for tokens
    print("\nExchanging code for tokens...")
    tokens = exchange_code_for_tokens(server.auth_code, code_verifier)
    
    if "refresh_token" in tokens:
        print("\n" + "=" * 60)
        print("SUCCESS! Your refresh token:")
        print("=" * 60)
        print(tokens["refresh_token"])
        print("=" * 60)
        print("\nCopy this token into your Pico's config.py:")
        print(f'SPOTIFY_REFRESH_TOKEN = "{tokens["refresh_token"]}"')
        print(f'SPOTIFY_CLIENT_ID = "{CLIENT_ID}"')
        
        # Save to file for reference
        with open("spotify_tokens.json", "w") as f:
            json.dump(tokens, f, indent=2)
        print("\nFull token response saved to spotify_tokens.json")
    else:
        print(f"\nError: {tokens}")
        print("Full response:", json.dumps(tokens, indent=2))

if __name__ == "__main__":
    main()