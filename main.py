import discord, os
from discord.ext import commands
from dotenv import load_dotenv

from autopost import auto_post_updates
import commands as slash_commands

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    GUILD_ID = int(os.getenv("GUILD_ID"))
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)

    if not auto_post_updates.is_running():
        auto_post_updates.start(bot)

    print(f"Logged in as {bot.user}")

slash_commands.setup(bot)
bot.run(os.getenv("DISCORD_TOKEN"))
