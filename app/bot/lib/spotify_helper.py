from .config import spotify_client

def get_spotify_track_name(url: str) -> str:
    track_id = url.split("/")[-1].split("?")[0]
    track_info = spotify_client.track(track_id)
    track_name = track_info["artists"][0]["name"] + " " + track_info["name"]
    return track_name


def get_spotify_album_tracks(url: str):
    tracks = spotify_client.album_tracks(url)
    track_urls = [
        "https://open.spotify.com/track/" + track["id"] for track in tracks["items"]
    ]
    return track_urls


def get_spotify_playlist_tracks(url: str):
    playlist_id = url.split("/")[-1].split("?")[0]
    results = spotify_client.playlist_tracks(playlist_id)
    track_urls = [
        "https://open.spotify.com/track/" + item["track"]["id"]
        for item in results["items"]
        if item["track"]
    ]
    return track_urls