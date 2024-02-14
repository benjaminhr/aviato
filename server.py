import os
import sys
import discord
import asyncio
import yt_dlp as youtube_dl
import spotipy
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Check for missing environment variables
if discord_token is None:
    print("Error: DISCORD_TOKEN is not set.")
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
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

ffmpeg_options = {"options": "-vn"}

# Track queue to play
track_queue = []


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


# Command to play music
@bot.command(name="play", help="Plays music from a Spotify or Youtube URL")
async def play(ctx, url: str):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        await ctx.send("🔴 Not connected to voice channel, use /join")
        return

    if voice_client.is_playing():
        await ctx.send("🟡 Added to queue")
        track_queue.append(url)
        return

    if len(url) == 0 or url is None:
        # Play next song in queue
        url = track_queue.pop(0)

    # Either collect track name from spotify and search it on youtube
    # or use youtube link directly
    search_term = None
    if "open.spotify.com" in url:
        track_id = url.split("/")[-1].split("?")[0]
        track_info = sp.track(track_id)
        track_name = track_info["name"] + " " + track_info["artists"][0]["name"]
        search_term = track_name + " audio"
    elif "youtube.com" in url:
        search_term = url

    # Once video has finished, this gets called to play next track
    def play_next_track(error):
        if error:
            print(f"Player error: {error}")
        if len(track_queue) > 0:
            coroutine = play(ctx, "")
            asyncio.run_coroutine_threadsafe(coroutine, bot.loop)

    # Search and play the song on YouTube
    async with ctx.typing():
        player = await YTDLSource.from_url(search_term, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=play_next_track)

    await ctx.send(f"🟢 Now playing: {player.title}")


@bot.command(name="queue", help="Print the current queue")
async def queue(ctx):
    if len(track_queue) == 0:
        await ctx.send("🟡 Empty queue")
        return

    output_str = ""
    for index, track in enumerate(track_queue):
        output_str += f"({index + 1}) {track}\n"
    await ctx.send(f"Current queue is: \n{output_str}")


@bot.command(name="clearqueue", help="Clear the current track queue")
async def clearqueue(ctx):
    global track_queue
    track_queue = []
    await ctx.send("🟡 Queue emptied")


@bot.command(name="next", help="Play next track in the queue")
async def next(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    if len(track_queue) == 0:
        await ctx.send("🟡 Queue is empty")
        return
    await play(ctx, "")


@bot.command(name="stop", help="Stops current track from playing")
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("🟡 Stopping track")


@bot.command(name="join", help="Joins a voice channel")
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("🔴 You are not connected to a voice channel.")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None or ctx.voice_client.channel != channel:
        await channel.connect()
        await ctx.send("🟢 Joined voice channel")


@bot.command(name="leave", help="Clears the queue and leaves the voice channel")
async def leave(ctx):
    await ctx.send("🟡 Leaving voice channel")
    await ctx.voice_client.disconnect()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("🔴 There was an error executing the command. See server logs.")
        print(error)


bot.run(discord_token)
