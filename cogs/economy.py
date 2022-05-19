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

print(land)

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
        """ Check your balance(ko: !자산) """
        if user is None:
            user = ctx.author
        try:
            await self.update_user(user.id)
            bal = await ecomoney.find_one({"id": user.id})
            embed = discord.Embed(
                timestamp=ctx.message.created_at,
                title=f"{user}'s Balance",
                color=0xFF0000,
            )
            embed.add_field(
                name="Land",
                value=f"{bal['land']}\U000033A5",
            )
            embed.add_field(
                name="Wallet",
                value=f"{bal['wallet']} ZEN",
            )
            embed.add_field(
                name="Bank",
                value=f"{bal['bank']} ZEN",
            )
            embed.set_footer(
                text=f"Requested By: {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
            )
            embed.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send('An error occured')
            print(e)

    @commands.command(aliases=["wd", "출금"])
    @cooldown(1, 2, BucketType.user)
    async def withdraw(self, ctx, amount: int):
        """ Withdraw money from your bank(ko : !자산)"""
        user = ctx.author
        try:
            await self.update_user(user.id)
            bal = await ecomoney.find_one({"id": user.id})
            if amount > bal['bank']:
                await ctx.send('You do not have enough money to withdraw that much')
            elif amount <= 0:
                await ctx.send('You cannot withdraw 0 or less')
            else:
                await ecomoney.update_one({"id": user.id}, {"$inc": {"wallet": +amount, "bank": -amount}})
                await ctx.send(f'You have withdrawn {amount} ZEN')
        except Exception:
            await ctx.send('An error occured')

    @commands.command(aliases=["dp", "입금"])
    @cooldown(1, 2, BucketType.user)
    async def deposit(self, ctx, amount: int):
        """ Deposit money to your bank(ko : !입금)"""
        user = ctx.author
        try:
            await self.update_user(user.id)
            bal = await ecomoney.find_one({"id": user.id})
            if amount > bal['wallet']:
                await ctx.send('You do not have enough money to deposit that much')
            elif amount <= 0:
                await ctx.send('You cannot deposit 0 or less')
            else:
                await ecomoney.update_one({"id": user.id}, {"$inc": {"wallet": -amount, "bank": +amount}})
                await ctx.send(f'You have deposited {amount} ZEN')
        except Exception as e:
            await ctx.send('An error occured')


    @commands.command(aliases=["강탈"])
    @cooldown(1, 120, BucketType.user)
    async def rob(self, ctx, user: discord.Member = None):
        """ Rob someone(ko : !강탈)"""
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
                await ctx.send('An error occured')

    # send money to another user
    @commands.command(aliases=["송금"])
    @cooldown(1, 2, BucketType.user)
    async def send(self, ctx, user: discord.Member, amount: int):
        """ Send money to another user(ko : !송금)"""
        try:
            await self.update_user(user.id)
            await self.update_user(ctx.author.id)
            user_bal = await ecomoney.find_one({"id": user.id})
            member_bal = await ecomoney.find_one({"id": ctx.author.id})
            mem_bank = member_bal["bank"]
            user_bank = user_bal["bank"]
            if amount > mem_bank or amount > 20000:
                await ctx.send('You do not have enough money to send that much or amount too much')
            elif amount <= 0:
                await ctx.send('You cannot send 0 or less')
            else:
                await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"bank": -amount}})
                await ecomoney.update_one({"id": user.id}, {"$inc": {"bank": +amount}})
                await ctx.send(f'You have sent {amount} ZEN to {user.mention}')
        except Exception:
            await ctx.send('An error occured')

    # grant money to user
    @commands.command(aliases=["gt", "지급"])
    @commands.has_role("mods")
    @cooldown(1, 2, BucketType.user)
    async def grant(self, ctx, user : discord.Member, amount : int):
        """ Grant money to another user(ko : !지급)"""
        try:
            await self.update_user(user.id)
            user_bal = await ecomoney.find_one({"id": user.id})
            user_bank = user_bal["bank"]
            if amount <= 0:
                await ctx.send('You cannot grant 0 or less')
            elif amount >= 10000:
                await ctx.send('You cannot grant more than 10,000 ZEN at once')
            else:
                await ecomoney.update_one({"id": user.id}, {"$inc": {"bank": +amount}})
                await ctx.send(f'{user.mention} got {amount} ZEN, check you bank!')
        except Exception:
            await ctx.send('An error occured')

    @commands.command(aliases=["ff", "몰수"])
    @commands.has_role("mods")
    @cooldown(1, 2, BucketType.user)
    async def forfeit(self, ctx, user: discord.Member):
        """ Confiscate all assets from the user(ko : !몰수)"""
        try:
            await ecomoney.delete_one({"id": user.id})
            await self.update_user(user.id)

        except Exception:
            await ctx.send('An error occured')

    # Buy land
    @commands.command(aliases=["l", "땅구매"])
    @cooldown(1, 2, BucketType.user)
    async def land(self, ctx, amount: int = 1):
        """ Buy land on AOZ world (ko : !땅구매)"""
        if amount <= 0 or amount > 100:
            await ctx.send("Amount must be greater than 0 or less than 100")
            return
        await self.update_user(ctx.author.id)
        bal = await ecomoney.find_one({"id": ctx.author.id})

        price = land["price"] * amount

        u_bal = bal["bank"]

        if u_bal < price:
            await ctx.send("You don't have enough money in your bank")
            return

        await ecomoney.update_one({"id": ctx.author.id}, {"$inc":{"bank": -price}})
        await ecomoney.update_one({"id": ctx.author.id}, {"$inc":{"land": amount}})
        await ctx.send(f"You bought {amount}\U000033A5 land for {price} ZEN")

    # A economy bot fun command
    @commands.command(aliases=["배팅"])
    @cooldown(1, 2, BucketType.user)
    async def gamble(self, ctx, amount: int):
        """ Gamble money(ko : !배팅) Max 1000 ZEN"""
        try:
            await self.update_user(ctx.author.id)
            user_bal = await ecomoney.find_one({"id": ctx.author.id})

            if amount > user_bal["wallet"]:
                await ctx.send('You do not have enough money to gamble that much')
            elif amount <= 0:
                await ctx.send('You cannot gamble 0 or less')
            elif amount > 1000:
                await ctx.send('You can not bet more than 1000 ZEN')
            else:
                num = random.randint(1, 100)
                if num <= 50:
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": +amount}})
                    await ctx.send(f'You have won {amount} ZEN')
                elif num > 50:
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                    await ctx.send(f'You have lost {amount} ZEN')
        except Exception:
            await ctx.send('An error occured')

    @commands.command(aliases=["주사위"])
    @cooldown(1, 2, BucketType.user)
    async def dice(self, ctx, amount: int):
        """ Dice game (ko : !주사위) Max 1000 ZEN"""
        try:
            await self.update_user(ctx.author.id)
            user_bal = await ecomoney.find_one({"id": ctx.author.id})

            if amount > user_bal["wallet"]:
                await ctx.send('You do not have enough money to gamble that much')
            elif amount <= 0:
                await ctx.send('You cannot gamble 0 or less')
            elif amount > 1000:
                await ctx.send('You can not bet more than 1000 ZEN')
            else:
                user_dice = random.randint(1, 7)
                robot_dice = random.randint(1, 7)

                if user_dice > robot_dice:
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": +(amount*4)}})
                    result = f"You have won {amount*4} ZEN"
                    _color = 0xFF0000
                elif user_dice == robot_dice:
                    result = f"You have drawn the game"
                    _color = 0xFAFA00
                else:
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                    result = f'You have lost {amount} ZEN'
                    _color = 0x00FF56

                embed = discord.Embed(title="Dice game result!", description=None, color=_color)
                embed.add_field(name="Super Bot's Number", value=f":game_die: {robot_dice}", inline=True)
                embed.add_field(name=f"{ctx.author.name}'s Number", value=f":game_die: {user_dice}", inline=True)
                embed.set_footer(text=result)
                await ctx.send(embed=embed)


        except Exception as e:
            print(e)
            await ctx.send('An error occured')



def setup(bot):
    bot.add_cog(Economy(bot))