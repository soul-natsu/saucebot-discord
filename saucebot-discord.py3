#!/usr/bin/python3

# Saucebot, a discord bot for interacting with furaffinity URLs

__title__ = 'saucebot-discord'
__author__ = 'Goopypanther'
__license__ = 'GPL'
__copyright__ = 'Copyright 2020 Goopypanther'
__version__ = '0.9'

import discord
import re
import requests
import json
import os
import pixivpy3
import io
from instalooter.looters import PostLooter
#instalooter needs a user agent to tell instagram, drop user-agent.txt into ~/.cache/instalooter/{version}/

#handle different ig links
def links(media, looter):
    if media.get('__typename') == "GraphSidecar":
        media = looter.get_post_info(media['shortcode'])
        nodes = [e['node'] for e in media['edge_sidecar_to_children']['edges']]
        return [n.get('video_url') or n.get('display_url') for n in nodes]
    elif media['is_video']:
        media = looter.get_post_info(media['shortcode'])
        return [media['video_url']]
    else:
        return [media['display_url']]


discord_token = os.environ["DISCORD_API_KEY"]
weasyl_headers = {'X-Weasyl-API-Key': os.environ["WEASYL_API_KEY"]}
pixiv_login = os.environ['PIXIV_LOGIN']
pixiv_password = os.environ['PIXIV_PASSWORD']

disable_command_pattern = re.compile('(<|\|\|)(?!@|#|:|a:).*(>|\|\|)')
fa_pattern = re.compile('(furaffinity\.net/(?:view|full)/(\d+))')
ws_pattern = re.compile('weasyl\.com\/~\w+\/submissions\/(\d+)')
wschar_pattern = re.compile('weasyl\.com\/character\/(\d+)')
da_pattern = re.compile('deviantart\.com.*.\d')
e621_pattern = re.compile('e621\.net\/post/show\/(\d+)')
pixiv_pattern = re.compile('pixiv.net\/.*artworks\/(\d*)')
pixiv_direct_img_pattern = re.compile('i\.pximg\.net\S*\w')
hf_pattern = re.compile('(hentai-foundry.com\/pictures\/user\/(\S*)\/(\d*)\/(\S*))')

faexport_url = "https://faexport.spangle.org.uk/submission/{}.json"
fapi_url = "https://bawk.space/fapi/submission/{}"
wsapi_url = "https://www.weasyl.com/api/submissions/{}/view"
wscharapi_url = "https://www.weasyl.com/api/characters/{}/view"
daapi_url = "https://backend.deviantart.com/oembed?url={}"
e621api_url = "https://e621.net/post/show.json?id={}"
hf_thumb_url = "https://thumbs.hentai-foundry.com/thumb.php?pid={}"

e621api_headers = {'User-Agent': 'saucebot-discord-v%s' % __version__}

help_message = "Hi! I\'m saucebot v%s, a discord bot that embeds images from art sites.\n" \
"If you would like to add me to your own server, click here: <https://discordapp.com/oauth2/authorize?client_id=284138973318742026&scope=bot>\n\n" \
"For more information you can join my support server: https://discord.gg/72NUrWU\n" \
"Or you can visit us on github to submit an issue or fork our code: <https://github.com/JeremyRuhland/saucebot-discord/>" % __version__


pixivapi = pixivpy3.AppPixivAPI()
pixivapi.login(pixiv_login, pixiv_password)

