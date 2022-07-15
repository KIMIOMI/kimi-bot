import asyncio
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
from utils.dbctrl import Db


db = Db()


def is_channel(*channelId):
    def predicate(ctx):
        result = False
        for channel in channelId:
            if ctx.message.channel.id == channel:
                result = True
        return result

    return commands.check(predicate)


class 경매(commands.Cog):
    """ 경매 명령어 """

    def __init__(self, bot):
        self.bot = bot
        self.bid_money = 0
        self.bid_user = ""
        self.auction_str = "현재 입찰자가 없습니다."
        self.auction_name = ""


    async def auction_loop(self, ctx, end_time):
        for i in range(0, end_time):
            await asyncio.sleep(60)
            await ctx.send(f"{self.auction_name} 경매진행 {i + 1}분 경과! {self.auction_str}")
        if self.bid_user != "":
            user_bal = await db.update_user(self.bid_user.id)
            if user_bal["bank"] < self.bid_money:
                await ctx.send(f"{self.bid_user.mention}님 계좌에 현재 낙찰에 지불할 금액이 없습니다!")
                self.bid_money = 0
                self.bid_user = ""
                self.auction_str = "현재 입찰자가 없습니다."
                self.auction_name = ""
                return
            await db.update_bank(self.bid_user.id, user_bal["bank"] - self.bid_money)
            await ctx.send(f"축하합니다! {self.bid_user.mention}님이 {self.auction_name}을 {self.bid_money}에 낙찰 받으셨습니다!")
        else:
            await ctx.send("아쉽지만 아무도 낙찰 받지 못하였습니다!")
        self.bid_money = 0
        self.bid_user = ""
        self.auction_str = "현재 입찰자가 없습니다."
        self.auction_name = ""

    @commands.Cog.listener()
    async def on_ready(self):
        print("Action Cog Loaded Succesfully")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @commands.has_role("mods")
    @is_channel(db.channel_data["경매장"])
    async def 경매(self, ctx, name: str, end_time: int = 5, bid_min: int = 100):
        """ 경매를 시작합니다.(관리자용) (!경매 [경매품] [시간] [최소입찰가]) """
        try:
            if self.bid_money > 0:
                await ctx.send("현재 경매가 진행 중입니다.")
                return
            if end_time < 5:
                await ctx.send("최소 경매 시간은 5분 입니다.")
                return
            if bid_min <= 0:
                await ctx.send("최소 입찰가를 확인해주세요")
                return
            self.auction_name = name
            await ctx.send(f"경매 항목 {name}의 경매를 시작합니다.\n{end_time}분 동안 진행됩니다.\n최소 입찰 금액은 {bid_min} ZEN 입니다.")
            self.bid_money = bid_min
            self.bot.loop.create_task(self.auction_loop(ctx, end_time))

        except Exception as e:
            print("!경매", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["경매장"])
    async def 입찰(self, ctx, bid: int):
        """ 경매에 입찰합니다. (!입찰 [입찰금액]) """
        try:
            await db.update_user(ctx.author.id)
            user_bal = await db.ecomoney.find_one({"id": ctx.author.id})
            if self.bid_money == 0:
                await ctx.send("현재 진행중인 경매가 없습니다.")
                return
            if bid <= self.bid_money:
                await ctx.send("최소 입찰 금액을 확인해 주세요")
                return

            if user_bal["bank"] < bid:
                await ctx.send(f"{ctx.author.mention}님 은행 계좌에 잔고가 부족합니다.")
                return

            self.bid_user = ctx.author
            self.bid_money = bid
            self.auction_str = f"{ctx.author.mention}님이 {bid} ZEN에 입찰하였습니다!"

            await ctx.send(self.auction_str)

        except Exception as e:
            print("!입찰", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')


def setup(bot):
    bot.add_cog(경매(bot))