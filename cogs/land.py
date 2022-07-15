import discord
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


class 땅(commands.Cog):
    """ 땅 관련 명령어 """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Land Cog Loaded Succesfully")

    # Buy land
    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["부동산"])
    async def 땅구매(self, ctx, amount: int = 1):
        """ 100 ZEN으로 1평의 땅을 구매합니다. (!땅구매 [수량]) """
        try:
            if amount <= 0 or amount > 100:
                await ctx.send("한번에 0에서 100평 이하의 땅을 구매가능합니다.")
                return
            await db.update_user(ctx.author.id)
            bal = await db.ecomoney.find_one({"id": ctx.author.id})

            price = db.market.land["price"] * amount

            u_bal = bal["bank"]

            if u_bal < price:
                await ctx.send("은행에 돈이 부족합니다.")
                return

            await db.add_bank(ctx.author.id, -price)
            await db.add_land(ctx.author.id, amount)
            await ctx.send(f"축하합니다! 당신이 {price} ZEN을 이용해 마하드비파 영토 {amount}평을 구매했습니다. 구웃~👍 추매 해서 땅부자가 되보자!")
        except Exception as e:
            print("!땅구매", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    # send your land to another user
    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["부동산"])
    async def 땅증여(self, ctx, user: discord.Member, amount: int):
        """ 보유중인 땅을 다른 사람에게 증여합니다. (!땅증여 [유저명] [수량]) """
        try:
            if ctx.author.id == user.id:
                await ctx.send('자기 자신에게 증여할 수 없습니다.')
            else:
                await db.update_user(user.id)
                await db.update_user(ctx.author.id)
                user_bal = await db.ecomoney.find_one({"id": user.id})
                member_bal = await db.ecomoney.find_one({"id": ctx.author.id})
                mem_land = member_bal["land"]
                user_bank = user_bal["land"]
                if amount > mem_land or amount > 100:
                    await ctx.send('증여할 땅 수량을 다시 확인하세요(1회 최대 100평의 땅을 증여 할 수 있습니다.)')
                elif amount <= 0:
                    await ctx.send('땅 수량을 다시 확인하세요')
                else:
                    await db.ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"land": -amount}})
                    await db.ecomoney.update_one({"id": user.id}, {"$inc": {"land": +amount}})
                    await ctx.send(f'{ctx.author.mention}이 {user.mention}에게 {amount}평의 땅을 송금했습니다.')
        except Exception as e:
            print("!땅증여", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')


def setup(bot):
    bot.add_cog(땅(bot))