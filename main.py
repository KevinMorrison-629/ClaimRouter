

from typing import List

import discord
import discord.ext.commands as commands
import discord.ext.tasks as tasks
from discord import Guild, RawReactionActionEvent, Embed, Message
from itertools import cycle

import asyncio
import sqlite3
import dotenv
import os



# Constants
dotenv.load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")

DB_FILEPATH = "RoutedClaims.db"
MUDAE_BOT_ID = 432610292342587392

TN_ACTIVEGUILDS = "ACTIVE_GUILDS"
TN_ROUTES = "ROUTES"
TN_ROUTEDMESSAGES = "ROUTED_MESSAGES"
TN_CHARACTEREMBEDS = "CHARACTER_EMBEDS"
EN_GUILDID = "GUILD_ID"
EN_SRCCHANNEL = "SRC_CHANNEL"
EN_DESTCHANNEL = "DEST_CHANNEL"
EN_MESSAGEID = "MESSAGE_ID"
EN_CHARNAME = "NAME"
EN_CHARORIGIN = "ORIGIN"
EN_CHARVALUE = "VALUE"
EN_CHARIMGURL = "IMG_URL"
EN_CHARIMGPROXYURL = "IMG_PROXY_URL"

intents = discord.Intents.default()
intents.message_content = True


# Initialize Discord Clien
client = commands.Bot(command_prefix="|bot|:", intents=intents)

# Create Bot Status List (just for a bit of fun)
statusList = cycle([discord.Game('in the Sand'),
                     discord.Game('with Waifu Bot'),
                     discord.Game('with myself'),
                     discord.Activity(type=discord.ActivityType.watching, name='Anime'),
                     discord.Activity(type=discord.ActivityType.watching, name='you waste your life'),
                     discord.Activity(type=discord.ActivityType.listening, name='to silence')])

# Create A Connection to a database (will store route information here)
con = sqlite3.connect(DB_FILEPATH)
cur = con.cursor()


# Database Helper Functions
def initializeTables() -> None:
    cur.execute(f"CREATE TABLE IF NOT EXISTS {TN_ACTIVEGUILDS}({EN_GUILDID})")
    cur.execute(f"CREATE TABLE IF NOT EXISTS {TN_ROUTES}({EN_GUILDID}, {EN_SRCCHANNEL}, {EN_DESTCHANNEL})")
    cur.execute(f"CREATE TABLE IF NOT EXISTS {TN_ROUTEDMESSAGES}({EN_MESSAGEID})")
    cur.execute(f"CREATE TABLE IF NOT EXISTS {TN_CHARACTEREMBEDS}({EN_CHARNAME}, {EN_CHARORIGIN}, {EN_CHARVALUE}, {EN_CHARIMGURL}, {EN_CHARIMGPROXYURL})")
    con.commit()
    return

def getAllActiveGuilds() -> set:
    try:
        query = f"""SELECT {EN_GUILDID} FROM {TN_ACTIVEGUILDS}"""
        cur.execute(query)
        return {each[0] for each in cur.fetchall()}
    except Exception as exc:
        print(f"[Error] (getAllActiveGuilds): {exc}")
        print(f"\tQuery: \"{query}\"")
        return set()

def getChannelRoutes(guildId : int, srcChannel : int) -> List[int]:
    try:
        query = f"""SELECT ({EN_DESTCHANNEL}) FROM {TN_ROUTES} WHERE {EN_GUILDID}={guildId} AND {EN_SRCCHANNEL}={srcChannel}"""
        cur.execute(query)
        res = [each[0] for each in cur.fetchall()]
        if len(res) > 0:
            return res
        query = f"""SELECT ({EN_DESTCHANNEL}) FROM {TN_ROUTES} WHERE {EN_GUILDID}={guildId} AND {EN_SRCCHANNEL}={-1}"""
        cur.execute(query)
        res = [each[0] for each in cur.fetchall()]
        return res
    except Exception as exc:
        print(f"[Error] (getChannelRoutes): {exc}")
        print(f"\tQuery: \"{query}\"")
        return []

def isRouted(messageId : int) -> bool:
    try:
        query = f"""SELECT ({EN_MESSAGEID}) FROM {TN_ROUTEDMESSAGES} WHERE {EN_MESSAGEID}={messageId}"""
        cur.execute(query)
        return len(cur.fetchall()) > 0
    except Exception as exc:
        print(f"[Error] (isRouted): {exc}")
        print(f"\tQuery: \"{query}\"")
        return True

