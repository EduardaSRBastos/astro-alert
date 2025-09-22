import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from skyfield.api import load, Topos
from skyfield import almanac, eclipselib
import requests
import numpy as np
import os
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

# --- Discord bot setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Global Skyfield setup with error handling ---
try:
    ts = load.timescale()
    eph = load("de421.bsp")  # planetary data file
    earth, sun, moon = eph["earth"], eph["sun"], eph["moon"]
except Exception as e:
    print(f"[ERROR] Failed to load ephemeris data: {e}")
    ts = None
    eph = None
    earth = sun = moon = None

AU_KM = 149597870
SUN_RADIUS_KM = 696340
MOON_RADIUS_KM = 1737

# --- Function to get location ---
def get_location():
    lat = lon = 0
    loc = "Unknown"
    offset_str = "+0000"
    try:
        ip_data = requests.get("https://ipapi.co/json/").json()
        region = ip_data.get("region", "Unknown")
        loc = region
        lat = ip_data.get("latitude", 0)
        lon = ip_data.get("longitude", 0)
        offset_str = ip_data.get("utc_offset", "+0000")
    except Exception as e:
        print(f"[WARN] Could not fetch location: {e}")
    offset = timedelta(hours=int(offset_str[1:3]), minutes=int(offset_str[3:]))
    if offset_str[0] == "-":
        offset = -offset
    return lat, lon, loc, offset

# --- Astronomy calculation functions with daily cache refresh ---
@lru_cache(maxsize=32)
def get_next_moon_phase(today: datetime.date = datetime.today().date()):
    phase_function = almanac.moon_phases(eph)
    mt0 = ts.utc(today.year, today.month, today.day)
    mt1 = ts.utc(today.year, today.month, today.day + 30)
    times, phases = almanac.find_discrete(mt0, mt1, phase_function)
    phase_names = {0: "New Moon", 1: "First Quarter", 2: "Full Moon", 3: "Last Quarter"}
    return phase_names[phases[0]], times[0].utc_datetime()

@lru_cache(maxsize=32)
def get_next_full_moon(today: datetime.date = datetime.today().date()):
    phase_function = almanac.moon_phases(eph)
    mt0 = ts.utc(today.year, today.month, today.day)
    mt1 = ts.utc(today.year, today.month, today.day + 30)
    times, phases = almanac.find_discrete(mt0, mt1, phase_function)
    for t, p in zip(times, phases):
        if p == 2:
            return t.utc_datetime()
    return None

@lru_cache(maxsize=32)
def get_upcoming_moon_phases(today: datetime.date = datetime.today().date()):
    phase_function = almanac.moon_phases(eph)
    mt0 = ts.utc(today.year, today.month, today.day)
    mt1 = ts.utc(today.year, today.month, today.day + 30)
    times, phases = almanac.find_discrete(mt0, mt1, phase_function)
    phase_names = {0: "New Moon", 1: "First Quarter", 2: "Full Moon", 3: "Last Quarter"}
    return [(phase_names[p], t.utc_datetime()) for t, p in zip(times, phases)]

@lru_cache(maxsize=32)
def get_next_eclipses(lat=0, lon=0, today: datetime.date = datetime.today().date()):
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)

    # Lunar eclipse
    et0 = ts.utc(today.year, today.month, today.day)
    et1 = ts.utc(today.year + 5, 12, 31)
    t_lunar, y_lunar, _ = eclipselib.lunar_eclipses(et0, et1, eph)
    next_lunar_time, lunar_type = None, None
    for t_ecl, idx in zip(t_lunar, y_lunar):
        alt, az, dist = observer.at(t_ecl).observe(moon).apparent().altaz()
        if alt.degrees <= 0:
            continue
        next_lunar_time = t_ecl.utc_datetime()
        lunar_type = eclipselib.LUNAR_ECLIPSES[idx]
        break

    # Solar eclipse
    total_minutes = int((et1.utc_datetime() - et0.utc_datetime()).total_seconds() / 60)
    times_sun = ts.utc(today.year, today.month, today.day, 0, np.arange(0, total_minutes, 10))
    sun_app = observer.at(times_sun).observe(sun).apparent()
    moon_app = observer.at(times_sun).observe(moon).apparent()
    separation = sun_app.separation_from(moon_app).degrees
    sun_radius = np.degrees(np.arcsin(SUN_RADIUS_KM / (sun_app.distance().au * AU_KM)))
    moon_radius = np.degrees(np.arcsin(MOON_RADIUS_KM / (moon_app.distance().au * AU_KM)))
    indices = np.where(separation < (sun_radius + moon_radius))[0]

    solar_type, next_solar_time = None, None
    if indices.size > 0:
        t_next = times_sun[indices[0]].utc_datetime()
        sep = separation[indices[0]]
        sr, mr = sun_radius[indices[0]], moon_radius[indices[0]]
        if mr >= sr and sep < sr:
            solar_type = "Total"
        elif mr < sr and sep < sr:
            solar_type = "Annular"
        else:
            solar_type = "Partial"
        next_solar_time = t_next

    return (solar_type, next_solar_time), (lunar_type, next_lunar_time)

