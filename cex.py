import asyncio
import json
import aiosqlite
import aiohttp
import discord
from discord.ext import commands
import time
import urllib.parse


# cleanSearchTerm = urllib.parse.quote(searchTerm) # clean up the search term for the url

class Cex(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.config = json.load(open('config.json', 'r'))
        self.cexRed = 0xff0000
        self.cexLogo = 'https://uk.webuy.com/_nuxt/74714aa39f40304c8fac8e7520cc0a35.png'
        # Search item aliases
        self.D = {
            'bI'    :   'boxId',
            'bN'    :   'boxName',
            'iMB'   :   'isMasterBox',
            'cI'    :   'categoryId',
            'cN'    :   'categoryName',
            'cFN'   :   'categoryFriendlyName',
            'sCI'   :   'superCatId',
            'sCN'   :   'superCatName',
            'sCFN'  :   'superCatFriendlyName',
            'cB'    :   'cannotBuy',
            'iNB'   :   'isNewBox',
            'sP'    :   'sellPrice',
            'cP'    :   'cashPrice',
            'eP'    :   'exchangePrice',
            'bR'    :   'boxRating',
            'oOS'   :   'outOfStock',
            'oOES'  :   'outOfEcomStock',
            'eQOH'  :   'ecomQuantityOnHand'
        }

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Cex cog online')

    # Retrieve search data
    async def cexSearch(self, arg):
        for i in range(0,3):
            async with aiohttp.ClientSession() as session:
                try:
                    data = await session.get(f'https://wss2.cex.uk.webuy.io/v3/boxes?q={arg}&firstRecord=1&count=50&sortOrder=desc')
                except ClientConnectorError as dnsIssue:
                    time.sleep(3) # if connection issue occurs, sleep for 3 seconds
                    continue
            product = await data.json()
            product = product['response']['data']
            searchObject = product
            return searchObject

    # Make embed from search data
    async def makeCexEmbed(self, searchObject):
        embed = discord.Embed(colour=discord.Colour(self.cexRed), url="https://uk.webuy.com/product-detail/?id="+searchObject[self.D['bI']])
        embed.set_author(name=searchObject[self.D['bN']], url="https://uk.webuy.com/product-detail/?id="+searchObject[self.D['bI']], icon_url=self.cexLogo)
        embed.set_thumbnail(url=searchObject['imageUrls']['large'].replace(" ", "%20")) # cleans up the URL
        embed.add_field(name="Category", value=searchObject[self.D['cFN']], inline=True)
        embed.add_field(name="WeSell for", value=f"", inline=True)
        embed.add_field(name="WeBuy for Voucher", value=f'£{eP}\n\(£{veP} @ 85%\)', inline=True)
        embed.add_field(name="WeBuy for Cash", value=f'£{cP}', inline=True)
        if searchObject[self.D['oOES']] == 1: # if it's out of stock
            embed.add_field(name="In Stock", value=False, inline=True)
        else:
            embed.add_field(name="Stock", value=searchObject[self.D['eQOH']], inline=True)
        embed.add_field(name="ID", value=str(searchObject[self.D['bI']]), inline=True)
        embed.set_footer(text="cexxy cex bot", icon_url=self.cexLogo)
        return embed



def setup(client):
    client.add_cog(Cex(client))