def addRoutedMessage(messageId : int) -> None:
    try:
        query = f"INSERT INTO {TN_ROUTEDMESSAGES} VALUES ({messageId})"
        cur.execute(query)
        con.commit()
    except Exception as exc:
        print(f"[Error] (addRoutedMessage): {exc}")
        print(f"\tQuery: \"{query}\"")

def addGuild(guildId : int) -> None:
    try:
        query = f"INSERT INTO {TN_ACTIVEGUILDS} VALUES ({guildId})"
        cur.execute(query)
        con.commit()
    except Exception as exc:
        print(f"[Error] (addGuild): {exc}")
        print(f"\tQuery: \"{query}\"")

def addDefaultRoute(guildId : int, destChannel : int) -> None:
    try:
        query = f"DELETE FROM {TN_ROUTES} WHERE {EN_GUILDID}={guildId} AND {EN_SRCCHANNEL}={-1}"
        cur.execute(query)
        con.commit()
        query = f"INSERT INTO {TN_ROUTES} VALUES ({guildId}, {-1}, {destChannel})"
        cur.execute(query)
        con.commit()
    except Exception as exc:
        print(f"[Error] (addDefaultRoute): {exc}")
        print(f"\tQuery: \"{query}\"")

def addRoute(guildId : int, srcChannel : int, destChannel : int) -> None:
    try:
        query = f"DELETE FROM {TN_ROUTES} WHERE {EN_GUILDID}={guildId} AND {EN_SRCCHANNEL}={srcChannel}"
        cur.execute(query)
        con.commit()
        query = f"INSERT INTO {TN_ROUTES} VALUES ({guildId}, {srcChannel}, {destChannel})"
        cur.execute(query)
        con.commit()
    except Exception as exc:
        print(f"[Error] (addRoute): {exc}")
        print(f"\tQuery: \"{query}\"")

def addCharacterEntry(name : str, origin : str, val : str, imgUrl : str, proxyUrl : str) -> None:
    try:
        query = f"""INSERT INTO {TN_CHARACTEREMBEDS} VALUES (?, ?, ?, ?, ?)"""
        cur.execute(query, (name, origin, val, imgUrl, proxyUrl))
        con.commit()

        print(f"\tNew Character Entry [{name} | {origin} | {val}]")
    except Exception as exc:
        print(f"[Error] (addCharacterEntry): {exc}")
        print(f"\tQuery: \"{query}\"")


# Discord Bot Helper Functions
async def tryRouteClaim(payload : RawReactionActionEvent) -> None:
    """"""
    try:
        roll_channel = client.get_channel(payload.channel_id)

        validClaimsChannels = getChannelRoutes(payload.guild_id, payload.channel_id)
        if (len(validClaimsChannels) > 0):
            claim_id = validClaimsChannels[0]
        else:
            print("\t[REACTION]: No Valid Route Destination Found")
            print(f"\t\t[Guild: {roll_channel.guild.name}] [RollChannel: {roll_channel.name}]")
            return False

        claimChannel = client.get_channel(claim_id)
        roll_channel = client.get_channel(payload.channel_id)

        if claimChannel is None:
            print("\t[REACTION]: Could Not Retrieve ClaimChannel")
            return False
        if roll_channel is None:
            print("\t[REACTION]: Could Not Retrieve RollChannel")
            return False

        message : Message = await roll_channel.fetch_message(payload.message_id)

        # Message Checks
        if payload.event_type != 'REACTION_ADD':
            # print("\t[REACTION]: Not Added Reaction")
            return False
        if 'kakera' in payload.emoji.name:
            # print("\t[REACTION]: Emoji was 'kakera'")
            return False
        if payload.user_id == MUDAE_BOT_ID:
            # print("\t[REACTION]: User was Mudae Bot")
            return False
        if payload.guild_id not in getAllActiveGuilds():
            # print("\t[REACTION]: Guild id Not Found")
            return False
        if payload.channel_id == claimChannel.id:
            # print("\t[REACTION]: Channel ID is Claims Channel")
            return False
        if message.author.id != MUDAE_BOT_ID:
            # print("\t[REACTION]: Reaction was not on a Mudae Roll")
            return False
        if len(message.embeds) <= 0:
            # print("\t[REACTION]: No Embeds Founds in Message")
            return False
        if 'footer' not in message.embeds[0].to_dict():
            # print("\t[REACTION]: No Footer Found in Message (not claimed)")
            return False
        if 'text' not in message.embeds[0].to_dict()['footer']:
            # print("\t[REACTION]: No text was found in footer (not claimed)")
            return False
        if '~~' in message.embeds[0].to_dict()['footer']['text'] or 'Belongs to' not in message.embeds[0].to_dict()['footer']['text']:
            # print("\t[REACTION]: Roll Not Claimed")
            return False
        if isRouted(message.id):
            # print("\t[REACTION]: Message has already been routed")
            return False

        for embed in message.embeds:
            await claimChannel.send(embed=embed)
            addRoutedMessage(payload.message_id)

    except Exception as exc:
        print(f"[Error] (tryRouteClaim): {exc}")


