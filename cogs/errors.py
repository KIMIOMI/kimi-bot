import math
import sys
import traceback

import discord
from discord.ext import commands


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Error cog loaded successfully")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, "on_error"):
            return

        # get the original exception
        error = getattr(error, "original", error)

        if isinstance(error, commands.BotMissingPermissions):
            missing = [
                perm.replace("_", " ").replace("guild", "server").title()
                for perm in error.missing_perms
            ]
            if len(missing) > 2:
                fmt = "{}, and {}".format("**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = " and ".join(missing)

            embed = discord.Embed(
                title="권한이 없습니다.",
                description=f"권한 **{fmt}** 이 필요합니다.",
                color=0xFF0000,
            )
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send("This command has been disabled.")
            return

        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="쿨다운",
                description=f"이 명령어를 다시 실행하기 위해선 {math.ceil(error.retry_after)}초 기다려주세요.",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingPermissions):
            missing = [
                perm.replace("_", " ").replace("guild", "server").title()
                for perm in error.missing_perms
            ]
            if len(missing) > 2:
                fmt = "{}, and {}".format("**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = " and ".join(missing)
            embed = discord.Embed(
                title="권한이 없습니다.",
                description=f"**{fmt}** 권한이 필요합니다.",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.UserInputError):
            embed = discord.Embed(
                title="입력 값 없음",
                description=f"추가 입력 값이 필요합니다.",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send("This command cannot be used in direct messages.")
            except discord.Forbidden:
                raise error
            return

        if isinstance(error, discord.errors.Forbidden):
            try:
                embed = discord.Embed(
                    title="Forbidden",
                    description=f"Error - 403 - Forbidden | Missing perms",
                    color=0xFF0000,
                )
                await ctx.send(embed=embed)
            except:
                print("Failed forbidden")
            return

        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                title="채널 확인!.",
                description=f"올바른 채널에서 명령어를 사용하세요",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
            return

        print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)

        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
        )


def setup(bot):
    bot.add_cog(Errors(bot))