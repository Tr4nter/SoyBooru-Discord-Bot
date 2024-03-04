import discord
from discord.ext import commands, tasks
from discord import app_commands

import aiohttp
from bs4 import BeautifulSoup, SoupStrainer

import typing
import configparser
import traceback
import time

from core.navigator import Navigator
from core.fetcher import fetch_media
from core.Trie import Trie
from core.CONSTANTS import *

#fix for bs4 errors https://stackoverflow.com/questions/69515086/error-attributeerror-collections-has-no-attribute-callable-using-beautifu
import collections
collections.Callable = collections.abc.Callable

Config = configparser.ConfigParser()
Config.read("config.ini")

GUILD_SYNC_ID = int(Config.get("MAIN", "GUILD_SYNC_ID"))

class Bot(commands.Bot):
    def __init__(self):
        intents =  discord.Intents.all()

        self.tags = Trie()
        self.lastTagFetch = time.time()

        self.frontFacingTags = [] # tags to show when keyword box is empty
        
        super().__init__(command_prefix="t.", intents=intents)


    @tasks.loop(minutes=30)
    async def looper(self):
        if (time.time())-self.lastTagFetch >= 30*60:
            await self.fetch_tags()
        

    async def fetch_tags(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_ADDRESS}/tags") as resp:
                tagSite = await resp.text()
        try:
            tagSoup = BeautifulSoup(tagSite, 'lxml')
            tagSection = tagSoup.find("section", {"id": "Tagsmain"})
            tagDiv = tagSection.find("div", {"class": "navside tab"})
            tags = tagDiv.find_all("a")
        except AttributeError: return self.fetch_tags()

        for tag in tags:
            tagText = tag.getText().replace(" ", "_")

            self.tags.insert(tagText)

            if len(self.frontFacingTags) < 25:
                self.frontFacingTags.append(tagText)
        self.lastTagFetch = time.time()


    async def setup_hook(self):
        await self.tree.sync(guild=discord.Object(id = GUILD_SYNC_ID))
        await self.fetch_tags()
        

    async def on_command_error(self, context: commands.Context, exception: commands.CommandError) -> None:
        await context.reply(exception, ephemeral=True)

        
    async def on_ready(self):
        await bot.change_presence(activity=discord.CustomActivity(name=f"Prefix: {self.command_prefix}"))
        print("bot is ready")
        self.looper.start()

        
bot = Bot()


@bot.hybrid_command(name="booru", with_app_command=True, description="Lookup booru.soy images")
@app_commands.guilds(discord.Object(id = GUILD_SYNC_ID))
async def booru(ctx: commands.Context, keyword: str, page: int = 1) -> None:
    await ctx.defer()
    message = await ctx.reply(f"*Fetching medias for {keyword}...*")
    try:
        mediaData = await fetch_media(keyword, page)
    except Exception as e: print(e)
    if not mediaData: await ctx.reply(f"Unable to find medias for keyword: *{keyword}*"); return

    mediaLinks = mediaData["mediaLinks"]
    maxPage = mediaData["maxPage"]

    await Navigator(ctx, mediaLinks, page, maxPage, keyword).send(message)


# Sometimes this doesn't work, couldnt figure out why, could be ratelimits?
@booru.autocomplete("keyword")
async def keyword_autocomplete(
    interaction: discord.Interaction, 
    current: str
) -> typing.List[app_commands.Choice[str]]:
    
    options = []
    if len(current) <= 0: return [app_commands.Choice(name=word, value=word) for word in bot.frontFacingTags]
    try:
        for word in (await bot.tags.search_autocompletion(current, interaction)): 
            options.append(app_commands.Choice(name=word, value=word))
            if len(options) >= 25: break # discord only supports up to 25 options at once, any more and it wont show any
        return options[:25]
    except Exception as e: print(traceback.format_exc())

if __name__ == "__main__":
    bot.run(Config.get("MAIN", "TOKEN"))

