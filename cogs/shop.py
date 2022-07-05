import os
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
import motor.motor_asyncio
import nest_asyncio
import json
import random
import datetime

with open('./data.json') as f:
    d1 = json.load(f)
with open('./market.json', encoding='UTF-8') as f:
    d2 = json.load(f)

items = {}

for x, item in d2["Weapon"].items():
    i = {x: ["무기", item['price'], x]}
    items.update(i)

for x, item in d2["item"].items():
    i = {x: ["가챠", item['price'], x]}
    items.update(i)

nest_asyncio.apply()

mongo_url = d1['mongo']

cluster = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
ecomoney = cluster["eco"]["money"]
ecobag = cluster["eco"]["bag"]

def gotcha():
    # weights = (50 / 17, 40 / 17, 35 / 17, 30 / 17, 25 / 17, 20 / 17, 15 / 17, 10 / 17, 9 / 17, 8 / 17, 7 / 17, 6 / 17, 5 / 17, 4 / 17, 3 / 17, 3 / 17, 1 / 17)
    weights = (80, 20, 10, 5, 25, 20, 15, 10, 9, 8, 7, 6, 5, 4, 3, 3, 1)
    a = random.choices(list(d2["item"]), weights=weights)
    name = a[0]

    return name

def is_channel(channelId):
    def predicate(ctx):
        return ctx.message.channel.id == channelId
    return commands.check(predicate)

