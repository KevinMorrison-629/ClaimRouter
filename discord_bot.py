

import discord
from discord.ext import commands, tasks
from itertools import cycle
import random
import os
import time
import asyncio

import pickle



# ============================================================================ #
# |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||| #
# ============================================================================ #



def save_asPickle(filename, dict_var):
    with open('routing/'+filename+'.pkl','wb') as f:
        pickle.dump(dict_var, f, protocol=pickle.HIGHEST_PROTOCOL)
    print('file saved as: {}'.format(filename))

def load_asPickle(filename):
    with open('routing/'+filename+'.pkl','rb') as f:
        dict_var = pickle.load(f)
        print('load saved: {}'.format(filename))
        return dict_var

if not os.path.exists('routing'):
    os.makedirs('routing')


routes = {}

routed_messages = []

if os.path.exists('routing/routes.pkl'):
    routes = load_asPickle('routes')
    print('route channels:')
    print(routes)
else:
    print('path doesnt exist')


if os.path.exists('bot_token.txt'):
    with open('bot_token.txt') as f:
        my_token = f.read()
        f.close
else:
    raise Exception


client = commands.Bot(command_prefix = '|bot|:')

status_list = cycle([discord.Game('League and hating myself'),
                     discord.Game('in the Sand'),
                     discord.Game('with Waifu Bot'),
                     discord.Game('with myself'),
                     discord.Activity(type=discord.ActivityType.watching, name='Anime'),
                     discord.Activity(type=discord.ActivityType.watching, name='some inters'),
                     discord.Activity(type=discord.ActivityType.watching, name='you waste your life'),
                     discord.Activity(type=discord.ActivityType.listening, name='to silence')])

mudae_bot_id = 432610292342587392



@client.command()
async def route_to(ctx, *, channel_id):
    '''Routes claims in this channel to a specifc channel id
    
    usage:     |bot|:route_to <channel_id_here>
    '''
    rolls_chan = ctx.message.channel.id
    guild_var = ctx.message.channel.guild
    guild_id = guild_var.id
    
    if guild_id not in routes:
        routes[guild_id] = {}
    try:
        chan_id = None
        for each in guild_var.text_channels:
            if int(channel_id) == each.id:
                chan_id = int(channel_id)
                continue
        if chan_id == None:
            print('Error_1: Not Valid Channel ID')
            return            
    except Exception as excep:
        print('Error_2: Not Valid Channel ID')
        print(excep)
        return
        
    routes[guild_id][rolls_chan] = chan_id
    print('Routing rolls in {} to the {} channel'.format(rolls_chan, chan_id))
    await ctx.send('Routing rolls in {} to the {} channel'.format(rolls_chan, chan_id))
    save_asPickle('routes', routes)


@client.command()
async def default_route(ctx, *, channel_id):
    '''Sets a default channel that all claims in the server will be routed to
    
    usage:     |bot|:default_route <channel_id_here>
    '''    
    guild_var = ctx.message.channel.guild
    guild_id = guild_var.id
    
    if guild_id not in routes:
        routes[guild_id] = {}
    try:
        chan_id = None
        for each in guild_var.text_channels:
            if int(channel_id) == each.id:
                chan_id = int(channel_id)
                continue
        if chan_id == None:
            print('Error_1: Not Valid Channel ID')
            return            
    except Exception as excep:
        print('Error_2: Not Valid Channel ID')
        print(excep)
        return
    
    routes[guild_id]['default'] = chan_id
    
    await ctx.send('Default Routing set to the {} channel'.format(chan_id))
    print('Default Routing set to the {} channel'.format(chan_id))
    save_asPickle('routes', routes)




@client.event
async def on_raw_reaction_add(payload):
    await asyncio.sleep(2.5)
    if payload.event_type == 'REACTION_ADD':
        if 'kakera' not in payload.emoji.name:
            if payload.user_id != mudae_bot_id:
                
                rolls_chan = payload.channel_id
                guild_var = client.get_channel(payload.channel_id).guild
                
                if guild_var.id in routes:
                    if rolls_chan in routes[guild_var.id]:
                        claim_id = routes[guild_var.id][rolls_chan]
                    elif 'default' in routes[guild_var.id]:
                        claim_id = routes[guild_var.id]['default']
                    else:
                        print('No Route Found')
                        return
                    claims_chan = client.get_channel(claim_id)
                    
                    if payload.channel_id != claims_chan.id:
                        roll_channel = client.get_channel(payload.channel_id)
                        message = await roll_channel.fetch_message(payload.message_id)
                        
                        if message.author.id == mudae_bot_id:
                            if len(message.embeds) > 0:
                                if 'footer' in message.embeds[0].to_dict():
                                    if 'text' in message.embeds[0].to_dict()['footer']:
                                        reactor = message.embeds[0].to_dict()['footer']['text']
                                        
                                        if '~~' not in reactor:
                                            if 'Belongs to' in reactor:
                                                if message.id not in routed_messages:
                                                    embeds = message.embeds
                                                    for embed in embeds:
                                                        print(embed.to_dict())
                                                        await claims_chan.send(embed=embed)
                                                        
                                                        routed_messages.insert(0, message.id)
                                                        if len(routed_messages) > 1000:
                                                            routed_messages.pop()
                                                else:
                                                    print('Message has already been routed')
                                            else:
                                                print("No 'Belongs to' in claim")
                                        else:
                                            print("'~~' in claim (page choice)")
                                    else:
                                        print('no text in footer')
                                else:
                                    print('no footer in embeded img')
                            else:
                                print('No embed in message')                                
                        else:
                            print('Image was not sent by Mudae')
                    else:
                        print('Reaction done in posted-claims channel (wrong channel)')
                else:
                    print('Guild not in Claim Routes')
            else:
                print('Reaction done by Mudae')
        else:
            print('Is kakera reaction')
    else:
        print('not REACTION_ADD')

@client.event
async def on_ready():
    print('Bot is Online')
    change_status.start()

@tasks.loop(seconds=6000)
async def change_status():
    await client.change_presence(activity=next(status_list))
    print('Changing Status')


client.run(my_token)
