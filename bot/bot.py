import discord
from discord.ext import commands
from music import Music
from help import Help
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="-", intents=intents)
bot.remove_command("help")

@bot.event
async def on_ready():
    await bot.add_cog(Music(bot))
    await bot.add_cog(Help(bot))
    await bot.change_presence(activity=discord.Activity(name='music', type=2))
    print(f"Logged in as {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    else:
        await ctx.send("An error occurred.")
    print(f"An error occurred: {error}")

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_BOT_TOKEN environment variable not set.")