# lfd2-bot
A tool to help form lobbies for Left 4 Dead 2 within Discord channels

# Requirements
- Python ^3.8

# Environment setup
## Windows
- Open a command prompt and navigate to this project's root directory. 
- Run `python -m venv venv` to recreate this repo's virtual environment.
- Run `.\venv\Scripts\activate.bat` to activate the env.
- Run `pip install -r requirements.txt` to install this project's dependencies.
## *nix/macOS
- Open a terminal and navigate to this project's root directory.
- Run `python -m venv env` to recreate this repo's virtual environment.
- Run `source ./env/bin/activate` to activate the env.
- Run `pip install -r requirements.txt` to install this project's dependencies.


# Manual testing
1. Configure a test Discord bot using this tutorial https://discordpy.readthedocs.io/en/latest/discord.html

**Step 3 Details**
- Ensure you use a name unique to your user
- Create a copy of example.config.json as config.json and populate it with the key you get from the tutorial
- Send a discord admin your bot invite URL

4. Run the bot `DISCORD_TOKEN="<your secret token>" python bot.py `
5. (optional) Change the command prefix in `bot.py`, e.g. from `?` to `!` 

# Useful Debug Commands

**Note: It's highly recommended to add a unique identifier in `bot.py` to avoid killing/reloading anyone else's bot**

`reload` - will reload the lobby cog without having to restart the bot. This is incredibly useful but will clear any variables within that cog

`disconnect` - kills the bot 



