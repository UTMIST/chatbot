# This code takes the AI functions and incorporates into a discord Bot 
import discord
from discord.ext import commands
from custom_query import aiResponse
import time

intents = discord.Intents.default()
intents.messages = True
intents.reactions = True

client = discord.Client(intents=intents)
dic = {}
#testing channel (channel we want the bot to work in)

@client.event
async def on_ready():
    print("Bot is now online")

@client.event
async def on_message(message):
    #avoid same message between user and the bot
    if message.author == client.user:
        return
    
    if message.author not in dic:
        dic[message.author] = [1, time.time()]
    else:
        dic[message.author][0] += 1
        if time.time() - dic[message.author][1] >= 86400:
            dic[message.author] = [1, time.time()]
            
    if dic[message.author][0] > 10:
        await message.channel.send("You have reached your message limit for the day. Come back again in 24 hours.")
        return
    
    #Check if the message is from the target guild
    #add reaction
    if message.content == 'thanks':
        await message.add_reaction('\U0001F970')

    #respond
    elif message.content == 'hello':
        await message.channel.send("Welcome to UTMIST!")
        
    else:
        output = aiResponse(message.content)
        await message.channel.send(output)

#addressing edited messages
@client.event
async def on_message_edit(before, after):
    await before.channel.send(
        f'{before.author} edit a message.\n'
        f'Before: {before.content}\n'
        f'After:{after.content}'
    )


@client.event
async def on_reaction_add(reaction, user):
    await reaction.message.channel.send(f'{user} reacted with {reaction.emoji}')


client.run('Your Key')