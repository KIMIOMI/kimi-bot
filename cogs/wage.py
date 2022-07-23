import datetime
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
from utils.dbctrl import db
from utils.twitter_api import twitter_check


def is_channel(*channelId):
    def predicate(ctx):
        result = False
        for channel in channelId:
            if ctx.message.channel.id == channel:
                result = True
        return result

    return commands.check(predicate)


class 돈벌이(commands.Cog):
    """ 돈벌이 관련 명령어 """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Wage Cog Loaded Succesfully")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["출석"])
    async def 출첵(self, ctx):
        """ 출석 체크를 통해 50 ZEN을 지급 받습니다. Aoz_Holder 롤이 있는 경우 100 ZEN을 지급 받습니다. """
        try:
            await db.update_user(ctx.author.id)
            eco = await db.ecomoney.find_one({"id": ctx.author.id})
            gm_time = eco['gm_time']
            if gm_time is not None:
                if (datetime.datetime.utcnow().date() - gm_time.date()).days < 1:
                    await ctx.send("오늘 출첵은 완료! 내일 다시 출첵해주세요.")
                    return

            amount = 50
            for role in ctx.author.roles:
                if role.id == db.holder_role:
                    amount = 100
            await db.add_bank(ctx.author.id, +amount)
            await db.ecomoney.update_one({"id": ctx.author.id}, {"$set": {"gm_time": datetime.datetime.utcnow()}})
            await ctx.send(f'{ctx.author.mention} 에게 {amount} ZEN을 지급했습니다.')
        except Exception as e:
            print("!출첵", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["출석"])
    async def 트윗(self, ctx, link: str):
        """ 트윗을 올려 인증 후 ZEN을 지급 받습니다.(!트윗 [링크]) 인증을 위해서 #AOZ #AgeOfZen #Zenisyou @Age_Of_Zen 의 태그가 있어야 합니다. """
        try:
            await db.update_user(ctx.author.id)
            eco = await db.ecomoney.find_one({"id": ctx.author.id})
            tw_time = eco['tw_time']
            result, createdAt = twitter_check(link)
            if result is False:
                await ctx.send("트윗 글자수, 해시태그, 혹은 링크를 다시 확인해주세요")
                return

            createdAt = datetime.datetime.strptime(createdAt, "%Y-%m-%dT%H:%M:%S.%fZ")

            if tw_time is not None:
                if (createdAt - tw_time).total_seconds() < 7200:
                    await ctx.send("2시간이 지난 새로운 트윗이 없습니다. 새로운 트윗이 있다면 글자 수, 해시태그를 다시 확인해 주세요")
                    return

            amount = 50
            for role in ctx.author.roles:
                if role.id == db.holder_role:
                    amount = 100
            await db.add_bank(ctx.author.id, +amount)
            await db.ecomoney.update_one({"id": ctx.author.id}, {"$set": {"tw_time": createdAt}})
            await ctx.send(f'{ctx.author.mention} 에게 {amount} ZEN을 지급했습니다.')
        except Exception as e:
            print("!트윗", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')


def setup(bot):
    bot.add_cog(돈벌이(bot))