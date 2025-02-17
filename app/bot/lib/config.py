import os
import sys
import spotipy

from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()
discord_token = (
    os.getenv("DISCORD_TOKEN_DEV")
    if os.getenv("MODE") == "dev"
    else os.getenv("DISCORD_TOKEN")
)
spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

if discord_token is None:
    print("Error: DISCORD_TOKEN or DISCORD_TOKEN_DEV is not set.")
    sys.exit(1)
if spotify_client_id is None:
    print("Error: SPOTIFY_CLIENT_ID is not set.")
    sys.exit(1)
if spotify_client_secret is None:
    print("Error: SPOTIFY_CLIENT_SECRET is not set.")
    sys.exit(1)

spotify_client = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=spotify_client_id, client_secret=spotify_client_secret
    )
)
