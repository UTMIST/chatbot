# This code takes the AI functions and incorporates into a discord Bot 
import discord
from discord.ext import commands
from custom_query import aiResponse, classifyRelevance, get_response_with_relevance
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True

from pathlib import Path

from dotenv import load_dotenv

client = discord.Client(intents=intents)

#testing channel (channel we want the bot to work in)

env_path = Path("..") / ".env"
load_dotenv(dotenv_path=env_path)



@client.event
async def on_ready():
    print("Bot is now online")

@client.event
async def on_message(message):

    #avoid same message between user and the bot
    if message.author == client.user:
        return
    
    print("message: ", message.content)

    #Check if the message is from the target guild
    #add reaction
    if message.content == 'thanks':
        await message.add_reaction('\U0001F970')

    #respond
    elif message.content == 'hello':
        await message.channel.send("Welcome to UTMIST!")
        
    else:
        print(message.content)

        relevance = classifyRelevance(message.content)

        print("relevance: ", relevance)

        output = get_response_with_relevance(message.content)
        
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


client.run(os.environ.get("DISCORD_BOT_TOKEN"))