class Shop(commands.Cog):
    """ Commands related to market"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Shop Cog Loaded Succesfully")


    async def open_account(self, id : int):
        if id is not None:
            new_user = {"id": id, "wallet": 0, "bank": 100, "land": 0, "wage": 0, "inventory": [], "gm_time": datetime.datetime.now() - datetime.timedelta(days=1, hours=1)}
            # wallet = current money, bank = money in bank
            await ecomoney.insert_one(new_user)

    async def update_wallet(self, id : int, wallet : int):
        if id is not None:
            await ecomoney.update_one({"id": id}, {"$set": {"wallet": wallet}})

    async def update_bank(self, id : int, bank : int):
        if id is not None:
            await ecomoney.update_one({"id": id}, {"$set": {"bank": bank}})

    async def open_bag(self, id : int):
        if id is not None:
            newuser = {"id": id, "bag": []}
            await ecobag.insert_one(newuser)

    async def update_user(self, id : int):
        try:
            if id is not None:
                bal = await ecomoney.find_one({"id": id})
                if bal is None:
                    await self.open_account(id)

        except Exception as e:
            print(e)

    async def update_bag(self, id : int):
        try:
            if id is not None:
                bag = await ecobag.find_one({"id": id})
                if bag is None:
                    await self.open_bag(id)
        except:
            print('update bag error')

    @commands.group(aliases=["상점"], invoke_without_command=True)
    @cooldown(1, 2, BucketType.user)
    @is_channel(956377522549981216)
    async def mkt(self,ctx):
        """ 상점 (ko: !상점)"""
        embed = discord.Embed(
            timestamp=ctx.message.created_at,
            title="상점 목록",
            color=0xFF0000,
        )
        embed.add_field(
            name="무기",
            value="무기 상점 | 사용 `!상점 무기`",
            inline=False
        )
        embed.add_field(
            name="가챠",
            value="가챠 상점 | 사용 `!상점 가챠템`",
            inline=False
        )
        embed.set_footer(
        text=f"요청자 : {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
        )

        await ctx.send(embed=embed)

    @mkt.command(name="wp", aliases=["무기"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(956377522549981216)
    async def weapon(self,ctx):
        """ 무기 상점 """
        embed = discord.Embed(
            timestamp=ctx.message.created_at,
            title="무기 상점",
            color=0xFF0000,
        )
        for x, item in d2["Weapon"].items():
            embed.add_field(
                name= x,
                value=f"공격력: {item['att']} | 방어력: {item['def']} | 체력: {item['health']}\n가격: {item['price']} ZEN",
                inline=False
            )
        embed.set_footer(
            text=f"요청자 : {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
        )
        await ctx.send(embed=embed)

    @mkt.command(name="gatcha", aliases=["가챠템"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(956377522549981216)
    async def gatcha_(self,ctx):
        """ 가챠 상점 (ko: !가챠템)"""
        embed = discord.Embed(
            timestamp=ctx.message.created_at,
            title="가챠템 목록",
            color=0xFF0000,
        )
        for x, item in d2["item"].items():
            embed.add_field(
                name= x,
                value=f"공격력: {item['att']} | 방어력: {item['def']} | 체력: {item['health']}\n가격: {item['price']} ZEN",
                inline=False
            )
        embed.set_footer(
            text=f"요청자 : {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
        )
        await ctx.send(embed=embed)

    # function to add item in ecobag
    async def add_item(self, id : int, item : str, amount : int):
        if id is not None:
            await ecobag.update_one({"id": id}, {"$push": {"bag": [item, amount]}})
        
    # function to edit amount of item in ecobag
    async def edit_item(self, id : int, index : int, amount : int):
        if id is not None:
            await ecobag.update_one({"id": id}, {"$set": {f"bag.{index}.1": amount}})

    # function to remove item from ecobag
    async def remove_item(self, id : int, name : str, amount : int):
        if id is not None:
            await ecobag.update_one({"id": id}, {"$pull": {"bag": [name, amount]}})


    @commands.command(aliases=["b", "산다"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(956377522549981216)
    async def buy(self, ctx, item : str, amount : int = 1):
        """ 상점에서 물건을 구입한다. (ko: !산다)"""
        if amount <= 0 or amount > 100:
            await ctx.send("한번에 최소 1개에서 최대 100개 까지 구입 가능합니다.")
            return

        bal = await ecomoney.find_one({"id": ctx.author.id})
        if bal is None:
            await self.open_account(ctx.author.id)
            bal = await ecomoney.find_one({"id": ctx.author.id})

        bag = await ecobag.find_one({"id": ctx.author.id})
        if bag is None:
            await self.open_bag(ctx.author.id)
            bag = await ecobag.find_one({"id": ctx.author.id})

        fg = items.get(item)

        if fg is None or fg[0] != '무기':
            await ctx.send("취급하지 않는 물건입니다..")
            return

        price = fg[1] * amount
        name = fg[2]

        u_bal = bal["bank"]

        if u_bal < price:
            await ctx.send(f"은행에 충분한 ZEN이 없습니다. 총 가격은 {price} ZEN 입니다.")
            return

        await self.update_bank(ctx.author.id, u_bal - price)

        for x in bag['bag']:
            if x[0] == item:
                init_amount = x[1]
                final_amount = amount + init_amount
                index = bag['bag'].index(x)
                await self.edit_item(ctx.author.id, index, final_amount)
                await ctx.send(f"{name} {amount}개를 {price} ZEN에 구입하였습니다.")
                return

        await self.add_item(ctx.author.id, item, amount)
        await ctx.send(f"{name} {amount}개를 {price} ZEN에 구입하였습니다.")

    @commands.command(aliases=["s", "판다"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(956377522549981216)
    async def sell(self, ctx, item : str = None, amount : int = 1):
        """ 상점에 물건을 판매합니다. (ko: !판다) """
        if amount <= 0 or amount > 100:
            await ctx.send("최소 수량 1개, 최대 수량 100개 판매 가능합니다.")
            return
        bal = await ecomoney.find_one({"id": ctx.author.id})
        if bal is None:
            await self.open_account(ctx.author.id)
            bal = await ecomoney.find_one({"id": ctx.author.id})

        bag = await ecobag.find_one({"id": ctx.author.id})
        if bag is None:
            await self.open_bag(ctx.author.id)
            bag = await ecobag.find_one({"id": ctx.author.id})
        
        fg = items.get(item)

        if fg is None:
            await ctx.send("취급하지 않는 물건입니다.")
            return

        price = fg[1]
        name = fg[2]

        u_bal = bal["bank"]

        for x in bag['bag']:
            if x[0] == item:
                init_amount = x[1]
                if amount > init_amount:
                    await ctx.send("수량을 다시 확인해주세요")
                    return
                elif amount == init_amount:
                    if name == '만만한 Hope_Candy의 막대사탕':
                        price = int(round(price * init_amount * 0.1,0))
                    else:
                        price = int(round(price * init_amount * 0.7,0))
                    index = bag['bag'].index(x)
                    await self.remove_item(ctx.author.id, item, init_amount)
                    await self.update_bank(ctx.author.id, u_bal + price)
                    await ctx.send(f"{name} {amount}개를 {price} ZEN에 판매하였습니다.")
                    return
                else:
                    final_amount = init_amount - amount
                    price =  int(round(price * amount * 0.7,0))
                    index = bag['bag'].index(x)
                    await self.edit_item(ctx.author.id, index, final_amount)
                    await self.update_bank(ctx.author.id, u_bal + price)
                    await ctx.send(f"{name} {amount}개를 {price} ZEN에 판매하였습니다.")
                    return

        await ctx.send("없는 물건은 못 팝니다.")

    @commands.command(aliases=["가챠"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(956377522549981216)
    async def gatcha(self, ctx):
        """ 가챠 (ko: !가챠)"""

        bal = await ecomoney.find_one({"id": ctx.author.id})
        if bal is None:
            await self.open_account(ctx.author.id)
            bal = await ecomoney.find_one({"id": ctx.author.id})

        bag = await ecobag.find_one({"id": ctx.author.id})
        if bag is None:
            await self.open_bag(ctx.author.id)
            bag = await ecobag.find_one({"id": ctx.author.id})

        item = gotcha()
        fg = items.get(item)

        if fg is None or fg[0] != '가챠':
            await ctx.send("취급하지 않는 물건입니다..")
            return
        amount = 1
        price = fg[1] * amount
        name = fg[2]


        u_bal = bal["bank"]

        if u_bal < price:
            await ctx.send(f"은행에 충분한 ZEN이 없습니다. 총 가격은 {price} ZEN 입니다.")
            return

        await self.update_bank(ctx.author.id, u_bal - price)

        for x in bag['bag']:
            if x[0] == item:
                init_amount = x[1]
                final_amount = amount + init_amount
                index = bag['bag'].index(x)
                await self.edit_item(ctx.author.id, index, final_amount)
                await ctx.send(f"축하합니다. {name}를 뽑았습니다. 총 수량 : {final_amount}")
                return

        await self.add_item(ctx.author.id, item, amount)
        await ctx.send(f"축하합니다. {name}를 뽑았습니다. 총 수량 : 1")

    @commands.command(aliases=["i", "가방"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(956377522549981216)
    async def inventory(self, ctx, page : int = 1):
        """ 가방을 확인합니다. (ko: !가방)
        물건이 많으면 페이지 넘버를 입력해주세요
        {1 : "0-9", 2 : "10-20", 3 : "20-30", 4 : "30-40", 5 : "40-50"} - 페이지, 아이템 수량
        """
        if page > 5 or page < 1:
            await ctx.send("페이지는 1에서 5까지 입니다.")
            return
        bal = await ecomoney.find_one({"id": ctx.author.id})
        if bal is None:
            await self.open_account(ctx.author.id)
            bal = await ecomoney.find_one({"id": ctx.author.id})

        bag = await ecobag.find_one({"id": ctx.author.id})
        if bag is None:
            await self.open_bag(ctx.author.id)
            bag = await ecobag.find_one({"id": ctx.author.id})

        total = 0
        page_dict = {1 : "0-9", 2 : "10-20", 3 : "20-30", 4 : "30-40", 5 : "40-50"}
        intial, final = page_dict[page].split('-')
        for x in bag['bag']:
            total += 1
        if total == 0:
            await ctx.send("가방이 비어있습니다.")
            return
        
        page_items = bag['bag'][int(intial):int(final)+1]

        embed = discord.Embed(
            title=f"{ctx.author.name}의 가방",
            description=f"페이지 {page} | 아이템 개수: {total}",
            color=0xFF0000
            )
        for x in page_items:
            fg = items.get(x[0])
            embed.add_field(name=fg[2], value=f"{x[1]}", inline=False)

        embed.set_footer(
            text=f"요청자 : {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["item", "템"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(956377522549981216)
    async def infoitem(self, ctx, *, ss: str):
        """ 아이템 정보를 확인합니다. (ko: !템) """
        if ss in items.keys():
            iteminshop = items[ss]
        else:
            await ctx.send("없는 템 입니다.")
            return

        if iteminshop[0] == '무기':
            item = d2["Weapon"][ss]
        elif iteminshop[0] == '가챠':
            item = d2["item"][ss]
        else:
            await ctx.send("없는 템 입니다.")
            return

        stats = f'공격력: {item["att"]}\n방어력: {item["def"]}\nHP: {item["health"]}\n'
        upProbability = item["강화확률"]
        upPrice = item["강화비용"]

        embed = discord.Embed(
            title=f'{ss}',
            color=discord.Color.gold()
        )

        embed.set_thumbnail(url=item["image"])
        embed.add_field(name="Stats", value=stats, inline=False)
        embed.add_field(name="강화확률", value=upProbability, inline=True)
        embed.add_field(name="강화비용", value=upPrice, inline=True)
        await ctx.send(embed=embed)

    @commands.command(aliases=["up", "강화"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(956377522549981216)
    async def upgrade(self, ctx, *, ss: str):
        """ 아이템 정보를 확인합니다. (ko: !템) """
        if ss in items.keys():
            iteminshop = items[ss]
        else:
            await ctx.send("존재하지 않는 템 입니다.")
            return

        if iteminshop[0] == '무기':
            item = d2["Weapon"][ss]
        elif iteminshop[0] == '가챠':
            item = d2["item"][ss]
        else:
            await ctx.send("존재하지 않는 템 입니다.")
            return

        stats = f'공격력: {item["att"]}\n방어력: {item["def"]}\nHP: {item["health"]}\n'
        upProbability = item["강화확률"]
        upPrice = item["강화비용"]

        embed = discord.Embed(
            title=f'{ss}',
            color=discord.Color.gold()
        )

        embed.set_thumbnail(url=item["image"])
        embed.add_field(name="Stats", value=stats, inline=False)
        embed.add_field(name="강화확률", value=upProbability, inline=True)
        embed.add_field(name="강화비용", value=upPrice, inline=True)
        await ctx.send(embed=embed)

    # leaderboard
    @commands.command(aliases=["lb"])
    @cooldown(1, 2, BucketType.user)
    async def leaderboard(self, ctx):
        """ Checkout the leaderboard."""

        rankings = ecomoney.find().sort("bank", -1)

        i = 1

        embed = discord.Embed(
            title=f"{ctx.guild.name}'s Leaderboard",
            description=f"\u200b",
            color=0xFF0000
            )

        async for x in rankings:
            try:
                temp = ctx.guild.get_member(x["id"])
                tb = x["bank"]
                embed.add_field(
                    name=f"{i} : {temp.name}", value=f"Money: ${tb}", inline=False
                )
                i += 1
            except:
                pass
            if i == 11:
                break


        embed.set_footer(
            text=f"Requested By: {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
        )
        await ctx.send(embed=embed)
        

def setup(bot):
    bot.add_cog(Shop(bot))