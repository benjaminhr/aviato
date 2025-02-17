import asyncio
import discord

from discord.ext import commands
from .youtube_downloader import YTDLSource
from .spotify_helper import *
from .queue_manager import *

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

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
            queue_manager.add_to_queue(url)
            await ctx.send("🟡 Added to queue")
        return

    # If URL is empty, try to get next song from queue
    if not url:
        if not queue_manager.track_queue:
            await ctx.send("🔴 The queue is empty.")
            return
        url = queue_manager.get_next_track()

    search_term = None
    if "open.spotify.com/track/" in url:
        track_name = get_spotify_track_name(url)
        search_term = track_name + " audio"
    elif "open.spotify.com/album/" in url:
        track_urls = get_spotify_album_tracks(url)
        first_track_url = track_urls.pop(0)
        track_name = get_spotify_track_name(first_track_url)
        search_term = track_name + " audio"
        # Queue the rest of the album
        for track_url in track_urls:
            queue_manager.add_to_queue(track_url) 
    elif "open.spotify.com/playlist/" in url:
        track_urls = get_spotify_playlist_tracks(url)
        first_track_url = track_urls.pop(0)
        track_name = get_spotify_track_name(first_track_url)
        search_term = track_name + " audio"
        for track_url in track_urls:
            queue_manager.add_to_queue(track_url)
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
        if len(queue_manager.track_queue) > 0:
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

    queue_manager.add_to_front_of_queue(url)
    await ctx.send("🟢 Added to front of queue")


@bot.command(name="queue", help="Print the current queue")
async def queue(ctx):
    if len(queue_manager.track_queue) == 0:
        await ctx.send("🟡 Empty queue")
        return

    async with ctx.typing():
        output_str = ""
        for index, track in enumerate(queue_manager.track_queue):
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
    if len(queue_manager.track_queue) == 0:
        await ctx.send("🟡 Queue is empty")
        return
    queue_manager.shuffle_queue()
    await ctx.send("🟢 Shuffled queue")


@bot.command(name="clear", help="Clear the current track queue")
async def clear(ctx):
    queue_manager.clear_queue()
    await ctx.send("🟡 Queue emptied")


@bot.command(name="next", help="Play next track in the queue")
async def next(ctx):
    while ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    if len(queue_manager.track_queue) == 0:
        await ctx.send("🟡 Queue is empty")
        return
    await play(ctx, "")


@bot.command(name="skip", help="Skip current track")
async def skip(ctx):
    while ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    if len(queue_manager.track_queue) == 0:
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
    queue_manager.clear_queue()
    await ctx.send("🟡 Leaving voice channel")
    await ctx.voice_client.disconnect()
