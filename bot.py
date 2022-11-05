import discord
from discord.ext import commands
from music import Music
from help import Help

allIntents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=allIntents)
bot.remove_command("help")

@bot.event
async def on_ready():

    await bot.add_cog(Music(bot))
    await bot.add_cog(Help(bot))
    await bot.change_presence(activity=discord.Activity(name='music', type=2))
    print(f"Logged in as {bot.user}")

bot.run("ODgyMjAyMDg5NDUzOTQwODA3.G3bdzI.iYgj2A6kKPqKRXu_4UxHvnQ9-Agfh5AuVPvi6w")
