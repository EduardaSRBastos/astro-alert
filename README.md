<div align="center">
  
# Astro Alert
[![GitHub License](https://img.shields.io/github/license/EduardaSRBastos/astro-alert?style=plastic&color=darkred)](https://github.com/EduardaSRBastos/astro-alert?tab=MIT-1-ov-file)
[![GitHub branch check runs](https://img.shields.io/github/check-runs/EduardaSRBastos/astro-alert/main?style=plastic)](https://github.com/EduardaSRBastos/astro-alert/actions)
[![GitHub repo size](https://img.shields.io/github/repo-size/EduardaSRBastos/astro-alert?style=plastic)](https://github.com/EduardaSRBastos/astro-alert)
[![Post Astro Alerts](https://github.com/EduardaSRBastos/astro-alert/actions/workflows/astro-alerts.yml/badge.svg)](https://github.com/EduardaSRBastos/astro-alert/actions/workflows/astro-alerts.yml)

<p><i>A Discord bot that posts real-time moon phases, eclipses, and astronomy alerts, and lets users explore upcoming celestial events.</i></p>

 </div>

<br>

## Table of Contents
- [Features](#features)
- [How to Use](#how-to-use)
- [Contributing](#contributing)
- [License](#license)

<br>

## Features

* **Automatic Astronomical Updates**: Posts daily updates about moon phases, full moons, and upcoming eclipses directly to your Discord channel.
* **Event Alerts**: Sends smart alerts when a celestial event (like a full moon or eclipse) is 12 hours or 2 hours away.
* **Eclipse Tracking**: Calculates upcoming solar and lunar eclipses based on your configured or detected location.
* **Slash Commands**: Includes `/nextmoonphase`, `/nextfullmoon`, `/upcomingmoonphases`, and `/nexteclipses` for quick event info.
* **Location-Aware Data**: Automatically detects your location or uses a custom one from environment variables.
* **Channel Cleanup**: Provides a `/clear` command to delete recent messages (excluding pinned ones).
* **Persistent Event Storage**: Keeps track of previously posted events in `dates.json` to avoid duplicates.
* **Automated Scheduling**: Runs automatically via GitHub Actions, staying active for scheduled time periods each day.

<br>

## How to Use

1. **Clone the Repository**

   ```bash
   git clone https://github.com/EduardaSRBastos/astro-alert.git
   cd astro-alert
   ```

2. **Set Up Environment Variables**
   Create a `.env` file in the project root with the following:

   ```env
   DISCORD_TOKEN=your_discord_bot_token
   CHANNEL_ID=your_discord_channel_id
   GUILD_ID=your_discord_server_id
   MY_LOCATION={"latitude":0,"longitude":0,"region":"YourRegion","utc_offset":"+0000"}
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Bot Locally (Optional)**

   ```bash
   python main.py
   ```

5. **Automate with GitHub Actions**
   The bot runs automatically every 12 hours for 5 minutes (configurable).
   Edit `.github/workflows/astro-alerts.yml` to adjust the schedule or runtime.

<br>

## Contributing
- Support this project by giving it a star ⭐. Thanks!
- Feel free to suggest improvements or report any issues in the repository.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
