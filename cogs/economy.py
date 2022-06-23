import datetime
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
with open('./market.json', encoding='UTF-8') as f:
    d2 = json.load(f)


land = d2["Land"]

# print(land)

nest_asyncio.apply()

mongo_url = d1['mongo']

cluster = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
ecomoney = cluster["eco"]["money"]
ecoinfo = cluster["eco"]["info"]

def is_channel(channelId):
    def predicate(ctx):
        return ctx.message.channel.id == channelId
    return commands.check(predicate)

def splitMoney(amount, n):
    a = amount
    avg_amount = round(amount / n)

    pieces = []
    for idx in range(1, n):
        remainer = a - sum(pieces)
        at_least = (n - idx) * avg_amount
        max_amount = remainer - at_least

        amount = random.randint(1, max_amount)
        pieces.append(random.randint(1, amount))
    pieces.append(a - sum(pieces))
    return pieces

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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        # check if the server exists in servers and if not create an entry
        server = await ecoinfo.find_one({"_id": message.guild.id})
        if server is None:
            await ecoinfo.insert_one(
                {"_id": message.guild.id, "event_count": 5, "message_counter": 0, "event": False})
        else:
            # check server message_counter
            message_counter = server["message_counter"]
            event_count = server["event_count"]
            event = server["event"]

            if message_counter + 1 >= event_count:
                # event occur
                amount = random.randint(100,1000)
                embed = discord.Embed(
                    title=f'하늘에서 ZEN이 떨어졌다! 지나가던 {message.author}가 {amount} ZEN 뭉치를 발견하였다!!',
                    description=f"{message.author}는 얼른 ZEN 을 획득하기 위해서'줍기'를 입력하라구!"
                                "\n10초 제한 시간내 줍지 않을 경우 다른 누구나 '줍기'를 통해 주을 수 있습니다.",
                    color=discord.Color.gold()
                )
                await message.channel.send(embed=embed)
                message_counter = 0
                event_count = random.randint(10,250)
                # event_count = 5
                await ecoinfo.update_one(server, {"$set":{"event_count": event_count, "message_counter": message_counter, "event_owner": str(message.author),
                                                          "event_amount": amount, "event_time": datetime.datetime.now(), "event": True}})
            else:
                message_counter += 1
                if event == True:
                    event_occurred_time = server["event_time"]
                    event_owner = server["event_owner"]
                    event_amount = server["event_amount"]
                    time_now = datetime.datetime.now()
                    if (time_now - event_occurred_time).total_seconds() < 10:
                        if str(message.author) == str(event_owner):
                            if str(message.content) == "줍기":
                                print(server)
                                await ecoinfo.update_one(server, {"$set":{"message_counter": message_counter, "event": False}})
                                await ecomoney.update_one({"id": message.author.id}, {"$inc": {"wallet": +event_amount}})
                                await message.channel.send(f'축하합니다. {message.author}가 {event_amount} ZEN을 획득하였습니다.')
                    else:
                        if str(message.content) == "줍기":
                            await ecoinfo.update_one(server, {"$set":{"message_counter": message_counter, "event": False}})
                            await ecomoney.update_one({"id": message.author.id}, {"$inc": {"wallet": +event_amount}})
                            await message.channel.send(f'축하합니다. {message.author}가 {event_amount} ZEN을 획득하였습니다.')
                else:
                    await ecoinfo.update_one(server, {"$set": {"message_counter": message_counter}})


    @commands.command(aliases=["bal", "자산"])
    @cooldown(1, 2, BucketType.user)
    # @is_channel(986902833871855626)
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
    @is_channel(986902833871855626)
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
    @is_channel(986902833871855626)
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

    # 출석체크
    @commands.command(aliases=["출첵"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(986902833871855626)
    async def gm(self, ctx):
        """ 출석체크를 통해 ZEN을 지급 받습니다. (ko : !출첵)"""
        try:
            await self.update_user(ctx.author.id)
            eco = await ecomoney.find_one({"id": ctx.author.id})
            gm_time = eco['gm_time']
            if gm_time is not None:
                if (datetime.datetime.now() - gm_time).total_seconds() < 86400:
                    await ctx.send("지난 출첵 부터 24시간이 지나야 다시 출첵 가능합니다.")
                    return

            amount = 50
            for role in ctx.author.roles:
                if role.id == 950255167264141412 or role.id == 950255426740568105 or role.id == 950255295786016768:
                    amount = 100
            print(amount)
            await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"bank": +amount}})
            await ecomoney.update_one({"id": ctx.author.id}, {"$set": {"gm_time": datetime.datetime.now()}})
            await ctx.send(f'{ctx.author.mention} 에게 {amount} ZEN을 지급했습니다.')
        except Exception as e:
            print(e)
            await ctx.send('취..익 취이..ㄱ')

    @commands.command(aliases=["강탈"])
    @cooldown(1, 120, BucketType.user)
    @is_channel(986902833871855626)
    async def rob(self, ctx, user: discord.Member = None):
        """ 상대의 지갑에 있는 돈을 강탈 합니다. (ko : !강탈)"""
        if user is None or user.id == ctx.author.id:
            await ctx.send('자기자신을 강탈 할 순 없습니다.')
        else:
            try:
                await self.update_user(ctx.author.id)
                await self.update_user(user.id)
                user_bal = await ecomoney.find_one({"id": user.id})
                member_bal = await ecomoney.find_one({"id": ctx.author.id})
                mem_bank = member_bal["wallet"]
                user_bank = user_bal["wallet"]
                if mem_bank < 500:
                    await ctx.send('자신의 지갑을 비운채 남을 강탈할 수 없습니다.(최소 500 ZEN)')
                elif mem_bank >= 500:
                    if user_bank < 100:
                        await ctx.send('상대의 지갑에 충분한 돈이 들어있지 않습니다.(최소 100 ZEN)')
                    elif user_bank >= 100:
                        num = random.randint(1, 100)
                        f_mem = mem_bank + num
                        f_user = user_bank - num
                        await self.update_wallet(ctx.author.id, f_mem)
                        await self.update_wallet(user.id, f_user)
                        await ctx.send(f'{ctx.author.mention}이 {user.mention}에게서 {num} ZEN 을 강탈하였다.')
            except Exception:
                await ctx.send('취..익 취이..ㄱ')

    # send money to another user
    @commands.command(aliases=["송금"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(986902833871855626)
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

    # send money to another user
    @commands.command(aliases=["돈뿌리기", "ga"])
    @cooldown(1, 2, BucketType.user)
    # @is_channel(986902833871855626)
    async def giveaway(self, ctx, amount: int):
        """ 지갑에 있는 ZEN을 랜덤하게 뿌립니다.(ko : !돈뿌리기)"""
        try:
            await self.update_user(ctx.author.id)
            member_bal = await ecomoney.find_one({"id": ctx.author.id})
            mem_wallet = member_bal["wallet"]
            if amount > mem_wallet or amount > 10000:
                await ctx.send('금액을 확인해주세요(1회 최대 10,000ZEN 만 뿌릴 수 있습니다.)')
            elif amount <= 0:
                await ctx.send('최소 금액을 다시 확인해주세요.')
            else:
                await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                # await ecomoney.update_one({"id": 987293637769560085}, {"$inc": {"wallet": +amount}})
                await ctx.send(f'{ctx.author.mention}이 {amount} ZEN을 뿌렸습니다. 어서어서들 줍줍 ㄱㄱ')

                number_of_member = len(ctx.guild.members)
                number_of_selected_member = random.randint(10, 20)


                if number_of_selected_member > number_of_member:
                    number_of_selected_member = number_of_member
                print(number_of_selected_member)
                split_money = splitMoney(amount, number_of_selected_member)
                print(split_money)
                for money in split_money:
                    select_index = random.randint(0, number_of_member - 1)
                    print(select_index)
                    selected_member = ctx.guild.members[select_index]

                    await self.update_user(selected_member.id)
                    await ecomoney.update_one({"id": selected_member.id}, {"$inc": {"wallet": +money}})
                    await ctx.send(f'{selected_member.mention}이 {money}를 받았습니다.')

        except Exception as e:
            print(e)
            await ctx.send('취..익 취이..ㄱ')
                
    # grant money to user
    @commands.command(aliases=["gt", "지급"])
    @commands.has_role("mods")
    @cooldown(1, 2, BucketType.user)
    @is_channel(986902833871855626)
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
    @is_channel(986902833871855626)
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
    @is_channel(986901923338809344)
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

    # send your land to another user
    @commands.command(aliases=["땅증여"])
    @cooldown(1, 2, BucketType.user)
    # @is_channel(986902833871855626)
    async def sendland(self, ctx, user: discord.Member, amount: int):
        """ 보유중인 땅을 다른 사람에게 증여합니다.(ko : !땅증여)"""
        try:
            if ctx.author.id == user.id:
                await ctx.send('자기 자신에게 증여할 수 없습니다.')
            else:
                await self.update_user(user.id)
                await self.update_user(ctx.author.id)
                user_bal = await ecomoney.find_one({"id": user.id})
                member_bal = await ecomoney.find_one({"id": ctx.author.id})
                mem_land = member_bal["land"]
                user_bank = user_bal["land"]
                if amount > mem_land or amount > 100:
                    await ctx.send('증여할 땅 수량을 다시 확인하세요(1회 최대 100평의 땅을 증여 할 수 있습니다.)')
                elif amount <= 0:
                    await ctx.send('땅 수량을 다시 확인하세요')
                else:
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"land": -amount}})
                    await ecomoney.update_one({"id": user.id}, {"$inc": {"land": +amount}})
                    await ctx.send(f'{ctx.author.mention}이 {user.mention}에게 {amount}평의 땅을 송금했습니다.')
        except Exception:
            await ctx.send('취..익 취이..ㄱ')

    # A economy bot fun command
    @commands.command(aliases=["배팅"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(986902068742717460)
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
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": +int(round(amount/2,0))}})
                    await ctx.send(f'당신이 승리해 Hope에게서 {int(round(amount/2,0))} ZEN을 빼앗았습니다. 후…. 봐줬다.')
                else:
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                    await ctx.send(f'당신이 패배해 Hope가 {amount} ZEN을 가져갔습니다. 메렁😋')
        except Exception:
            await ctx.send('취..익 취이..ㄱ')

    @commands.command(aliases=["주사위"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(986902068742717460)
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
                    if random.randint(1, 10) == 9:
                        amount = amount * 2
                        result = f"잭팟! 불굴의 의지로 당신은 Hope에게서 {amount} ZEN을 강탈했습니다. Hope가 원통해합니다.👿"
                    else:
                        amount = amount
                        result = f"당신은 Hope에게서 {amount} ZEN을 강탈했습니다. Hope가 분노한다👿"
                    await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": +(amount)}})
                    _color = 0xFF0000
                elif user_dice == robot_dice:
                    result = f"당신의 {amount} ZEN을 Hope가 강탈하지 못했습니다. Hope한테 삥뜯으려면 다시 ㄱㄱ🤡"
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

    @commands.command(aliases=["가바보"])
    @cooldown(1, 2, BucketType.user)
    @is_channel(986902319574700052)
    async def rps(self, ctx, userRPS : str, amount: int):
        """ 가위바위보 게임을 시작합니다. (ko : !가바보) 최대 1000 ZEN"""
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
                rps_table = ['가위', '바위', '보']
                if userRPS in rps_table:
                    rps_emoji = [':v:', ':fist:', ':hand_splayed:']
                    botRPS = random.choice(rps_table)
                    botEmoji = rps_emoji[rps_table.index(botRPS)]
                    userEmoji = rps_emoji[rps_table.index(userRPS)]
                    result = rps_table.index(userRPS) - rps_table.index(botRPS)  # 인덱스 비교로 결과 결정
                    if result == 0:
                        result = f"Hope! 다시 한 번 붙어보자! 보상 X"
                        _color = 0xFAFA00
                    elif result == 1 or result == -2:
                        if random.randint(1, 10) == 9:
                            amount = amount * 2
                            result = f"잭팟! 당신은 Hope에게 이겼다! (보상 : {amount})"
                        else:
                            amount = amount
                            result = f"당신은 Hope에게 이겼다! (보상 : {amount})"
                        await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": +amount}})
                        _color = 0xFF0000
                    else:
                        result = f'당신은 Hope에게 졌다!'
                        await ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                        _color = 0x00FF56

                    embed = discord.Embed(title="가위바위보 게임 결과!", description="누가 누가 이겼을까? 돈놓고 돈먹기 가즈앗!", color=_color)
                    embed.add_field(name="Hope", value= botEmoji, inline=True)
                    embed.add_field(name=f"{ctx.author.name}", value=userEmoji, inline=True)
                    embed.set_footer(text=result)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("가위 바위 보 중에 하나를 선택하세요.")
        except Exception:
            await ctx.send('취..익 취이..ㄱ')

def setup(bot):
    bot.add_cog(Economy(bot))