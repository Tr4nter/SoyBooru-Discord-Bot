import discord
from discord.ext import commands
import typing
from fetcher import fetch_media


class Navigator(discord.ui.View):
    def __init__(self, context: commands.Context, medias: typing.List[str], maxPage: int, keyword: str):
        self.context = context

        self.keyword = keyword
        self.medias = medias
        self.maxPage = maxPage

        self.currentIndex = 0
        self.currentPage = 0
        self.sent = False

        self._currentMessage = None
        super().__init__(timeout=600)

        
    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user == self.context.author: await interaction.response.defer(); return False
        return True

    
    async def send(self, messageToEdit: discord.Message):
        if self.sent: return
        self.sent = True

        self._currentMessage = await messageToEdit.edit(view=self, embed=await self._make_embed(), content=None)

        
    async def _make_embed(self):
        embed = discord.Embed()    
        currentMediaData = self.medias[self.currentIndex]
        embed.set_image(url=currentMediaData["media"])
        embed.description =  currentMediaData["origin"]+"\n"+currentMediaData["media_tags"]
        embed.title = f"Media: {self.currentIndex+1}/{len(self.medias)}\nPage: {self.currentPage+1}/{self.maxPage}"
        return embed


    async def _edit(self, interaction: discord.Interaction):
        newMessage = await self._currentMessage.edit(view=self, embed=await self._make_embed())
        await interaction.response.defer()
        return newMessage


    async def _mediaNavigationHandler(self, interaction: discord.Interaction) -> discord.Message:
        if self.currentIndex < 0: 
            self.currentIndex = self.currentIndex = len(self.medias)-1
        else:
            if self.currentIndex == len(self.medias): self.currentIndex = 0
        return (await self._edit(interaction))


    async def _pageNavigationHandler(self, interaction: discord.Interaction) -> discord.Message:
        if self.currentPage < 0: 
            self.currentPage = self.maxPage-1
        elif self.currentPage == self.maxPage:
            self.currentPage = 0

        self.currentIndex = 0
        self.medias = (await fetch_media(self.keyword, self.currentPage+1))["mediaLinks"]
        return (await self._edit(interaction))


    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.blurple)
    async def previous_page(self, interaction: discord.Interaction, button: discord.Button):
        self.currentPage -= 1
        self._currentMessage = await self._pageNavigationHandler(interaction)
    

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous_media(self, interaction: discord.Interaction, button: discord.Button):
        
        self.currentIndex -= 1
        self._currentMessage = await self._mediaNavigationHandler(interaction)


    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next_media(self, interaction: discord.Interaction, button: discord.Button):

        self.currentIndex += 1
        self._currentMessage = await self._mediaNavigationHandler(interaction)


    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.Button):
        self.currentPage += 1
        self._currentMessage = await self._pageNavigationHandler(interaction)
