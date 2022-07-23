import datetime
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
import random
import asyncio
from utils.dbctrl import db
from utils.event import event


def is_channel(*channelId):
    def predicate(ctx):
        result = False
        for channel in channelId:
            if ctx.message.channel.id == channel:
                result = True
        return result

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


class 돈(commands.Cog):
    """ 돈 관련 명령어 """

    def __init__(self, bot):
        self.bot = bot
        self.rob_event = False

    async def rob_event_loop(self, end_time):
        for i in range(0, end_time):
            await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Eco Cog Loaded Succesfully")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.channel.id == db.channel_data["사냥터"] or message.channel.id == db.channel_data[
            "강화"] or message.channel.id == db.channel_data["무기상점"] or message.channel.id == db.channel_data[
            "도박장"] or message.channel.id == db.channel_data["가위바위보"]:
            return

        # check if the server exists in servers and if not create an entry
        server = await db.ecoinfo.find_one({"_id": message.guild.id})
        if server is None:
            await db.ecoinfo.insert_one(
                {"_id": message.guild.id, "event_count": 5, "message_counter": 0, "event": False})
        else:
            # check server message_counter
            message_counter = server["message_counter"]
            event_count = server["event_count"]
            event = server["event"]

            if message_counter + 1 >= event_count:
                # event occur
                amount = random.randint(100, 1000)
                embed = discord.Embed(
                    title=f'하늘에서 ZEN이 떨어졌다! 지나가던 {message.author}가 {amount} ZEN 뭉치를 발견하였다!!',
                    description=f"{message.author}는 얼른 ZEN 을 획득하기 위해서'줍기'를 입력하라구!"
                                "\n10초 제한 시간내 줍지 않을 경우 다른 누구나 '줍기'를 통해 주을 수 있습니다.",
                    color=discord.Color.gold()
                )
                await message.channel.send(embed=embed)
                message_counter = 0
                event_count = random.randint(10, 250)
                # event_count = 5
                await db.ecoinfo.update_one(server, {
                    "$set": {"event_count": event_count, "message_counter": message_counter,
                             "event_owner": str(message.author),
                             "event_amount": amount, "event_time": datetime.datetime.utcnow(), "event": True}})
            else:
                message_counter += 1
                if event == True:
                    event_occurred_time = server["event_time"]
                    event_owner = server["event_owner"]
                    event_amount = server["event_amount"]
                    time_now = datetime.datetime.utcnow()
                    if (time_now - event_occurred_time).total_seconds() < 10:
                        if str(message.author) == str(event_owner):
                            if str(message.content) == "줍기":
                                await db.ecoinfo.update_one(server,
                                                            {"$set": {"message_counter": message_counter,
                                                                      "event": False}})
                                await db.add_wallet(message.author.id, +event_amount)
                                await message.channel.send(f'축하합니다. {message.author}가 {event_amount} ZEN을 획득하였습니다.')
                    else:
                        if str(message.content) == "줍기":
                            await db.ecoinfo.update_one(server,
                                                        {"$set": {"message_counter": message_counter, "event": False}})
                            await db.add_wallet(message.author.id, +event_amount)
                            await message.channel.send(f'축하합니다. {message.author}가 {event_amount} ZEN을 획득하였습니다.')
                else:
                    await db.ecoinfo.update_one(server, {"$set": {"message_counter": message_counter}})

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["주막"], db.channel_data["무기상점"], db.channel_data["도박장"], db.channel_data["가위바위보"],
                db.channel_data["부동산"], db.channel_data["강화"])
    async def 자산(self, ctx, user: discord.Member = None):
        """
            유저의 자산을 확인합니다. 유저명 누락시 본인 (!자산 [유저명])
        """
        if user is None:
            user = ctx.author
        try:
            await db.update_user(user.id)
            bal = await db.ecomoney.find_one({"id": user.id})
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
            print("!자산 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 300, BucketType.user)
    @is_channel(db.channel_data["주막"])
    async def 인출(self, ctx, amount: int):
        """ 수량만큼의 ZEN을 봇짐으로 인출합니다. (!인출 [수량]) """
        user = ctx.author
        try:
            await db.update_user(user.id)
            bal = await db.ecomoney.find_one({"id": user.id})
            if amount > bal['bank']:
                await ctx.send('은행에 잔고가 부족합니다.')
            elif amount <= 0:
                await ctx.send('최소 인출액을 확인해주세요.')
            else:
                await db.ecomoney.update_one({"id": user.id}, {"$inc": {"wallet": +amount, "bank": -amount}})
                await ctx.send(f'당신의 은행에서 {amount} ZEN이 인출되었습니다.')
        except Exception as e:
            print("!인출 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 300, BucketType.user)
    @is_channel(db.channel_data["주막"])
    async def 입금(self, ctx, amount: int):
        """ 수량 만큼의 ZEN을 은행으로 입금합니다. (!입금 [수량])"""
        user = ctx.author
        try:
            await db.update_user(user.id)
            bal = await db.ecomoney.find_one({"id": user.id})
            if amount > bal['wallet']:
                await ctx.send('잔액이 부족합니다.')
            elif amount <= 0:
                await ctx.send('최소 입금액을 확인해주세요.')
            else:
                await db.ecomoney.update_one({"id": user.id}, {"$inc": {"wallet": -amount, "bank": +amount}})
                await ctx.send(f'당신의 {amount} ZEN이 은행으로 입금되었습니다. 꿀꺽~')
        except Exception as e:
            print("!입금 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 120, BucketType.user)
    @is_channel(db.channel_data["주막"])
    async def 강탈(self, ctx, user: discord.Member = None):
        """ 상대의 봇짐에 있는 돈을 강탈 합니다. (!강탈 [유저명]) """
        if user is None or user.id == ctx.author.id:
            await ctx.send('자기자신을 강탈 할 순 없습니다.')
        else:
            try:
                member_bal = await db.update_user(ctx.author.id)
                user_bal = await db.update_user(user.id)

                mem_bank = member_bal["wallet"]
                user_bank = user_bal["wallet"]

                if mem_bank < 500:
                    await ctx.send('자신의 봇짐을 비운채 남을 강탈할 수 없습니다.(최소 500 ZEN)')
                    return

                if user.id == db.bot_id:
                    bot_rob = round(mem_bank * 0.1)
                    await ctx.send(f'{ctx.author.mention}, 감히 나를 강탈하려 하다니! {bot_rob} ZEN을 강탈하겠습니다!')
                    await db.add_wallet(ctx.author.id, -bot_rob)
                    return

                if user_bank < 100:
                    await ctx.send('상대의 봇짐이 텅텅 비었습니다. 거지는 건들이지 맙시다.(최소 100 ZEN)')
                elif user_bank >= 100:
                    num = random.randint(1, 100)
                    f_mem = mem_bank + num
                    f_user = user_bank - num
                    await db.update_wallet(ctx.author.id, f_mem)
                    await db.update_wallet(user.id, f_user)
                    await ctx.send(f'{ctx.author.mention}이 {user.mention}에게서 {num} ZEN 을 강탈하였습니다.')

            except Exception as e:
                print("!강탈", e)
                await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 20, BucketType.user)
    @is_channel(db.channel_data["주막"])
    async def 은행털기(self, ctx, user: discord.Member = None):
        """ 상대의 은행에 있는 돈을 강탈 합니다. 이벤트시 가능 (!은행털기 [유저명]) """
        if user is None or user.id == ctx.author.id:
            await ctx.send('자기자신을 털 순 없습니다.')
        else:
            try:
                if not event.rob_event:
                    await ctx.send("은행을 털 순 없습니다. AOZ의 은행은 지금 굳건합니다.")
                    return

                member_bal = await db.update_user(ctx.author.id)
                user_bal = await db.update_user(user.id)
                mem_bank = member_bal["bank"]
                user_bank = user_bal["bank"]

                if user.id == db.bot_id:
                    bot_rob = round(mem_bank * 0.1)
                    await ctx.send(f'{ctx.author.mention}, 감히 나를 강탈하려 하다니! {bot_rob} ZEN을 강탈하겠습니다!')
                    await db.add_bank(ctx.author.id, -bot_rob)
                    return

                if user_bank < 100:
                    await ctx.send('상대의 계좌가 텅텅 비었습니다. 거지는 건들이지 맙시다.(최소 100 ZEN)')
                elif user_bank >= 100:
                    num = random.randint(50, 100)
                    f_mem = mem_bank + num
                    f_user = user_bank - num
                    await db.update_bank(ctx.author.id, f_mem)
                    await db.update_bank(user.id, f_user)
                    await ctx.send(f'{ctx.author.mention}이 {user.mention}의 계좌의 {num} ZEN 을 강탈하였다.')

            except Exception as e:
                print("!은행털기", e)
                await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["주막"])
    async def 송금(self, ctx, user: discord.Member, amount: int):
        """ 유저에게 수량 만큼의 ZEN을 은행에서 송금합니다. (!송금 [유저명] [수량]) """
        try:
            await db.update_user(user.id)
            await db.update_user(ctx.author.id)
            user_bal = await db.ecomoney.find_one({"id": user.id})
            member_bal = await db.ecomoney.find_one({"id": ctx.author.id})
            mem_bank = member_bal["bank"]
            user_bank = user_bal["bank"]
            if amount > mem_bank or amount > 20000:
                await ctx.send('송금액을 확인해주세요(1회 최대 20,000ZEN 만 보낼 수 있습니다.)')
            elif amount <= 0:
                await ctx.send('최소 송금금액을 다시 확인해주세요.')
            else:
                await db.ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"bank": -amount}})
                await db.ecomoney.update_one({"id": user.id}, {"$inc": {"bank": +amount}})
                await ctx.send(f'당신이 {user.mention}에게 {amount} ZEN을 송금했습니다. 더 줘 빨리 꺼억🙌')
        except Exception:
            await ctx.send('취..익 취이..ㄱ')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["주막"])
    async def 돈뿌리기(self, ctx, amount: int):
        """ 봇짐에 있는 ZEN을 랜덤 유저에게 나누어서 뿌립니다. (!돈뿌리기 [수량]) """
        try:
            await db.update_user(ctx.author.id)
            member_bal = await db.ecomoney.find_one({"id": ctx.author.id})
            mem_wallet = member_bal["wallet"]
            if amount > mem_wallet or amount > 10000:
                await ctx.send('금액을 확인해주세요(1회 최대 10,000ZEN 만 뿌릴 수 있습니다.)')
            elif amount <= 0:
                await ctx.send('최소 금액을 다시 확인해주세요.')
            else:
                await db.ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                # await ecomoney.update_one({"id": 987293637769560085}, {"$inc": {"wallet": +amount}})
                await ctx.send(f'{ctx.author.mention}이 {amount} ZEN을 뿌렸습니다. 어서어서들 줍줍 ㄱㄱ')

                number_of_member = len(ctx.guild.members)
                number_of_selected_member = random.randint(10, 20)

                if number_of_selected_member > number_of_member:
                    number_of_selected_member = number_of_member
                split_money = splitMoney(amount, number_of_selected_member)
                for money in split_money:
                    select_index = random.randint(0, number_of_member - 1)
                    selected_member = ctx.guild.members[select_index]

                    await db.update_user(selected_member.id)
                    await db.ecomoney.update_one({"id": selected_member.id}, {"$inc": {"wallet": +money}})
                    await ctx.send(f'{selected_member.mention}이 {money}를 받았습니다.')

        except Exception as e:
            print("!돈뿌리기", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @commands.has_role("mods")
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["주막"])
    async def 지급(self, ctx, user: discord.Member, amount: int):
        """ 유저에게 ZEN을 지급합니다.(관리자용) (!지급 [유저명] [수량]) """
        try:
            user_bal = await db.update_user(user.id)
            if amount <= 0:
                await ctx.send('0 ZEN 이상 수량을 입력해 주세요.')
            elif amount >= 10000:
                await ctx.send('1회 최대 10,000 ZEN 지급 가능합니다.')
            else:
                await db.add_wallet(user.id, +amount)
                await ctx.send(f'{user.mention} 에게 {amount} ZEN을 지급했습니다.')
        except Exception as e:
            print("!지급", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @commands.has_role("mods")
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["주막"])
    async def 몰수(self, ctx, user: discord.Member):
        """ 유저의 모든 재산을 몰수합니다.(관리자용) (!몰수 [유저명]) """
        try:
            user_bal = await db.update_user(user.id)
            user_bank = user_bal["bank"]
            user_wallet = user_bal["wallet"]
            user_land = user_bal["land"]
            await db.add_bank(user.id, -user_bank)
            await db.add_wallet(user.id, -user_wallet)
            await db.add_land(user.id, -user_land)
            await db.ecomoney.delete_one({"id": user.id})
            await db.ecobag.delete_one({"id": user.id})
            await db.ecouser.delete_one({"id": user.id})

            # await db.update_user(user.id)
            # await db.update_battle_user(user.id)
            # await db.update_bag(user.id)
            await ctx.send(f"{user.mention}에게서 모든 자산을 몰수하였습니다. !!")

        except Exception as e:
            print("!몰수", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    # leaderboard
    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["주막"])
    async def 랭킹(self, ctx, field: str):
        """ 각종 랭킹을 확인합니다. (!랭킹 [필드명]) 필드 목록 : 은행, 레벨, 토지 기여도"""
        if field == "은행":
            rankings = db.ecomoney.find().sort("bank", -1)
        elif field == "레벨":
            rankings = db.ecouser.find().sort("level", -1)
        elif field == "토지":
            rankings = db.ecomoney.find().sort("land", -1)
        elif field == "기여도":
            rankings = db.ecouser.find().sort("point", -1)
        else:
            await ctx.send("없는 랭킹 입니다!")
            return

        i = 1

        embed = discord.Embed(
            title=f"{ctx.guild.name} {field} 랭킹",
            description=f"\u200b",
            color=0xFF0000
        )

        async for x in rankings:
            try:
                if x["id"] == db.bot_id:
                    continue
                temp = ctx.guild.get_member(x["id"])
                if field == "은행":
                    tb = x["bank"]
                    embed.add_field(
                        name=f"{i} : {temp.name}", value=f"{tb} ZEN", inline=False
                    )
                elif field == "레벨":
                    tb = x["level"]
                    embed.add_field(
                        name=f"{i} : {temp.name}", value=f"레벨: {tb}", inline=False
                    )
                elif field == "토지":
                    tb = x["land"]
                    embed.add_field(
                        name=f"{i} : {temp.name}", value=f"{tb}평", inline=False
                    )
                elif field == "기여도":
                    tb = x["point"]
                    embed.add_field(
                        name=f"{i} : {temp.name}", value=f"{tb}포인트", inline=False
                    )
                i += 1
            except:
                pass
            if i == 11:
                break

        embed.set_footer(
            text=f"요청자: {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(돈(bot))