# --- Slash Commands with embeds ---
@bot.tree.command(name="nextmoonphase", description="Shows the next moon phase.")
async def next_moon_phase_cmd(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        phase, when = get_next_moon_phase()
        embed = discord.Embed(
            title="🌙 Next Moon Phase",
            color=discord.Color.blurple()
        )
        embed.add_field(name=f"**🌗 Phase:** {phase}", value=f"\n\n🗓️ **When:** {when:%d/%m/%Y}", inline=False)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")

@bot.tree.command(name="nextfullmoon", description="Shows the next full moon.")
async def next_full_moon_cmd(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        when = get_next_full_moon()
        embed = discord.Embed(
            title="🌕 Next Full Moon",
            description=f"🗓️ **When:** {when:%d/%m/%Y}" if when else "Not found",
            color=discord.Color.gold()
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")

@bot.tree.command(name="upcomingmoonphases", description="Shows upcoming moon phases.")
async def upcoming_moon_phases_cmd(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        phases = get_upcoming_moon_phases()
        embed = discord.Embed(
            title="📅 Upcoming Moon Phases",
            color=discord.Color.purple()
        )
        for phase, when in phases:
            embed.add_field(name=f"**🌗 Phase:** {phase}", value=f"\n\n🗓️ **When:** {when:%d/%m/%Y}", inline=False)
            embed.add_field(name=" ", value=" ", inline=False) 
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")

@bot.tree.command(name="nexteclipses", description="Shows next solar and lunar eclipses.")
async def next_eclipses_cmd(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        lat, lon, loc, offset = get_location()
        (solar_type, solar_time), (lunar_type, lunar_time) = get_next_eclipses(lat, lon)

        embed = discord.Embed(
            title="☀️🌙 Next Eclipses",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"\n📍 Location: {loc}")

        embed.add_field(name="Solar Eclipse", value="", inline=False)
        if solar_time:
            solar_time_local = solar_time + offset
            embed.add_field(name=f"🌖 **Type:** {solar_type}", value=f"🗓️ **When:** {solar_time_local:%d/%m/%Y - %H:%M}", inline=False)
        else:
            embed.add_field(name="🌖 Solar Eclipse", value="No solar eclipse found", inline=False)

        embed.add_field(name=" ", value=" ", inline=False) 
        
        embed.add_field(name="Lunar Eclipse", value="", inline=False)
        if lunar_time:
            lunar_time_local = lunar_time + offset
            embed.add_field(name=f"🌒 **Type:** {lunar_type}", value=f"🗓️ **When:** {lunar_time_local:%d/%m/%Y - %H:%M}", inline=False)
        else:
            embed.add_field(name="🌒 Lunar Eclipse", value="No lunar eclipse found", inline=False)

        embed.add_field(name=" ", value=" ", inline=False) 

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


# --- Command: Clear messages ---
@bot.tree.command(name="clear", description="Delete messages in this channel.")
@app_commands.describe(amount="Number of messages to delete (max 100)")
async def clear_slash(interaction: discord.Interaction, amount: int = 100):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission.", ephemeral=True)
        return
    if not interaction.guild.me.guild_permissions.manage_messages:
        await interaction.response.send_message("I don't have permission to delete messages!", ephemeral=True)
        return
    await interaction.response.send_message(f"Deleting up to {amount} messages...", ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount, check=lambda m: True)
    await interaction.edit_original_response(content=f"Deleted {len(deleted)} messages.")

# --- Sync commands ---
@bot.event
async def on_ready():
    try:
        GUILD_ID = int(os.getenv("GUILD_ID"))
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"Logged in as {bot.user} and synced commands to guild {GUILD_ID}")
    except Exception as e:
        print(f"[ERROR] Could not sync commands: {e}")

# --- Run bot ---
bot.run(os.getenv("DISCORD_TOKEN"))
