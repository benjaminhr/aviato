import os
import random
import sys
import discord
import asyncio
import traceback
import yt_dlp as youtube_dl
import spotipy
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables
load_dotenv()
discord_token = (
    os.getenv("DISCORD_TOKEN_DEV")
    if os.getenv("MODE") == "DEV"
    else os.getenv("DISCORD_TOKEN")
)
spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Check for missing environment variables
if discord_token is None:
    print("Error: DISCORD_TOKEN or DISCORD_TOKEN_DEV is not set.")
    sys.exit(1)
if spotify_client_id is None:
    print("Error: SPOTIFY_CLIENT_ID is not set.")
    sys.exit(1)
if spotify_client_secret is None:
    print("Error: SPOTIFY_CLIENT_SECRET is not set.")
    sys.exit(1)

# Setup Spotify API
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=spotify_client_id, client_secret=spotify_client_secret
    )
)

# Setup Discord Bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# youtube-dl video stream options
ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

ffmpeg_options = {
    "options": '-vn -filter:a "volume=0.25"',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
}


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        if "entries" in data:
            # Take first item from a playlist
            data = data["entries"][0]
        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


def get_spotify_track_name(url: str) -> str:
    track_id = url.split("/")[-1].split("?")[0]
    track_info = sp.track(track_id)
    track_name = track_info["artists"][0]["name"] + " " + track_info["name"]
    return track_name


def get_spotify_album_tracks(url: str):
    tracks = sp.album_tracks(url)
    track_urls = [
        "https://open.spotify.com/track/" + track["id"] for track in tracks["items"]
    ]
    return track_urls


def get_spotify_playlist_tracks(url: str):
    playlist_id = url.split("/")[-1].split("?")[0]
    results = sp.playlist_tracks(playlist_id)
    track_urls = [
        "https://open.spotify.com/track/" + item["track"]["id"]
        for item in results["items"]
        if item["track"]
    ]
    return track_urls


# Track queue to play, spotify urls
track_queue = []

last_interaction_time = datetime.now(timezone.utc)
leave_after_minutes = 30


# checks if channel is empty, then leaves
async def check_inactivity():
    while True:
        await asyncio.sleep(60)  # Check every minute
        if not bot.voice_clients:
            continue
        current_time = datetime.now(timezone.utc)
        for voice_client in bot.voice_clients:
            if voice_client.is_connected():
                if (current_time - last_interaction_time) > timedelta(
                    minutes=leave_after_minutes
                ):
                    if (
                        not voice_client.channel.members
                        or len(voice_client.channel.members) == 1
                    ):  # Only bot itself
                        await voice_client.disconnect()
                        track_queue.clear()


@bot.event
async def on_command(_):
    global last_interaction_time
    last_interaction_time = datetime.now(timezone.utc)


@bot.event
async def on_ready():
    bot.loop.create_task(check_inactivity())