client = discord.Client()


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # DM Bot for help message
    if isinstance(message.channel, discord.DMChannel):
        await message.channel.send(help_message)
        return

    # Check for command to disable image previewing
    disable_command = disable_command_pattern.findall(message.content)
    if (disable_command):
        return

    fa_links = fa_pattern.findall(message.content)

    # Process each fa link
    for (fa_link, fa_id) in fa_links:
        # Request submission info
        fa_get = requests.get(faexport_url.format(fa_id))

        # Backup request
        if (fa_get.status_code is not 200):
            fa_get = requests.get(fapi_url.format(fa_id))

        # Check for success from API
        if not fa_get:
            continue

        fapi = json.loads(fa_get.text)

        # FA now embeds general submissions, skip in that case
        if fapi["rating"].lower() == "general":
            continue

        try:
            fapi_img = fapi["download"]
        except:
            fapi_img = fapi["image_url"]

        print(message.author.name + '#' + message.author.discriminator + '@' + message.guild.name + ':' + message.channel.name + ': ' + fapi_img)

        em = discord.Embed(
            title=fapi["title"])
        # discord api does not like it when embed urls are set?
        # it's not of critical importance as the original url will be near
        # em.url = fa_link

        try:
            fapi_author = fapi["author"]
        except:
            fapi_author = fapi["profile_name"]

        em.set_image(url=fapi_img)
        em.set_author(
            name=fapi_author,
    	    icon_url=fapi["avatar"])

        await message.channel.send(embed=em)


    ws_links = ws_pattern.findall(message.content)

    # Process each ws link
    for (ws_id) in ws_links:
        # Request submission info
        ws_get = requests.get(wsapi_url.format(ws_id), headers=weasyl_headers)

        # Check for success from API
        if not ws_get:
            continue

        wsapi = json.loads(ws_get.text)
        print(message.author.name + '#' + message.author.discriminator + '@' + message.guild.name + ':' + message.channel.name + ': ' + wsapi["media"]["submission"][0]["links"]["cover"][0]["url"])

        em = discord.Embed(
            title=wsapi["title"])

        # Discord didn't want to load the submission image, but the link worked
        em.set_image(url=wsapi["media"]["submission"][0]["links"]["cover"][0]["url"])
        em.set_author(
            name=wsapi["owner"],
            icon_url=wsapi["owner_media"]["avatar"][0]["url"])

        await message.channel.send(embed=em)


    wschar_links = wschar_pattern.findall(message.content)

    # Process each ws character page link
    for (wschar_id) in wschar_links:
        # Request submission info
        wschar_get = requests.get(wscharapi_url.format(wschar_id), headers=weasyl_headers)

        # Check for success from API
        if not wschar_get:
            continue

        wscharapi = json.loads(wschar_get.text)
        print(message.author.name + '#' + message.author.discriminator + '@' + message.guild.name + ':' + message.channel.name + ': ' + wscharapi["media"]["submission"][0]["links"]["cover"][0]["url"])

        em = discord.Embed(
            title=wscharapi["title"])

        # Discord didn't want to load the submission image, but the link worked
        em.set_image(url=wscharapi["media"]["submission"][0]["links"]["cover"][0]["url"])
        em.set_author(
            name=wscharapi["owner"],
            icon_url=wscharapi["owner_media"]["avatar"][0]["url"])

        await message.channel.send(embed=em)


    da_links = da_pattern.findall(message.content)

    # Process each da link
    for (da_id) in da_links:
        # Request submission info
        da_get = requests.get(daapi_url.format(da_id))

        # Check for success from API
        if not da_get:
            continue

        daapi = json.loads(da_get.text)
        print(message.author.name + '#' + message.author.discriminator + '@' + message.guild.name + ':' + message.channel.name + ': ' + daapi["url"])

        em = discord.Embed(
            title=daapi["title"])

        em.set_image(url=daapi["url"])
        em.set_author(
            name=daapi["author_name"],
            icon_url=em.Empty)

        await message.channel.send(embed=em)


    e621_links = e621_pattern.findall(message.content)

    # Process each e621 link
    for (e621_id) in e621_links:
        # Request submission info
        e621_get = requests.get(e621api_url.format(e621_id), headers=e621api_headers)

        # Check for success from API
        if not e621_get:
            continue

        e621api = json.loads(e621_get.text)
        print(message.author.name + '#' + message.author.discriminator + '@' + message.guild.name + ':' + message.channel.name + ': ' + e621api["file_url"])

        em = discord.Embed(
            title=e621api["artist"][0])

        em.set_image(url=e621api["file_url"])

        await message.channel.send(embed=em)


    pixiv_links = pixiv_pattern.findall(message.content)

    # Refresh oauth before using API
    if (pixiv_links) :
        pixivapi.auth()

        # Process each pixiv link
        for (pixiv_id) in pixiv_links:
            # Request submission info
            pixiv_result = pixivapi.illust_detail(pixiv_id)

            # Check for success from API
            if not 'illust' in pixiv_result:
                continue

            # Check for multi-image set
            if len(pixiv_result.illust.meta_pages) > 0:
                await message.channel.send('This is part of a {} image set.'.format(len(pixiv_result.illust.meta_pages)))

            pixiv_image_link = pixiv_result.illust.image_urls.large

            print(message.author.name + '#' + message.author.discriminator + '@' + message.guild.name + ':' + message.channel.name + ': ' + pixiv_image_link)

            async with message.channel.typing():
                pixiv_image_rsp = requests.get(pixiv_image_link, headers={'Referer': 'https://app-api.pixiv.net/'}, stream=True)

                pixiv_image_rsp_fp = io.BytesIO(pixiv_image_rsp.content)
                # Add file name to stream
                pixiv_image_rsp_fp.name = pixiv_image_link.rsplit('/', 1)[-1]

                await message.channel.send(file=discord.File(pixiv_image_rsp_fp))


    pixiv_direct_img_links = pixiv_direct_img_pattern.findall(message.content)

    # Process direct image links to pixiv, normally protected behind antihotlink filter
    if (pixiv_direct_img_links) :
        for url in pixiv_direct_img_links:
            url = 'https://' + url

            async with message.channel.typing():
                pixiv_image_rsp = requests.get(url, headers={'Referer': 'https://app-api.pixiv.net/'}, stream=True)

                print(message.author.name + '#' + message.author.discriminator + '@' + message.guild.name + ':' + message.channel.name + ': ' + url)

                pixiv_image_rsp_fp = io.BytesIO(pixiv_image_rsp.content)
                # Add file name to stream
                pixiv_image_rsp_fp.name = url.rsplit('/', 1)[-1]

                await message.channel.send(file=discord.File(pixiv_image_rsp_fp))


    hf_thumb_img_links = hf_pattern.findall(message.content)

    # Process thumbnails of image lnks on hentai-foundry
    if (hf_thumb_img_links) :
        for (hf_link, hf_user, hf_pid, hf_title) in hf_thumb_img_links:
            hf_link = "https://www." + hf_link

            print(message.author.name + '#' + message.author.discriminator + '@' + message.guild.name + ':' + message.channel.name + ': ' + hf_link)

            em = discord.Embed(title=hf_title)

            em.set_image(url=(hf_thumb_url.format(hf_pid)))
            em.set_author(name=hf_user, icon_url=em.Empty)

            await message.channel.send(embed=em)
            
    # process instagram links
    instaglam=re.compile('instagram\.com\/p\/[a-zA-Z0-9!$*\-_]+')
    iglinks=instaglam.findall(message.content)
    for x in iglinks:
        postid=x[16:]
        looter=None
        #is post id valid
        try:
            looter=PostLooter(postid)
        except:
            continue
        tex=''
        for media in looter.medias():
            for link in links(media, looter):
                tex+="{}\n".format(link)
        await message.channel.send(tex)
    


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print([x.name for x in client.guilds])
    print('%s servers' % len(client.guilds))
    print('------')

# Attempt to reconnect if we lose connection to discord, ie. one of these http requests took too long and we lost our auth.
# TODO: Figoure out how to use aiohttp and what to do about modules that use requests internally.
client.run(discord_token) # Connect to discord and begin client event functions
