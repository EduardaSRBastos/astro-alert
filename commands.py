import discord
from discord import app_commands
from astronomy import (
    get_next_moon_phase,
    get_next_full_moon,
    get_upcoming_moon_phases,
    get_next_eclipses,
    get_next_meteor_shower,
    calculate_meteor_visibility,
)
from location import get_location, get_hemisphere, get_moon_illumination

def setup(bot: discord.Client):

    @bot.tree.command(name="nextmoonphase", description="Shows the next moon phase.")
    async def next_moon_phase_cmd(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            phase, when = get_next_moon_phase()
            embed = discord.Embed(
                title="🌙 Next Moon Phase",
                color=discord.Color.blurple()
            )
            embed.add_field(
                name=f"**🌗 Phase:** {phase}",
                value=f"\n\n🗓️ **When:** {when:%d/%m/%Y}",
                inline=False
            )
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
                embed.add_field(
                    name=f"**🌗 Phase:** {phase}",
                    value=f"\n\n🗓️ **When:** {when:%d/%m/%Y}",
                    inline=False
                )
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
                embed.add_field(
                    name=f"🌖 **Type:** {solar_type}",
                    value=f"🗓️ **When:** {solar_time_local:%d/%m/%Y - %H:%M}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🌖 Solar Eclipse",
                    value="No solar eclipse found",
                    inline=False
                )

            embed.add_field(name=" ", value=" ", inline=False)

            embed.add_field(name="Lunar Eclipse", value="", inline=False)
            if lunar_time:
                lunar_time_local = lunar_time + offset
                embed.add_field(
                    name=f"🌒 **Type:** {lunar_type}",
                    value=f"🗓️ **When:** {lunar_time_local:%d/%m/%Y - %H:%M}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🌒 Lunar Eclipse",
                    value="No lunar eclipse found",
                    inline=False
                )

            embed.add_field(name=" ", value=" ", inline=False)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Error: {e}")

    @bot.tree.command(name="nextmeteors", description="Shows the next meteor shower peak.")
    async def next_meteors_cmd(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            lat, lon, loc, offset = get_location()
            shower, start_date, end_date, peak_time = get_next_meteor_shower()
            moon_illum = get_moon_illumination(peak_time)
            hemisphere = get_hemisphere(lat)
            visibility = calculate_meteor_visibility(shower, hemisphere, moon_illum)

            if not shower:
                await interaction.followup.send("No upcoming meteor showers found.")
                return

            embed = discord.Embed(
                title=f"🌠 Next Meteor Shower: {shower['name']}",
                color=discord.Color.teal()
            )

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
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Error: {e}")

    @bot.tree.command(name="clear", description="Delete messages in this channel.")
    @app_commands.describe(amount="Number of messages to delete (max 100)")
    async def clear_slash(interaction: discord.Interaction, amount: int = 100):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You don't have permission.", ephemeral=True)
            return
        if not interaction.guild.me.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "I don't have permission to delete messages!",
                ephemeral=True
            )
            return

        amount = min(amount, 100)
        await interaction.response.send_message(
            f"Deleting up to {amount} messages...",
            ephemeral=True
        )

        deleted = await interaction.channel.purge(
            limit=amount,
            check=lambda m: not m.pinned
        )

        await interaction.edit_original_response(
            content=f"Deleted {len(deleted)} messages."
        )
