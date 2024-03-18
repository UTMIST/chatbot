import discord

client = discord.Client()

@client.event
async def on_ready():
    print("Bot is now online")

@client.event
async def on_message(message):
    #avoid same message between user and the bot
    if message.author == client.user:
        return

    #add reaction
    if message.content == 'thanks':
        await message.add_reaction('\U0001F970')

    #respond
    if message.content == "hello":
        await message.channel.send("Welcome to UTMIST!")

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


client.run('MTIwODQ0NzgxMTAyOTMwNzUwMw.GPD84a.gDtF4mKY3KHX-FBsWR3Yz6X7RRhFCRGttCp3qs')

