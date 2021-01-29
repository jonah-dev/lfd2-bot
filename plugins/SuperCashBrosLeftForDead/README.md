## Usage

```
@SuperCashBrosLeftForDead(...)
```

## Features

### Lobby Setting Defaults
  - Player Min: 8
  - Player Max: 8
  - Teams: [4, 4]
  - Overflow: On

### Ranked Gameplay
```
@SuperCashBrosLeftForDead(history: '<gsheets ID>')
```
... where `<gsheets ID>` points to Google Sheet like
[1KMCycw69dIHHyOrfrRU0eZjsOa7BDgom-UPU2Swb5rw](https://docs.google.com/spreadsheets/d/1KMCycw69dIHHyOrfrRU0eZjsOa7BDgom-UPU2Swb5rw). The first sheet must match this format. The later pages are human-edited (by you) after playing matches. You can set them up however you want as long as the first page looks like it does in the example.
- `?leaderboard` will produce player rankings. These are based on win/loss history and score differences. Provide the `lobby` argument to filter the list to players in the lobby.
- `?ranked` will produce output like `?shuffle` but the teams are ordered based on average team rank. 

## Running your Own Instance
In order to access google sheets, you need to provide two files in the root of your project folder: `client_secrets.json` and `oath_cache.json`. You can create them with your google account. 

[Follow these instructions](https://gsheets.readthedocs.io/en/stable/)