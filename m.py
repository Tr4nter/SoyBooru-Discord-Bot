import discord
from discord.ext import commands, tasks
from discord import app_commands

import aiohttp
import httpx
from bs4 import BeautifulSoup, SoupStrainer

import typing
import configparser

from navigator import Navigator
from CONSTANTS import *
from fetcher import fetch_media

#fix for bs4 errors https://stackoverflow.com/questions/69515086/error-attributeerror-collections-has-no-attribute-callable-using-beautifu
import collections
collections.Callable = collections.abc.Callable

class Bot(commands.Bot):
    def __init__(self):
        intents =  discord.Intents.all()
        self.tags = {}
        
        super().__init__(command_prefix="t.", intents=intents)

    @tasks.loop(minutes=30)
    async def looper(self):
        await self.fetch_tags()
        

    async def fetch_tags(self):
        tagSite = httpx.get(f"{BASE_ADDRESS}/tags").text
        tagSoup = BeautifulSoup(tagSite, 'lxml')
        tagSection = tagSoup.find("section", {"id": "Tagsmain"})
        tagDiv = tagSection.find("div", {"class": "navside tab"})

        for tag in tagDiv.find_all("a"):
            tagText = tag.getText().replace(" ", "_")

            if self.tags.get(tagText): continue
            self.tags[tagText] = 0 # dict lookup is faster then checking if entry is in list ( maybe )


    async def setup_hook(self):
        await self.tree.sync(guild=discord.Object(id = GUILD_SYNC_ID))
        await self.fetch_tags()
        

    async def on_command_error(self, context: commands.Context, exception: commands.CommandError) -> None:
        await context.reply(exception, ephemeral=True)

        
    async def on_ready(self):
        await bot.change_presence(activity=discord.CustomActivity(name=f"Prefix: {self.command_prefix}"))
        self.looper.start()

        
bot = Bot()

@bot.event
async def on_message(message: discord.Message):
    mentions = message.mentions
    if len(mentions) >= MENTION_THRESHOLD:
        author = message.author
        role = message.guild.get_role(RETARDROLE_ID)
        await bot.add_roles(author, role)
        await message.channel.send(f"Muted {author.mention} for mass-mentions.")
    await bot.process_commands(message)


@bot.hybrid_command(name="booru", with_app_command=True, description="Lookup booru.soy images")
@app_commands.guilds(discord.Object(id = GUILD_SYNC_ID))
async def booru(ctx: commands.Context, keyword: str, page: int = 1) -> None:
    await ctx.defer()
    message = await ctx.reply(f"*Fetching medias for {keyword}...*")
    mediaData = await fetch_media(keyword, page)
    if not mediaData: await ctx.reply(f"Unable to find medias for keyword: *{keyword}*"); return

    mediaLinks = mediaData["mediaLinks"]
    maxPage = mediaData["maxPage"]

    await Navigator(ctx, mediaLinks, maxPage, keyword).send(message)


@booru.autocomplete("keyword")
async def keyword_autocomplete(
    interaction: discord.Interaction, 
    current: str
) -> typing.List[app_commands.Choice[str]]:
    
    options = []
    for word in bot.tags:
        if not current in word: continue
        options.append(app_commands.Choice(name=word, value=word))
    return options[:25] # discord only supports up to 25 options at once, any more and it wont show any

Config = configparser.ConfigParser()
Config.read("config.ini")

TOKEN = Config.get("MAIN", "TOKEN")

bot.run(TOKEN)
