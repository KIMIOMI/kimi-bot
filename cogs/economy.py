import os
import discord
import psutil
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
import motor.motor_asyncio
import nest_asyncio
import json
import random

with open('./data.json') as f:
    d1 = json.load(f)
with open('./market.json') as f:
    d2 = json.load(f)

land = d2["Land"]

# print(land)

nest_asyncio.apply()

mongo_url = d1['mongo']

cluster = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
ecomoney = cluster["eco"]["money"]

class Economy(commands.Cog):
    """ Commands related to economy"""
    def __init__(self, bot):
        self.bot = bot
        self.key = ["id", "wllet", "bank", "land", "wage", "inventory"]

    @commands.Cog.listener()
    async def on_ready(self):
        print("Eco Cog Loaded Succesfully")

    async def open_account(self, id : int):
            new_user = {"id": id, "wallet": 0, "bank": 100, "land": 0, "wage": 0, "inventory": []}
            # wallet = current money, bank = money in bank
            await ecomoney.insert_one(new_user)

    async def update_wallet(self, id : int, wallet : int):
        if id is not None:
            await ecomoney.update_one({"id": id}, {"$set": {"wallet": wallet}})

    async def update_bank(self, id : int, bank : int):
        if id is not None:
            await ecomoney.update_one({"id": id}, {"$set": {"bank": bank}})

    async def add_wallet(self, id : int, amount : int):
        if id is not None:
            await ecomoney.update_one({"id": id}, {"$inc": {"wallet": amount}})

    async def add_land(self, id : int, amount : int):
        if id is not None:
            await ecomoney.update_one({"id": id}, {"$inc": {"wallet": amount}})

    async def update_user(self, id : int):
        try:
            if id is not None:
                bal = await ecomoney.find_one({"id": id})
                if bal is None:
                    await self.open_account(id)
                for key in self.key:
                    if key in bal:
                        pass
                    else:
                        a = lambda key: 100 if key == "bank" else 0
                        await ecomoney.update_one({"id": id}, {"$set": {key : a(key)}})
        except Exception as e:
            print(e)

    @commands.command(aliases=["bal", "자산"])
    @cooldown(1, 2, BucketType.user)
    async def balance(self, ctx, user: discord.Member = None):
        """ 당신의 자산을 확인합니다.(ko: !자산) """
        if user is None:
            user = ctx.author
        try:
            await self.update_user(user.id)
            bal = await ecomoney.find_one({"id": user.id})
            embed = discord.Embed(
                timestamp=ctx.message.created_at,
                title=f"{user.name}의 재산",
                color=0xFF0000,
            )
            embed.add_field(
                name="영토",
                value=f"{bal['land']}\U000033A5",
            )
            embed.add_field(
                name="봇짐",
                value=f"{bal['wallet']} ZEN",
            )
            embed.add_field(
                name="은행",
                value=f"{bal['bank']} ZEN",
            )
            embed.set_footer(
                text=f"요청자: {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
            )
            embed.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send('취..익 취이..ㄱ')

    @commands.command(aliases=["wd", "인출"])
    @cooldown(1, 2, BucketType.user)
    async def withdraw(self, ctx, amount: int):
        # """ Withdraw money from your bank(ko : !자산)"""
        """ 은행에서 돈을 인출합니다.(ko : !인출)"""
        user = ctx.author
        try:
            await self.update_user(user.id)
            bal = await ecomoney.find_one({"id": user.id})
            if amount > bal['bank']:
                await ctx.send('은행에 잔고가 부족합니다.')
            elif amount <= 0:
                await ctx.send('최소 인출액을 확인해주세요.')
            else:
                await ecomoney.update_one({"id": user.id}, {"$inc": {"wallet": +amount, "bank": -amount}})
                await ctx.send(f'당신의 은행에서 {amount} ZEN이 인출되었습니다.')
        except Exception:
            await ctx.send('취..익 취이..ㄱ')

    @commands.command(aliases=["dp", "입금"])
    @cooldown(1, 2, BucketType.user)
    async def deposit(self, ctx, amount: int):
        # """ Deposit money to your bank(ko : !입금)"""
        """ 은행에 돈을 입급합니다. (ko : !입금)"""
        user = ctx.author
        try:
            await self.update_user(user.id)
            bal = await ecomoney.find_one({"id": user.id})
            if amount > bal['wallet']:
                await ctx.send('잔액이 부족합니다.')
            elif amount <= 0:
                await ctx.send('최소 입금액을 확인해주세요.')
            else:
                await ecomoney.update_one({"id": user.id}, {"$inc": {"wallet": -amount, "bank": +amount}})
                await ctx.send(f'당신의 {amount} ZEN이 은행으로 입금되었습니다. 꿀꺽~')
        except Exception as e:
            await ctx.send('취..익 취이..ㄱ')


    @commands.command(aliases=["강탈"])
    @cooldown(1, 120, BucketType.user)
    async def rob(self, ctx, user: discord.Member = None):
        """ 상대의 지갑에 있는 돈을 강탈 합니다. (ko : !강탈)"""
        if user is None or user.id == ctx.author.id:
            await ctx.send('Trying to rob yourself?')
        else:
            try:
                await self.update_user(ctx.author.id)
                await self.update_user(user.id)
                user_bal = await ecomoney.find_one({"id": user.id})
                member_bal = await ecomoney.find_one({"id": ctx.author.id})
                mem_bank = member_bal["bank"]
                user_bank = user_bal["bank"]
                if mem_bank < 100:
                    await ctx.send('You do not have enough money to rob someone')
                elif mem_bank >= 100:
                    if user_bank < 100:
                        await ctx.send('User do not have enough money to get robbed ;-;')
                    elif user_bank >= 100:
                        num = random.randint(1, 100)
                        f_mem = mem_bank + num
                        f_user = user_bank - num
                        await self.update_bank(ctx.author.id, f_mem)
                        await self.update_bank(user.id, f_user)
                        await ctx.send(f'You have robbed {num} ZEN from {user.mention}')
            except Exception:
                await ctx.send('취..익 취이..ㄱ')

    # send money to another user
    @commands.command(aliases=["송금"])
    @cooldown(1, 2, BucketType.user)
    async def send(self, ctx, user: discord.Member, amount: int):
        """ 은행의 ZEN을 다른 사람에게 송급합니다.(ko : !송금)"""
        try:
            await self.update_user(user.id)
            await self.update_user(ctx.author.id)
            user_bal = await ecomoney.find_one({"id": user.id})
            member_bal = await ecomoney.find_one({"id": ctx.author.id})
            mem_bank = member_bal["bank"]
            user_bank = user_bal["bank"]
            if amount > mem_bank or amount > 20000:
                await ctx.send('송금액을 확인해주세요(1회 최대 20,000ZEN 만 보낼 수 있습니다.)')
            elif amount <= 0:
                await ctx.send('최소 송금금액을 다시 확인해주세요.')
            else:
                await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"bank": -amount}})
                await ecomoney.update_one({"id": user.id}, {"$inc": {"bank": +amount}})
                await ctx.send(f'당신이 {user.mention}에게 {amount} ZEN을 송금했습니다. 더 줘 빨리 꺼억🙌')
        except Exception:
            await ctx.send('취..익 취이..ㄱ')

    # grant money to user
    @commands.command(aliases=["gt", "지급"])
    @commands.has_role("mods")
    @cooldown(1, 2, BucketType.user)
    async def grant(self, ctx, user : discord.Member, amount : int):
        """ 유저에게 ZEN을 지급합니다.(관리자용) (ko : !지급)"""
        try:
            await self.update_user(user.id)
            user_bal = await ecomoney.find_one({"id": user.id})
            user_bank = user_bal["bank"]
            if amount <= 0:
                await ctx.send('0 ZEN 이상 수량을 입력해 주세요.')
            elif amount >= 10000:
                await ctx.send('1회 최대 10,000 ZEN 지급 가능합니다.')
            else:
                await ecomoney.update_one({"id": user.id}, {"$inc": {"bank": +amount}})
                await ctx.send(f'{user.mention} 에게 {amount} ZEN을 지급했습니다.')
        except Exception:
            await ctx.send('취..익 취이..ㄱ')

    @commands.command(aliases=["ff", "몰수"])
    @commands.has_role("mods")
    @cooldown(1, 2, BucketType.user)
    async def forfeit(self, ctx, user: discord.Member):
        """ 유저의 모든 재산을 몰수합니다.(관리자용) (ko : !몰수)"""
        try:
            await ecomoney.delete_one({"id": user.id})
            await self.update_user(user.id)
            await ctx.send(f"{user.mention}에게서 모든 자산을 몰수하였습니다. !!")

        except Exception:
            await ctx.send('취..익 취이..ㄱ')

    # Buy land
    @commands.command(aliases=["l", "땅구매"])
    @cooldown(1, 2, BucketType.user)
    async def land(self, ctx, amount: int = 1):
        """ 땅을 구매합니다. (ko : !땅구매)"""
        try:
            if amount <= 0 or amount > 100:
                await ctx.send("한번에 0에서 100평 이하의 땅을 구매가능합니다.")
                return
            await self.update_user(ctx.author.id)
            bal = await ecomoney.find_one({"id": ctx.author.id})

            price = land["price"] * amount

            u_bal = bal["bank"]

            if u_bal < price:
                await ctx.send("은행에 돈이 부족합니다.")
                return

            await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"bank": -price}})
            await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"land": amount}})
            await ctx.send(f"축하합니다! 당신이 {price} ZEN을 이용해 마하드비파 영토 {amount}평을 구매했습니다. 구웃~👍 추매 해서 땅부자가 되보자!")
        except Exception:
            await ctx.send('취..익 취이..ㄱ')


    # A economy bot fun command
    @commands.command(aliases=["배팅"])
    @cooldown(1, 2, BucketType.user)
    async def gamble(self, ctx, amount: int):
        """ 배팅게임을 시작합니다. (ko : !배팅) 최대 1000 ZEN"""
        try:
            await self.update_user(ctx.author.id)
            user_bal = await ecomoney.find_one({"id": ctx.author.id})

            if amount > user_bal["wallet"]:
                await ctx.send('지갑에 잔고가 부족합니다.')
            elif amount <= 0:
                await ctx.send('0 ZEN 이상을 배팅해주세요.')
            elif amount > 1000:
                await ctx.send('최대 1000 ZEN 만 배팅 가능합니다.')
            else:
                num = random.randint(1, 100)
                if num <= 50:
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": +amount}})
                    await ctx.send(f'당신이 승리해 Hope에게서 {amount} ZEN을 빼앗았습니다. 후…. 봐줬다.')
                elif num > 50:
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                    await ctx.send(f'당신이 패배해 Hope가 {amount} ZEN을 가져갔습니다. 메렁😋')
        except Exception:
            await ctx.send('취..익 취이..ㄱ')

    @commands.command(aliases=["주사위"])
    @cooldown(1, 2, BucketType.user)
    async def dice(self, ctx, amount: int):
        """ 주사위 게임을 시작합니다. (ko : !주사위) 최대 1000 ZEN"""
        try:
            await self.update_user(ctx.author.id)
            user_bal = await ecomoney.find_one({"id": ctx.author.id})

            if amount > user_bal["wallet"]:
                await ctx.send('지갑에 잔고가 부족합니다.')
            elif amount <= 0:
                await ctx.send('0 ZEN 이상을 배팅해주세요.')
            elif amount > 1000:
                await ctx.send('최대 1000 ZEN 만 배팅 가능합니다.')
            else:
                user_dice = random.randint(1, 7)
                robot_dice = random.randint(1, 7)

                if user_dice > robot_dice:
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": +(amount*4)}})
                    result = f"당신은 Hope에게서 {amount*4} ZEN을 강탈했습니다. Hope가 분노한다👿"
                    _color = 0xFF0000
                elif user_dice == robot_dice:
                    result = f"당신의 {amount} ZEN을 Hope가 강탈하지 못했습니다. Hope한테 삥뜯으려면 다시 ㄱㄱ"
                    _color = 0xFAFA00
                else:
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                    result = f'당신은 Hope에게 {amount} Zen을 강탈당했습니다. 약 오르지? 메렁😋'
                    _color = 0x00FF56

                embed = discord.Embed(title="던져! 던져! 주사위 게임 결과!", description="누가 누가 이겼을까? 돈놓고 돈먹기 가즈앗!", color=_color)
                embed.add_field(name="Hope's Number", value=f":game_die: {robot_dice}", inline=True)
                embed.add_field(name=f"{ctx.author.name}'s Number", value=f":game_die: {user_dice}", inline=True)
                embed.set_footer(text=result)
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send('취..익 취이..ㄱ')

def setup(bot):
    bot.add_cog(Economy(bot))