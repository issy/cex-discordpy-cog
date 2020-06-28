import asyncio
import json
import aiosqlite
import aiohttp
import discord
from discord.ext import commands
import time
import urllib.parse
import re

class CexSearch(commands.Cog):

    def __init__(self, client):
        self.client = client
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
    async def cexSearch(self, searchTerm):
        cleanSearchTerm = urllib.parse.quote(searchTerm) # clean up the search term for the url
        for i in range(0,3):
            async with aiohttp.ClientSession() as session:
                try:
                    data = await session.get(f'https://wss2.cex.uk.webuy.io/v3/boxes?q={cleanSearchTerm}&firstRecord=1&count=50&sortOrder=desc')
                except ClientConnectorError as dnsIssue:
                    time.sleep(3) # if connection issue occurs, sleep for 3 seconds
                    continue
            products = await data.json()
            products = products['response']['data']
            return products

    # Make embed from search data
    async def makeCexEmbed(self, searchObject, index):
        embed = discord.Embed(colour=discord.Colour(self.cexRed), url="https://uk.webuy.com/product-detail/?id="+searchObject[self.D['bI']])
        embed.set_author(name=searchObject[self.D['bN']], url="https://uk.webuy.com/product-detail/?id="+searchObject[self.D['bI']], icon_url=self.cexLogo)
        embed.set_thumbnail(url=searchObject['imageUrls']['large'].replace(" ", "%20")) # cleans up the URL
        embed.add_field(name="Category", value=searchObject[self.D['cFN']], inline=False)
        embed.add_field(name="WeSell for", value=f"£{searchObject[self.D['sP']]}", inline=True)
        embed.add_field(name="WeBuy for Voucher", value=f"£{searchObject[self.D['eP']]}", inline=True)
        embed.add_field(name="WeBuy for Cash", value=f"£{searchObject[self.D['cP']]}", inline=True)
        if searchObject[self.D['oOES']] == 1: # if it's out of stock
            embed.add_field(name="In Stock", value=False, inline=True)
        else:
            embed.add_field(name="Stock", value=searchObject[self.D['eQOH']], inline=True)
        if searchObject[self.D['bR']] == None:
            embed.add_field(text="Rating",value='None',inline=True)
        else:
            embed.add_field(text="Rating",value=searchObject[self.D['bR']],inline=True)
        embed.set_footer(text=f"{index['current']+1} of {index['max']+1}", icon_url=self.cexLogo)
        return embed

    # Search command
    @commands.command()
    async def search(self, ctx, *arg):
        """Searches the Cex website"""
        indexReg = re.compile("r=[0-9]+")
        if indexReg.match(arg.split(' ')[-1]):
            match = indexReg.match(arg.split(' ')[-1])
            index = int(match.group(1))
        else:
            index = 0
        # Fetch search data
        cexSearch = await self.cexSearch(arg)
        if cexSearch is None: # If no results found for that search term
            embed = discord.Embed(colour=self.cexRed, description="No products found for `{}`".format(arg.replace('`','``')), title=f"No results 🙁")
            await ctx.send(embed=embed)
            return
        else:
            cexSearch = cexSearch['boxes']
        try:
            cexSearch[index]
        except IndexError:
            index = len(cexSearch)-1
        minIndex = 0
        maxIndex = len(cexSearch)-1
        cexEmbed = await self.makeCexEmbed(cexSearch[index])
        messageObject = await ctx.send(embed=cexEmbed) # Send a result
        emojis = ['◀','▶']
        if (len(cexSearch) == 1) and (index == maxIndex == minIndex): # If this is the only result, no pagination is required
            allowedEmojis = []
            await ctx.send(embed=cexEmbed)
            return
        if (index == 0) and (len(cexSearch) > 1): # if this is the first result, no back arrow is required
            await messageObject.add_reaction('▶')
            allowedEmojis = ['▶']
        if (index != minIndex) and (index != maxIndex): # if it's not the first/last result
            allowedEmojis = emojis
            for emoji in emojis:
                await messageObject.add_reaction(emoji) # add forwards AND backwards emojis
        if (index != minIndex) and (index == maxIndex): # if it's the last result, only add back arrow
            await messageObject.add_reaction('◀')
            allowedEmojis = ['◀']
        async def editResult(cexSearch, index, messageObject):
            cexEmbed = await self.makeCexEmbed(cexSearch[index])
            await messageObject.edit(embed=cexEmbed)
            emojis = ['◀','▶']
            if (len(cexSearch) == 1) and (index == maxIndex == minIndex): # If this is the only result, no pagination is required
                allowedEmojis = []
                await ctx.send(embed=cexEmbed)
                return
            if (index == 0) and (len(cexSearch) > 1): # if this is the first result, no back arrow is required
                await messageObject.add_reaction('▶')
                allowedEmojis = ['▶']
            if (index != minIndex) and (index != maxIndex): # if it's not the first/last result
                for emoji in emojis:
                    await messageObject.add_reaction(emoji) # add forwards AND backwards emojis
                    allowedEmojis = emojis
            if (index != minIndex) and (index == maxIndex): # if it's the last result, only add back arrow
                await messageObject.add_reaction('◀')
                allowedEmojis = ['◀']
            def reaction_info_check(reaction, user):
                return user == ctx.author and reaction.message.id == messageObject.id
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=reaction_info_check)
            except asyncio.TimeoutError:
                await messageObject.clear_reactions() # clear reactions on bot message
                return
            else:
                # Okay, the user has reacted with an emoji, let us find out which one!
                if reaction.emoji in allowedEmojis:
                    if reaction.emoji == '▶':
                        index = index + 1
                        await messageObject.clear_reactions() # clear reactions on bot message
                        await editResult(cexSearch, index, messageObject)
                    if reaction.emoji == '◀':
                        index = index - 1
                        await messageObject.clear_reactions() # clear reactions on bot message
                        await editResult(cexSearch, index, messageObject)
        def reaction_info_check(reaction, user):
            return user == ctx.author and reaction.message.id == messageObject.id
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=reaction_info_check)
        except asyncio.TimeoutError:
            await messageObject.clear_reactions() # clear reactions on bot message
            return
        else:
            # Okay, the user has reacted with an emoji, let us find out which one!
            if reaction.emoji in allowedEmojis:
                if reaction.emoji == '▶':
                    index = index + 1
                    #await editResult(cexSearch, index)
                    await messageObject.clear_reactions() # clear reactions on bot message
                    await editResult(cexSearch, index, messageObject)
                if reaction.emoji == '◀':
                    index = index - 1
                    await messageObject.clear_reactions() # clear reactions on bot message
                    await editResult(cexSearch, index, messageObject)

def setup(client):
    client.add_cog(CexSearch(client))
