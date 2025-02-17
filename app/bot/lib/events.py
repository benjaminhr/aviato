import asyncio
import traceback
import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from .queue_manager import track_queue
from .commands import bot

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
