# Lobby For Discord 2 Bot
But you can call me ***Lobby Bot***.

This bot helps organize players around specific games. We've found this to be very helpful in oversized voice channels where wrangling participants is near impossible. We hope you do too. 

## Usage
All commands start with `?` and the basic ones are detailed by `?help`. The typical experience is first `?join`-ing the lobby and then `?ready`-ing once you are able to play a game. The lobby will separate 'readied' and 'unreadied' players as 'players' and 'alternates'. Once you have enough ready players you'll get a ping to start the game. If your game has teams, you can get match suggestions by calling `?shuffle`.

A channel can have only one lobby active at a time. You can reset the lobby by calling `?clear`. You can repurpose the lobby by calling `?config` with different *directives*. For example, you can change the minimum number of players with `?config @players(min: 8)` or the team configuration with `?config @teams([4, 4])`. Simply call `?config` to see your active settings. You can also add these commands to your text channel's *topic* setting in Discord. These will be run every time the lobby restarts. 

## Plugins
Beyond the standard commands and directives, contributors have added plugins to power advanced, game specific, features. These can be found in the `./plugins/` directory. Every plugin starts with a new directive. Plugins can change settings for the lobby as well as install extra commands. 

## Running your Own Instance
1. [Create and invite your own bot](https://discordpy.readthedocs.io/en/latest/discord.html). Make sure to get your secret token.
2. Verify your [environment setup](#Environment-Setup)
3. Run the bot `DISCORD_TOKEN="<your secret token>" python bot.py`

## Requirements
- Python ^3.8

### Environment Setup
***Windows***
- Open a command prompt and navigate to this project's root directory. 
- Run `python -m venv venv` to recreate this repo's virtual environment.
- Run `.\venv\Scripts\activate.bat` to activate the env.
- Run `pip install -r requirements.txt` to install this project's dependencies.

****nix/macOS***
- Open a terminal and navigate to this project's root directory.
- Run `python -m venv env` to recreate this repo's virtual environment.
- Run `source ./env/bin/activate` to activate the env.
- Run `pip install -r requirements.txt` to install this project's dependencies.

## History
This isn't the second version of the bot, so the '2' in the name makes no sense. Actually, this bot was specifically designed to help us launch into a *Left 4 Dead 2* verses match. Getting eight people on board took serious effort so we created this tool to help out. Eventually the bot was genericized to support other games of different sizes and team compositions. We're continuing to develop features and improve the experience so feel free to open an issue or contribute. Thanks for reading!
