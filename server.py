import os
import discord

# import youtube_dl
import yt_dlp as youtube_dl
import spotipy
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=spotify_client_id, client_secret=spotify_client_secret
    )
)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

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

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


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
@bot.command(name="play", help="Plays music from a Spotify URL")
async def play(ctx, url: str):
    search_term = None
    if "open.spotify.com" in url:
        track_id = url.split("/")[-1].split("?")[0]
        track_info = sp.track(track_id)
        track_name = track_info["name"] + " " + track_info["artists"][0]["name"]
        search_term = track_name + " audio"
    elif "youtube.com" in url:
        search_term = url

    print(search_term)

    # Search and play the song on YouTube
    async with ctx.typing():
        player = await YTDLSource.from_url(search_term, loop=bot.loop, stream=True)
        ctx.voice_client.play(
            player, after=lambda e: print("Player error: %s" % e) if e else None
        )

    await ctx.send(f"Now playing: {player.title}")


@bot.command(name="join", help="Joins a voice channel")
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None or ctx.voice_client.channel != channel:
        await channel.connect()


@bot.command(name="leave", help="Clears the queue and leaves the voice channel")
async def leave(ctx):
    await ctx.voice_client.disconnect()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("There was an error executing the command.")
        print(error)


bot.run(discord_token)
