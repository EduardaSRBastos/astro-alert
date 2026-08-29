import discord
import os
import json
from datetime import datetime, UTC
from discord.ext import tasks
from astronomy import (
    get_next_moon_phase,
    get_next_full_moon,
    get_upcoming_moon_phases,
    get_next_eclipses,
    get_next_meteor_shower,
    calculate_meteor_visibility,
)
from location import get_location, get_hemisphere, get_moon_illumination


DATES_FILE = "dates.json"


def load_last_events():
    if not os.path.exists(DATES_FILE):
        return {
            "last_full_moon": None,
            "last_moon_phase": None,
            "last_solar_eclipse": None,
            "last_lunar_eclipse": None,
            "last_upcoming_phases": [],
            "meteor_alert_12h": None,
            "meteor_alert_2h": None
        }
    with open(DATES_FILE, "r") as f:
        return json.load(f)


def save_last_events(data):
    tmp_file = f"{DATES_FILE}.tmp"
    with open(tmp_file, "w") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp_file, DATES_FILE)


@tasks.loop(hours=24)
async def auto_post_updates(bot):
    last_events = load_last_events()

    await bot.wait_until_ready()

    channel = bot.get_channel(int(os.getenv("CHANNEL_ID")))
    if channel is None:
        print("[WARN] Channel not found, check CHANNEL_ID")
        return

    lat, lon, loc, offset = get_location()
    hemisphere = get_hemisphere(lat)

    # --- Next Moon Phase ---
    phase, when = get_next_moon_phase()

    if last_events.get("last_moon_phase") != f"{phase}_{when.date().isoformat()}":
        last_events["last_moon_phase"] = f"{phase}_{when.date().isoformat()}"

        embed = discord.Embed(
            title="🌙 Next Moon Phase",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name=f"**🌗 Phase:** {phase}",
            value=f"\n\n🗓️ **When:** {when:%d/%m/%Y}",
            inline=False
        )
        await channel.send(embed=embed)

    # --- Next Full Moon ---
    full_moon = get_next_full_moon()

    if full_moon and last_events.get("last_full_moon") != full_moon.date().isoformat():
        last_events["last_full_moon"] = full_moon.date().isoformat()

        embed = discord.Embed(
            title="🌕 Next Full Moon",
            description=f"🗓️ **When:** {full_moon:%d/%m/%Y}",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)

    # --- Upcoming Moon Phases ---
    now = datetime.now(UTC)
    phases = get_upcoming_moon_phases()
    future_phases = [(p, w) for p, w in phases if w > now]
    upcoming_phase_dates = [w.date().isoformat() for _, w in future_phases]

    if upcoming_phase_dates != last_events.get("last_upcoming_phases", []):
        last_events["last_upcoming_phases"] = upcoming_phase_dates

        embed = discord.Embed(
            title="📅 Upcoming Moon Phases",
            color=discord.Color.purple()
        )
        for phase, when in phases:
            embed.add_field(
                name=f"**🌗 Phase:** {phase}",
                value=f"\n\n🗓️ **When:** {when:%d/%m/%Y}",
                inline=False
            )
            embed.add_field(name=" ", value=" ", inline=False)
        await channel.send(embed=embed)

    # --- Next Eclipses ---
    (solar_type, solar_time), (lunar_type, lunar_time) = get_next_eclipses(lat, lon)

    def eclipse_alert(key, event_time):
        if not event_time:
            return False
        hours_away = (event_time - datetime.now(UTC)).total_seconds() / 3600
        event_id = event_time.date().isoformat()
        already_alerted = last_events.get(key) == event_id

        if hours_away <= 24 and not already_alerted:
            last_events[key] = event_id
            return True
        return False

    solar_due = eclipse_alert("last_solar_eclipse", solar_time)
    lunar_due = eclipse_alert("last_lunar_eclipse", lunar_time)

    if solar_due or lunar_due:
        embed = discord.Embed(
            title="☀️🌙 Next Eclipse",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"📍 Location: {loc}")

        if solar_due:
            solar_time_local = solar_time + offset
            embed.add_field(
                name=f"☀️ **Solar Eclipse ({solar_type})**",
                value=f"🗓️ **When:** {solar_time_local:%d/%m/%Y - %H:%M}",
                inline=False
            )

        if lunar_due:
            lunar_time_local = lunar_time + offset
            embed.add_field(
                name=f"🌙 **Lunar Eclipse ({lunar_type})**",
                value=f"🗓️ **When:** {lunar_time_local:%d/%m/%Y - %H:%M}",
                inline=False
            )

        await channel.send(embed=embed)

        # --- Meteor Shower Alerts ---
    shower, start_date, end_date, peak_time = get_next_meteor_shower()

    if shower and peak_time:
        moon_illum = get_moon_illumination(peak_time)
        visibility = calculate_meteor_visibility(shower, hemisphere, moon_illum)

        event_id = peak_time.date().isoformat()
        hours_away = (peak_time - datetime.now(UTC)).total_seconds() / 3600

        def meteor_stage_due(key, threshold):
            already_alerted = last_events.get(key) == event_id
            if hours_away <= threshold and not already_alerted:
                last_events[key] = event_id
                return True
            return False

        alert_2h = meteor_stage_due("meteor_alert_2h", 2)
        alert_12h = None
        if not alert_2h:
            alert_12h = meteor_stage_due("meteor_alert_12h", 12)

        alert_label = "2h" if alert_2h else ("12h" if alert_12h else None)

        if alert_2h:
            last_events["meteor_alert_12h"] = event_id

        if alert_label:
            embed = discord.Embed(
                title="🌠 Meteor Shower Alert",
                color=discord.Color.teal()
            )
            embed.description = f"⏰ **{shower['name']} peaks in less than {alert_label}**"

            embed.add_field(
                name="📊 Visibility Conditions",
                value=(
                    f"🌍 **Hemisphere:** {hemisphere}\n"
                    f"🌕 **Moon illumination:** {moon_illum}%\n"
                    f"👁️ **Estimated visibility:** {visibility}%\n"
                    f"☄️ **ZHR:** {shower['zhr']} meteors/hour"
                ),
                inline=False
            )

            embed.add_field(
                name="🗓️ Dates",
                value=(
                    f"📅 Start: {start_date + offset:%d/%m/%Y}\n"
                    f"📅 Peak: {peak_time + offset:%d/%m/%Y}\n"
                    f"📅 End: {end_date + offset:%d/%m/%Y}\n"
                    f"⏰ Best time: {shower['best_time']}"
                ),
                inline=False
            )

            embed.set_footer(text=f"📍 Location: {loc}")
            await channel.send(embed=embed)

    save_last_events(last_events)
