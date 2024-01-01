import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = """
```
General commands:
-help - displays all the available commands
-join - connects the bot to the author's voice channel
-play <keywords> - finds the song on youtube and plays it in your current channel. Will resume playing the current song
-queue - displays the current music queue
-queueRemaining - displays the remaining music queue
-skip - skips the current song being played
-remove - removes song at index from the queue
-loop - enables/disables single song looping and queue looping
-shuffle - shuffles the queue
-previous - plays the previous song on the queue
-rewind - rewinds the current song
-seek - seeks to the given second of the playing song
-clear - clears the queue
-leave - Disconnects the bot from the voice channel
-pause - pauses the current song being played or resumes if already paused
-resume - resumes playing the current song
```
"""

    @commands.command(name="help", aliases=['h'])
    async def help(self, ctx):
        await ctx.send(self.help_message)
