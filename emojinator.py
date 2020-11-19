#!/usr/bin/env python3
import discord
from io import BytesIO
import aiohttp
from subprocess import check_output
import asyncio
from time import time
from json import load
from random import choice

client = discord.Client()

__emoji_help = """Usage:
!emoji import <custom emoji to import> <another custom emoji> ... - emoji will be imported using the name from the other server
!emoji image <name> - attach an image and specify the name to import. image must be smaller than 256kb
!emoji url <name> <url> - specify an emoji name and image url to import. image must be smaller than 256kb
!emoji geturl <custom emoji> <another custom emoji> ... - emoji urls will be listed to the user for further use
!emoji mashup - get a random mashup from @emojimashupbot"""

last_status_update = 0


async def playing_update():
    global last_status_update
    if time() - last_status_update < 30:
        return
    last_status_update = time()
    emoji_sum = sum(len(g.emojis) for g in client.guilds)
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="{} emojis on {} servers".format(emoji_sum, len(client.guilds))))

def get_emoji_count(guild):
    emojis = guild.emojis
    normal = [e for e in emojis if not e.animated]
    animated = [e for e in emojis if e.animated]
    if not guild.premium_tier:
        return "{0}/50 normal, {1}/50 animated".format(len(normal), len(animated))
    elif guild.premium_tier in [1,2]:
        return "{0}/{2} normal, {1}/{2} animated".format(len(normal), len(animated), 50+(guild.premium_tier*50))
    else:
        return "{0}/250 normal, {1}/250 animated".format(len(normal), len(animated))

async def get_bytes_from_url(url, max_size=256*1024):
    if max_size:
        async with aiohttp.ClientSession() as session:
            async with session.head(url) as resp:
                if int(resp.headers["Content-Length"]) > max_size:
                    return False, "Image at specified url is too large (max 256kB)"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            img_bytes = await resp.read()
            return True, img_bytes

async def emoji(message):
    content = message.content[6:].strip()
    try:
        cmd, *args = content.split()
        if cmd not in ["import", "image", "url", "geturl", "mashup"]:
            content = None
    except ValueError:
        content = None
    if not content:
        try:
            await message.author.send(__emoji_help)
        except discord.Forbidden:
            await message.channel.send(__emoji_help)
        return
    if cmd == "import":
        out = []
        for emoji_inp in args:
            animated,shortname,emoji_id = emoji_inp[1:-1].split(":")
            success, resp = await get_bytes_from_url(f"https://cdn.discordapp.com/emojis/{emoji_id}." + ("gif" if animated else "png"))
            if not success:
                print(repr(resp))
                await message.channel.send(resp)
                continue
            try:
                emoji = await message.guild.create_custom_emoji(name=shortname, image=resp, reason=f"Added by {message.author.name}#{message.author.discriminator}")
            except discord.errors.HTTPException as e:
                err = "!emoji failed on {}: {}".format(emoji_inp[1:-1], e.text.split("\n")[1])
                await message.channel.send(err)
                print(err)
                continue
            except discord.errors.InvalidArgument as e:
                err = "!emoji failed on {}: Invalid argument: {}".format(emoji_inp[1:-1], e.text.replace("\n", ""))
                await message.channel.send(err)
                print(err)
                continue
            out.append(str(emoji))
        response = get_emoji_count(message.guild) + "\n" + " ".join(out)
        print(repr(response))
        await message.channel.send(response)
    elif cmd == "image":
        out = []
        for arg,attachment in zip(args, message.attachments):
            img_bytes = await attachment.read()
            try:
                emoji = await message.guild.create_custom_emoji(name=arg, image=img_bytes, reason=f"Added by {message.author.name}#{message.author.discriminator}")
            except discord.errors.HTTPException as e:
                await message.channel.send("!emoji failed on {}: {}".format(arg, e.text.split("\n")[1]))
                continue
            out.append(str(emoji))
        await message.channel.send(get_emoji_count(message.guild) + "\n" + " ".join(out))
    if cmd == "url":
        name, url = args
        success, resp = await get_bytes_from_url(url)
        if not success:
            await message.channel.send(resp)
            return
        try:
            emoji = await message.guild.create_custom_emoji(name=name, image=resp, reason=f"Added by {message.author.name}#{message.author.discriminator}")
        except discord.errors.HTTPException as e:
            await message.channel.send("!emoji failed: {}".format(e.text))
            return
        await message.channel.send(get_emoji_count(message.guild) + "\n" + str(emoji))
    elif cmd == "geturl":
        out = []
        for emoji_inp in args:
            animated,shortname,emoji_id = emoji_inp[1:-1].split(":")
            out.append(f"<https://cdn.discordapp.com/emojis/{emoji_id}." + ("gif" if animated else "png") + ">")
        await message.channel.send("\n".join(out))
    elif cmd == "mashup":
        with open("emojimashup.json") as f:
            mashup_data = load(f)
        mashup = choice(mashup_data)
        await asyncio.sleep(1)
        await message.channel.send("{1} = https://pbs.twimg.com/media/{0}.jpg".format(*mashup))


@client.event
async def on_message(message):
    if message.author.bot:
        return
    await playing_update()

#    if message.content.lower().startswith("!boop emojinator") and message.channel.id == 697503616587792415:
#        await client.get_channel(697503616587792415).send("I've been booped! Back shortly...")
#        await client.logout()

    if message.content.lower().startswith("!emoji"):
        print("{}({}) {}#{}: {}".format(message.guild.name, message.guild.id, message.author.name, message.author.discriminator, repr(message.content)))
        if message.content.lower().startswith("!emoji mashup") or message.author.permissions_in(message.channel).manage_emojis:
            async with message.channel.typing():
                await emoji(message)
        else:
            await message.channel.send("No 'Manage Emoji' permission")

    if message.content.lower() == "!invite":
        await message.channel.send(discord.utils.oauth_url(client.user.id, permissions=discord.Permissions(1073743872)))

@client.event
async def on_ready():
    print("Logged in as {} ({})".format(client.user.name, client.user.id))
    if client.user.bot:
        print(discord.utils.oauth_url(client.user.id, permissions=discord.Permissions(1073743872)))
    await playing_update()

if __name__ == "__main__":
    with open(".bottoken") as f:
        client.run(f.read().strip())
