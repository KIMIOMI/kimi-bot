import datetime
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
import json
import random
from utils.dbctrl import db

mydb = db()

def is_channel(channelId):
    def predicate(ctx):
        return ctx.message.channel.id == channelId

    return commands.check(predicate)


class Battle(commands.Cog):
    """ Commands related to Battle"""

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print("Battle Cog Loaded Succesfully")


    @commands.Cog.listener()
    async def on_message(self, message):
        pass

    @commands.command(aliases=["프로필"])
    @cooldown(1, 2, BucketType.user)
    #@is_channel(channel_id)
    async def profile(self, ctx, user: discord.Member = None):
        """ 유저의 스탯을 확인합니다.(ko: !프로필) """
        if user is None:
            user = ctx.author
        try:
            user_profile = await mydb.update_battle_user(user.id)

            embed = discord.Embed(
                timestamp=ctx.message.created_at,
                title=f"{user.name}의 프로필",
                description=f"이름: `{user.name}`\n레벨: `{user_profile['level']}`\n착용무기: `{user_profile['armed']['weapon']}`",
                color=0xFF0000,
            )
            embed.add_field(
                name="스탯",
                value=f"공격력: `{user_profile['att']}`\n방어력: `{user_profile['def']}`\n체력: `{user_profile['health']}`"
           )
            ment = ''
            for skill_name, skill in user_profile['skill'].items():
                ment += f"{skill_name} lv:{skill['level']}\n"
            embed.add_field(
                name="스킬",
                value=ment,
            )
            ment = f''
            for title_name, title in user_profile['title'].items():
                ment += f"{title_name} ({title})\n"
            embed.add_field(
                name="칭호",
                value=ment,
            )
            embed.set_footer(
                text=f"요청자: {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
            )
            embed.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
            await ctx.send('취..익 취이..ㄱ')


def setup(bot):
    bot.add_cog(Battle(bot))