async def storeRolls(message : Message) -> None:
    """"""
    try:
        if message.author.id != MUDAE_BOT_ID:
            # print(f"\t[ON_MESSAGE]: Message is not from MudaeBot")
            return False
        if len(message.embeds) <= 0:
            # print("\t[ON_MESSAGE]: No Embeds Founds in Message")
            return False
        if len(message.embeds[0].to_dict()) <= 0:
            # print("\t[ON_MESSAGE]: Embeds Are empty")
            return False
        
        embedDict = message.embeds[0].to_dict()

        if "author" not in embedDict:
            return False
        if "name" not in embedDict["author"]:
            return False
        if "description" not in embedDict:
            return False
        if "React with any emoji to claim!" not in embedDict["description"]:
            return False
        if "image" not in embedDict:
            return False
        if "url" not in embedDict["image"] and "proxy_url" not in embedDict["image"]:
            return False

        name = embedDict["author"]["name"]
        origin = " ".join(embedDict["description"][0:(embedDict["description"].find("**"))].split())
        value = embedDict["description"][(embedDict["description"].find("**")):(embedDict["description"].rfind("**"))].strip("*")
        url = embedDict["image"]["url"]
        proxy_url = embedDict["image"]["proxy_url"]

        addCharacterEntry(name, origin, value, url, proxy_url)
    except Exception as exc:
        print(f"[Error] (storeRolls): {exc}")



# Discord Bot Events/Command Functions
@client.event
async def on_ready():
    print("Bot Online")
    print(f"{len(client.guilds)} Active Guilds")

    initializeTables()

    for guild in client.guilds:
        if (guild.id not in getAllActiveGuilds()):
            addGuild(guild.id)
            print("Adding Guild To Database")

    change_status.start()

@commands.guild_only()
@commands.has_permissions(manage_channels=True)
@client.event
async def on_raw_reaction_add(payload : RawReactionActionEvent):
    """"""
    await asyncio.sleep(2.5)
    await tryRouteClaim(payload)


@commands.guild_only()
@commands.has_permissions(manage_channels=True)
@client.event
async def on_message(message : Message):
    """"""
    await client.process_commands(message)
    await storeRolls(message)


@tasks.loop(seconds=6000)
async def change_status():
    await client.change_presence(activity=next(statusList))
    print('Changing Status')

@client.event
async def on_guild_join(guild : Guild):
    print(f"Joining Guild: {guild.name}")
    if guild.id not in getAllActiveGuilds():
        print(f'Adding claim channel to: {guild.name}')
        new_channel = await guild.create_text_channel('posted-claims')
        print(f'\t{new_channel.name} channel added to {guild.name}')

        await new_channel.send('Default Claim Routing set to this channel \nUse "|bot|:help" to see a list of helpful commands')
        print(f'\tDefault Routing set to the {new_channel.id} channel')

        addGuild(guild.id)
        addRoute(guild.id, -1, new_channel.id)

@commands.guild_only()
@commands.has_permissions(manage_channels=True)
@client.command()
async def setAsDefaultRoute(ctx : commands.Context):
    '''Sets a default channel that all claims in the server will be routed to
    
    usage:     |bot|:setAsDefaultRoute
    '''
    addDefaultRoute(ctx.message.guild.id, ctx.message.channel.id)

    await ctx.send(f'Default Routing set to the {ctx.message.channel.name} channel')
    print(f'Default Routing set to {ctx.message.channel.id} [GuildId:{ctx.message.guild.id}]')

@commands.guild_only()
@commands.has_permissions(manage_channels=True)
@client.command()
async def routeTo(ctx : commands.Context, *, destChannelId : int):
    '''Routes claims in this channel to a specifc channel id
        
        usage:     |bot|:routeTo <channel_id_here>
        '''
    if int(destChannelId) in [x.id for x in ctx.guild.text_channels]:
        addRoute(ctx.guild.id, ctx.message.channel.id, destChannelId)
        await ctx.send(f'Route set from {ctx.message.channel.name} to {destChannelId}')
    else:
        await ctx.send(f'Could Not Route Claims in {ctx.message.channel.name} to {destChannelId}')


if __name__ == "__main__":
    client.run(BOT_TOKEN)


    # build using "pyinstaller main.py -F"