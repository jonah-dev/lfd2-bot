# lfd2-bot
A tool to help form lobbies for Left 4 Dead 2 within a Discord channel

# Requirements
## Python Modules
- numpy
- discord
- pillow

Eventually I'll get a setup.py configured for all dependencies

# Getting Started

1. Clone the repository to your local machine
2. Install the required Python modules
3. Configure a test Discord bot using this tutorial https://discordpy.readthedocs.io/en/latest/discord.html

**Step 3 Details**
- Ensure you use a name unique to your user
- Create a copy of example.config.json as config.json and populate it with the key you get from the tutorial
- Send a discord admin your bot invite URL

4. Run the bot `python bot.py`
5. Edit the command prefix in `bot.py` in the case that an existing bot using that command prefix is in the channel you will be testing in.

# Useful Debug Commands

`reload` - will reload the lobby cog without having to restart the bot. This is incredibly useful but will clear any variables within that cog

`disconnect` - kills the bot **note: It's best to add some sort of unique identifier in `bot.py` to make sure not to kill anyone elses bot**



