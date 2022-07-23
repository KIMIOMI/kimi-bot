import asyncio
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
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

boss_json = {
    "빌런왕": {'name': '빌런왕', 'current_hp': 2000, 'att': 20, 'def': 110, 'exp': 0, 'reward': 600}
}

class 이벤트(commands.Cog):
    """ 이벤트 관련 명령어 """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("event Cog Loaded Succesfully")

    @commands.command()
    @commands.has_role("mods")
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["관리자"])
    async def 이벤트(self, ctx, name: str, time: int = None):
        """ 이벤트를 발생시킵니다. (관리자용) (!이벤트 [이벤트명]) """
        try:
            if name == "지진":
                if time == None:
                    time = 5
                if time > 60:
                    await ctx.send("지진 이벤트 시간은 10 분 이내로 설정해주세요!")
                event.rob_event = True
                msg_channel = ctx.guild.get_channel(db.channel_data["주막"])
                await msg_channel.send(f"{ctx.guild.get_role(db.mention_role).mention} 지진이 발생했습니다! 지진이 발생했습니다!!")
                await asyncio.sleep(60 * time)
                event.rob_event = False
                await msg_channel.send(f"{ctx.guild.get_role(db.mention_role).mention} 지진이 멈췄습니다!")
            elif name == "보스":
                if time == None:
                    time = 30
                if time > 60:
                    await ctx.send("보스 이벤트 시간은 60 분 이내로 설정해주세요!")
                if event.isboss:
                    await ctx.send("현재 보스레이드 중 입니다.")
                    return
                event.isboss = True
                event.boss = boss_json['빌런왕']
                msg_channel = ctx.guild.get_channel(db.channel_data["사냥터"])
                await msg_channel.send(f"{ctx.guild.get_role(db.mention_role).mention} 보스가 등장 했습니다. 보스가 등장했습니다!! 보스 이름 {event.boss['name']}")
                await asyncio.sleep(60 * time)
                event.isboss = False
                event.boss = ''
                await msg_channel.send(f"{ctx.guild.get_role(db.mention_role).mention} 보스 사냥을 완료 하였습니다. 모든 기여도 정산이 완료 되었습니다.")
            else:
                await ctx.send('없는 명령어 입니다.')


        except Exception as e:
            print("!이벤트 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

def setup(bot):
    bot.add_cog(이벤트(bot))