# Command to play music
@bot.command(name="play", help="Plays music from a Spotify or Youtube URL")
async def play(ctx, url: str):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if not voice_client:
        connected = await join(ctx)
        if connected:
            await play(ctx, url)
        return

    if voice_client.is_playing():
        if url:
            track_queue.append(url)
            await ctx.send("🟡 Added to queue")
        return

    # If URL is empty, try to get next song from queue
    if not url:
        if not track_queue:
            await ctx.send("🔴 The queue is empty.")
            return
        url = track_queue.pop(0)

    search_term = None
    if "open.spotify.com/track/" in url:
        track_name = get_spotify_track_name(url)
        search_term = track_name + " audio"
    elif "open.spotify.com/album/" in url:
        track_urls = get_spotify_album_tracks(url)
        first_track_url = track_urls.pop(0)
        track_name = get_spotify_track_name(first_track_url)
        search_term = track_name + " audio"
        track_queue.extend(track_urls)  # Queue the rest of the album
    elif "open.spotify.com/playlist/" in url:
        track_urls = get_spotify_playlist_tracks(url)
        first_track_url = track_urls.pop(0)
        track_name = get_spotify_track_name(first_track_url)
        search_term = track_name + " audio"
        track_queue.extend(track_urls)
    elif "youtu.be" in url:
        # fixes shortened links e.g. https://youtu.be/TZeK5-_YNxY
        video_id = url.split("/")[-1]
        search_term = "https://www.youtube.com/watch?v=" + video_id
    elif "youtube.com" in url:
        search_term = url
    elif "soundcloud.com" in url:
        search_term = url
    else:
        await ctx.send("🔴 Invalid URL")
        return

    # Once video has finished, this gets called to play next track
    def play_next_track(error):
        if error:
            print(f"Player error: {error}")
        if len(track_queue) > 0:
            coroutine = play(ctx, "")
            asyncio.run_coroutine_threadsafe(coroutine, bot.loop)

    if not voice_client.is_playing():
        # Search and play the song on YouTube
        async with ctx.typing():
            ctx.voice_client.stop()
            player = await YTDLSource.from_url(search_term, loop=bot.loop, stream=True)
            ctx.voice_client.play(player, after=play_next_track)
        await ctx.send(f"🟢 Now playing: {player.title}")


@bot.command(name="playnext", help="Add track to next in queue")
async def playnext(ctx, url: str):
    if not url:
        return

    track_queue.insert(0, url)
    await ctx.send("🟢 Added to front of queue")


@bot.command(name="queue", help="Print the current queue")
async def queue(ctx):
    if len(track_queue) == 0:
        await ctx.send("🟡 Empty queue")
        return

    async with ctx.typing():
        output_str = ""
        for index, track in enumerate(track_queue):
            if "open.spotify.com/track/" in track:
                track = get_spotify_track_name(track)
            output_str += f"({index + 1}) {track}\n"

        # 2000 char message limit, if queue is long then split into chunks
        chunks = [output_str[i : i + 1900] for i in range(0, len(output_str), 1900)]

        await ctx.send(f"Current queue is: \n")
        for chunk in chunks:
            await ctx.send(chunk)


@bot.command(name="shuffle", help="Shuffles song queue")
async def shuffle(ctx):
    global track_queue
    if len(track_queue) == 0:
        await ctx.send("🟡 Queue is empty")
        return
    random.shuffle(track_queue)
    await ctx.send("🟢 Shuffled queue")


@bot.command(name="clear", help="Clear the current track queue")
async def clear(ctx):
    track_queue.clear()
    await ctx.send("🟡 Queue emptied")


@bot.command(name="next", help="Play next track in the queue")
async def next(ctx):
    while ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    if len(track_queue) == 0:
        await ctx.send("🟡 Queue is empty")
        return
    await play(ctx, "")


@bot.command(name="skip", help="Skip current track")
async def skip(ctx):
    while ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    if len(track_queue) == 0:
        await ctx.send("🟡 Queue is empty")
        return
    await play(ctx, "")


@bot.command(name="stop", help="Stops playing audio")
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("🔴 Audio stopped")
    else:
        await ctx.send("🟡 No audio is currently playing")


@bot.command(name="join", help="Joins a voice channel")
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("🔴 You are not connected to a voice channel.")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None or ctx.voice_client.channel != channel:
        await channel.connect()
        await ctx.send("🟢 Joined voice channel")
        return True


@bot.command(name="leave", help="Clears the queue and leaves the voice channel")
async def leave(ctx):
    track_queue.clear()
    await ctx.send("🟡 Leaving voice channel")
    await ctx.voice_client.disconnect()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("🔴 There was an error. See server logs.")
        traceback.print_exception(type(error), error, error.__traceback__)
    print(error)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        if (
            isinstance(error.original, discord.errors.ClientException)
            and str(error.original) == "Already playing audio."
        ):
            return
        await ctx.send("🔴 There was an error. See server logs.")
        traceback.print_exception(type(error), error, error.__traceback__)
    else:
        print(error)


bot.run(discord_token)
