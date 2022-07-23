import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
from utils.dbctrl import db


title_json = {
    "강탈자": {'name': '강탈자', 'rarity': 'common'},
}


def is_channel(*channelId):
    def predicate(ctx):
        result = False
        for channel in channelId:
            if ctx.message.channel.id == channel:
                result = True
        return result

    return commands.check(predicate)


class 칭호(commands.Cog):
    """ 칭호 명령어 """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Title Cog Loaded Succesfully")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @commands.has_role("mods")
    @is_channel(db.channel_data["주막"])
    async def 칭호부여(self, ctx, user: discord.Member, title: str):
        """ 유저에게 칭호를 부여합니다.(관리자용) (!칭호부여 [유저] [칭호명]) """
        try:
            if title in title_json.keys():
                title_info = title_json[title]
            else:
                await ctx.send("아직 창조되지 않은 칭호입니다..")
                return
            await db.ecouser.update_one({"id": user.id}, {"$push": {"title": title_info}})

            await ctx.send(f"{user.mention}에게 {title} 칭호를 부여합니다.")

        except Exception as e:
            print("!경매", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

def setup(bot):
    bot.add_cog(칭호(bot))