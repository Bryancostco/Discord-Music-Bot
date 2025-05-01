# PokéBot - A Discord Bot for Music and Pokémon Fans

PokéBot is a Python-based Discord bot that can play music, show Pokémon data, and fetch Pokémon card prices using public APIs. It's designed for fun, learning, and practicing API integrations.

## Features

- `!play [song name or Spotify link]` — Plays music using YouTube search.
- `!join`, `!leave`, `!skip` — Voice channel controls.
- `!pokemon [name]` — Retrieves a Pokémon's abilities and types using the PokéAPI.
- `!cardPrice [card name]` or `!cardPrice [name + number]` — Gets market prices from the Pokémon TCG API.
- `!ping` — Basic ping command to check if the bot is running.
- `!Dababy` — Just for fun.

## Installation

1. Clone the repository

   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name



## Env file example
    these are the keys that should be saved in your .env

    DISCORD_TOKEN=your_discord_bot_token
    SPOTIFY_CLIENT_ID=your_spotify_client_id
    SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
    OKEMONTCG_IO_API_KEY=your_pokemontcg_api_key

## Finally to run 
    python your_main_file.py (bot.py)



## notes 
    
    The bot uses the YouTube-DLP library and FFmpeg to stream audio. 
    You will need FFmpeg installed and added to your system path.