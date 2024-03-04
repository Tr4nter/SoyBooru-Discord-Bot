import aiohttp
from bs4 import BeautifulSoup
from CONSTANTS import *

async def fetch_media(keyword: str, page: int) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_ADDRESS}/post/list/{keyword}/{page}") as resp:
            booruImagePage = await resp.text()

    soupObject = BeautifulSoup(booruImagePage, "lxml")

    mediaHolder = soupObject.find("div", {"class": "shm-image-list"})
    if not mediaHolder: return None

    attributeSlider = soupObject.find("div", {"class": "paginator sfoot"})
    maxPage = int(attributeSlider.find_all("a")[-1]["href"].split("/")[-1])

    if page > maxPage: page = maxPage

    mediaRefs = mediaHolder.find_all("a")

    mediaLinks = []
    for mediaRef in mediaRefs:
        media = mediaRef.find("img")
        mediaId = media["src"].split("/")[2]

        mediaLink = BASE_ADDRESS+"/_images/"+mediaId
        mediaLinkForEmbed = mediaLink+f".{mediaRef['data-mime'].split('/')[1]}"

        if mediaLinkForEmbed.split(".")[-1] in VIDEO_EXTENSIONS: continue # skip video formats due to discord not supporting putting videos in embed
        mediaLinks.append({"origin": BASE_ADDRESS+mediaRef["href"], "media": mediaLinkForEmbed, "media_tags": mediaRef["data-tags"]}) #discord embed requires extension at the end of the an url for the content to be displayed
    return {"mediaLinks": mediaLinks, "maxPage": maxPage}
