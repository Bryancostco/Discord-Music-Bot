import discord
from discord.ext import commands
import asyncio
import yt_dlp as youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import pokemontcgsdk
from pokemontcgsdk import Card
from pokemontcgsdk import Set
from dotenv import load_dotenv
import os 



load_dotenv()

# Intents & Bot Setup 
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
poke_base_url = "https://pokeapi.co/api/v2/"
POKEMONTCG_IO_API_KEY = os.getenv("POKEMONTCG_IO_API_KEY")

# Spotify API Setup 
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
spotify_credentials = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)
spotify = spotipy.Spotify(client_credentials_manager=spotify_credentials)

# yt_dlp and FFmpeg Options 
ytdl_format_options = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}
ffmpeg_options = {'options': '-vn'}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# YTDL Source 
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# Music Player Class 
class MusicPlayer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.bot = ctx.bot
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

    async def player_loop(self):
        while True:
            self.next.clear()
            track = await self.queue.get()
            self.ctx.voice_client.play(
                track,
                after=lambda e: self.bot.loop.call_soon_threadsafe(self.next.set)
            )
            await self.ctx.send(f"playing: **{track.title}**")
            await self.next.wait()

# Music Cog 
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
        print("🎶 Music cog initialized")

    def get_player(self, ctx):
        player = self.players.get(ctx.guild.id)
        if not player:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player
            self.bot.loop.create_task(player.player_loop())
        return player

    @commands.command(name="join")
    async def join_(self, ctx):
        print(f"🔊 join_() triggered by {ctx.author} in guild {ctx.guild}")
        if ctx.author.voice:
         channel = ctx.author.voice.channel
         vc = ctx.voice_client
        if vc is None:
             try:
                await channel.connect()
                await ctx.send(f" BOMBOCLAT whats good {channel.name}")
                print("✅ Im IN 😈.")
             except Exception as e:
                print(f"couldn't join VC: {e}")
                await ctx.send(f" Couldn't join the voice channel.\n**Error:** {e}")

        else:
         await ctx.send("bro r u stupid ur not even in vc.")


    @commands.command(name="play")
    async def play_(self, ctx, *, query):
        print(f"🎵 play_() called with query: {query}")
        await ctx.send("🎧 Thinking about whether this shi ass or gas")

        if not ctx.voice_client:
            join_command = self.bot.get_command("join")
            await ctx.invoke(join_command)

        player = self.get_player(ctx)

        if "open.spotify.com/track" in query:
            try:
                loop = self.bot.loop
                track_info = await loop.run_in_executor(None, lambda: spotify.track(query))
                track_name = track_info['name']
                artist_names = ", ".join(artist['name'] for artist in track_info['artists'])
                search_query = f"{track_name} {artist_names}"
                await ctx.send(f"🔍 Searching YouTube for: **{track_name}** by **{artist_names}**")
            except Exception as e:
                print(f" Spotify lookup error: {e}")
                await ctx.send("Could not retrieve Spotify track info.")
                return
        else:
            search_query = query

        loop = self.bot.loop
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{search_query}", download=False))
        except Exception as e:
            print(f" YouTube search error: {e}")
            await ctx.send(" YouTube search failed.")
            return

        if not data or not data.get('entries'):
            await ctx.send(" No results found.")
            return

        video = data['entries'][0]
        try:
            source = await YTDLSource.from_url(video['webpage_url'], loop=loop, stream=True)
        except Exception as e:
            print(f" Error loading audio: {e}")
            await ctx.send(" Failed to load audio.")
            return

        await player.queue.put(source)
        await ctx.send(f" Ur Goofy ahh queued: **{source.title}**")

    @commands.command(name="skip")
    async def skip_(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Skipped!")

    @commands.command(name="leave")
    async def leave_(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Cya.")
        else:
            await ctx.send("dumbahh I'm not in a voice channel.")
            

# Events 
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    print(f"✅ Registered commands: {[command.name for command in bot.commands]}")

@bot.command()
async def ping(ctx):
    await ctx.send("pong")
    
@bot.command(name="pokemon")
async def Pokemon_(ctx, name):
    print(f"[DEBUG] Pokemon_ command called with name={name}")

    url = f"{poke_base_url}/pokemon/{name.lower()}"
    print(f"[DEBUG] Fetching from URL: {url}")

    response = requests.get(url)
    print(f"[DEBUG] Response status code: {response.status_code}")

    if response.status_code != 200:
        await ctx.send(f" Couldn't find a Pokémon named '{name}'. Check your spelling!")
        print(f"[ERROR] Invalid Pokémon name: {name}")
        return

    pokemon_data = response.json()
    print(f"[DEBUG] Data keys: {list(pokemon_data.keys())}")

    # abilities
    abilities = [a['ability']['name'] for a in pokemon_data['abilities']]
    print(f"[DEBUG] Found abilities: {abilities}")
    ability_list = ", ".join([ability.title() for ability in abilities])

    # type
    types = [t['type']['name'] for t in pokemon_data['types']]
    print(f"[DEBUG] Found types: {types}")
    type_list = ", ".join([ptype.title() for ptype in types])

    # clean set up 
    await ctx.send(
        f"🔎 **{name.title()}**\n"
        f"🧬 Abilities: {ability_list}\n"
        f"🌟 Types: {type_list}"
    )
    print(f"[DEBUG] Sent info for {name.title()}")
    
    
@bot.command(name="cardPrice")
async def cardPrice_(ctx, *, query):
    headers = {"X-Api-Key": POKEMONTCG_IO_API_KEY}

    # Try to split out number from the end
    parts = query.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        name_query = parts[0]
        card_number = parts[1]
        full_query = f'name:"{name_query}" number:{card_number}'
    else:
        full_query = f'name:"{query}"'

    params = {"q": full_query}
    response = requests.get("https://api.pokemontcg.io/v2/cards", headers=headers, params=params)

    if response.status_code != 200:
        await ctx.send(" API error while fetching card data. Tell bryan")
        return

    data = response.json()
    cards = data.get("data", [])

    if not cards:
        await ctx.send(f" no cards found matching **{query}**.")
        return

    response_lines = [f"Found {len(cards[:5])} cards for \"{query}\":\n"]

    for card in cards[:5]:
        name = card.get("name", "Unknown")
        number = card.get("number", "?")
        set_info = card.get("set", {})
        set_code = set_info.get("id", "?")
        print("found card and info ")
        url = card.get("tcgplayer", {}).get("url", "")
        market = card.get("tcgplayer", {}).get("prices", {}).get("holofoil", {}).get("market")

        price_str = f"${market:.2f}" if isinstance(market, float) else "Not listed"

        if url:
            response_lines.append(f"- **[{name} ({number}/{set_code})]({url})** – {price_str}")
            print("url has been added")
        else:
            response_lines.append(f"- **{name} ({number}/{set_code})** – {price_str}")

    await ctx.send("\n".join(response_lines))
    

@bot.command()
async def Dababy(ctx):
    await ctx.send("Lets GO!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

# Main Entrypoint 
async def main():
    async with bot:
        print("🔁 Adding Music cog...")
        await bot.add_cog(Music(bot))
        print("✅ Music cog added.")
        DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
        await bot.start("DISCORD_TOKEN") 

asyncio.run(main())
