import asyncio
import json
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
        self.cexEmoji = client.get_emoji(702111065953271848)
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
        print('Cex search cog online')

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
        """Searches the CeX website"""
        index = {}
        indexReg = re.compile("r=[0-9]+")
        if indexReg.match(arg[-1]):
            match = indexReg.match(arg[-1])
            index['current'] = int(match.group(1))
            arg = arg[:-1]
        else:
            index['current'] = 0
        arg = " ".join(arg)

        cexSearch = await self.cexSearch(arg)

        if cexSearch is None: # No results for that search term
            await self.noResults(ctx, arg)
            return
        else:
            cexSearch = cexSearch['boxes']

        if len(cexSearch) == 1: # Only one result
            index = {'min':0,'current':0,'max':0}
            cexEmbed = await self.makeCexEmbed(cexSearch,index)
            await ctx.send(embed=embed)
            return
        
        try: # Check that the current index, if modified, is within range
            cexSearch[index['current']]
        except IndexError:
            index['current'] = len(cxSearch) - 1

        index = {'min':0,
                'current':index['current'],
                'max':len(cexSearch)-1}

        cexEmbed = await self.makeCexEmbed(cexSearch[index], index)
        messageObject = await ctx.send(embed=cexEmbed) # send a result
        allowedEmojis = await self.addButtons(messageObject, index) # add buttons and get allowedEmojis
        def reaction_info_check(reaction, user):
            return user == ctx.author and reaction.message.id == messageObject.id
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=120.0, check=reaction_info_check)
        except asyncio.TimeoutError:
            await messageObject.clear_reactions()
            return
        else:
            # User has reacted with an emoji, find out which one
            if reaction.emoji in allowedEmojis:
                if reaction.emoji == '▶':
                    index['current'] = index['current'] + 1
                    await self.editResult(ctx, cexSearch, index, messageObject)
                if reaction.emoji == '◀':
                    index['current'] = index['current'] - 1
                    await self.editResult(ctx, cexSearch, index, messageObject)

    async def editResult(self, ctx, cexSearch, index, messageObject)
        await messageObject.clear_reactions()
        cexEmbed = await.self.makeCexEmbed(cexsearch[index], index)
        await messageObject.edit(embed=cexEmbed)
        allowedEmojis = await self.addButtons(messageObject, index) # add buttons and get allowedEmojis
        def reaction_info_check(reaction, user):
            return user == ctx.author and reaction.message.id == messageObject.id
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=120.0, check=reaction_info_check)
        except asyncio.TimeoutError:
            await messageObject.clear_reactions()
            return
        else:
            # User has reacted with an emoji, find out which one
            if reaction.emoji in allowedEmojis:
                if reaction.emoji == '▶':
                    index['current'] = index['current'] + 1
                    await self.editResult(ctx, cexSearch, index, messageObject)
                if reaction.emoji == '◀':
                    index['current'] = index['current'] - 1
                    await self.editResult(ctx, cexSearch, index, messageObject)



    async def noResults(self, ctx, arg):
        embed = discord.Embed(colour=self.cexRed, description="No products found for `{}`".format(arg.replace('`','``')), title=f"No results 🙁")
        await ctx.send(embed=embed)
        return

    async def addButtons(self, messageObject, index):
        if index['current'] == index['min']: # first result, no back arrow required
            allowedEmojis = ['▶']
        if index['current'] == index['max']: # last result, no forward arrow required
            allowedEmojis = ['◀']
        if index['min'] < index['current'] < index['max']: # a middle result, both arrows required
            allowedEmojis = ['◀','▶']
        for emoji in allowedEmojis:
            await messageObject.add_reaction(emoji)
        return allowedEmojis

    # Old search command
    @commands.command()
    async def searchold(self, ctx, *arg):
        """Searches the Cex website"""
        print(arg)
        index = {}
        indexReg = re.compile("r=[0-9]+")
        if indexReg.match(arg[-1]):
            match = indexReg.match(arg[-1])
            index['current'] = int(match.group(1))
            arg = arg[:-1]
        else:
            index['current'] = 0
        # Fetch search data
        arg = " ".join(arg)
        cexSearch = await self.cexSearch(arg)
        if cexSearch is None: # If no results found for that search term
            embed = discord.Embed(colour=self.cexRed, description="No products found for `{}`".format(arg.replace('`','``')), title=f"No results 🙁")
            await ctx.send(embed=embed)
            return
        else:
            cexSearch = cexSearch['boxes']

        index['min'] = 0
        index['max'] = len(cexSearch)-1
        if index['current'] < 0:
            index['current'] = 0
        elif index['current'] > index['max']:
            index['current'] = index['max']
        # try:
        #     cexSearch[index['current']]
        # except IndexError:
        #     index['current'] = len(cexSearch)-1
        cexEmbed = await self.makeCexEmbed(cexSearch[index])
        messageObject = await ctx.send(embed=cexEmbed) # Send a result
        emojis = ['◀','▶']
        if (len(cexSearch) == 1) and (index['current'] == index['max'] == index['min']): # If this is the only result, no pagination is required
            allowedEmojis = []
            await ctx.send(embed=cexEmbed)
            return
        if (index['current'] == 0) and (len(cexSearch) > 1): # if this is the first result, no back arrow is required
            await messageObject.add_reaction('▶')
            allowedEmojis = ['▶']
        if (index['current'] != index['min']) and (index['current'] != index['max']): # if it's not the first/last result
            allowedEmojis = emojis
            for emoji in emojis:
                await messageObject.add_reaction(emoji) # add forwards AND backwards emojis
        if (index['current'] != index['min']) and (index['current'] == index['max']): # if it's the last result, only add back arrow
            await messageObject.add_reaction('◀')
            allowedEmojis = ['◀']
        async def editResult(cexSearch, index, messageObject):
            cexEmbed = await self.makeCexEmbed(cexSearch[index])
            await messageObject.edit(embed=cexEmbed)
            emojis = ['◀','▶']
            if (len(cexSearch) == 1) and (index['current'] == index['max'] == index['min']): # If this is the only result, no pagination is required
                allowedEmojis = []
                await ctx.send(embed=cexEmbed)
                return
            if (index['current'] == 0) and (len(cexSearch) > 1): # if this is the first result, no back arrow is required
                await messageObject.add_reaction('▶')
                allowedEmojis = ['▶']
            if (index['current'] != index['min']) and (index['current'] != index['max']): # if it's not the first/last result
                for emoji in emojis:
                    await messageObject.add_reaction(emoji) # add forwards AND backwards emojis
                    allowedEmojis = emojis
            if (index['current'] != index['min']) and (index['current'] == index['max']): # if it's the last result, only add back arrow
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
                        index['current'] = index['current'] + 1
                        await messageObject.clear_reactions() # clear reactions on bot message
                        await editResult(cexSearch, index, messageObject)
                    if reaction.emoji == '◀':
                        index['current'] = index['current'] - 1
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
                    index['current'] = index['current'] + 1
                    #await editResult(cexSearch, index)
                    await messageObject.clear_reactions() # clear reactions on bot message
                    await editResult(cexSearch, index, messageObject)
                if reaction.emoji == '◀':
                    index['current'] = index['current'] - 1
                    await messageObject.clear_reactions() # clear reactions on bot message
                    await editResult(cexSearch, index, messageObject)



def setup(client):
    client.add_cog(CexSearch(client))
