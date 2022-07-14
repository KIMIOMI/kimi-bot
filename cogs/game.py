import random
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
from utils.dbctrl import Db


db = Db()


def is_channel(*channelId):
    def predicate(ctx):
        result = False
        for channel in channelId:
            ctx.message.channel.id == channel
            result = True
        return result

    return commands.check(predicate)


class 게임(commands.Cog):
    """ 게임 명령어 """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Battle Cog Loaded Succesfully")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["도박장"])
    async def 배팅(self, ctx, amount: int):
        """ 배팅게임을 시작합니다. (!배팅 [배팅금액]) """
        try:
            await db.update_user(ctx.author.id)
            user_bal = await db.ecomoney.find_one({"id": ctx.author.id})

            if amount > user_bal["wallet"]:
                await ctx.send('봇짐에 잔고가 부족합니다.')
            elif amount <= 0:
                await ctx.send('0 ZEN 이상을 배팅해주세요.')
            # elif amount > 1000:
            #     await ctx.send('최대 1000 ZEN 만 배팅 가능합니다.')
            else:
                num = random.randint(1, 100)
                if num <= 50:
                    await db.ecomoney.update_one({"id": ctx.author.id},
                                                 {"$inc": {"wallet": +int(round(amount / 2, 0))}})
                    await ctx.send(f'당신이 승리해 Hope에게서 {int(round(amount / 2, 0))} ZEN을 빼앗았습니다. 후…. 봐줬다.')
                else:
                    await db.ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                    await ctx.send(f'당신이 패배해 Hope가 {amount} ZEN을 가져갔습니다. 메렁😋')
        except Exception as e:
            print("!배팅", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["도박장"])
    async def 주사위(self, ctx, amount: int):
        """ 주사위 게임을 시작합니다. (!주사위 [배팅액]) """
        try:
            await db.update_user(ctx.author.id)
            user_bal = await db.ecomoney.find_one({"id": ctx.author.id})

            if amount > user_bal["wallet"]:
                await ctx.send('봇짐에 잔고가 부족합니다.')
            elif amount <= 0:
                await ctx.send('0 ZEN 이상을 배팅해주세요.')
            # elif amount > 1000:
            #     await ctx.send('최대 1000 ZEN 만 배팅 가능합니다.')
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
                    await db.ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": +(amount)}})
                    _color = 0xFF0000
                elif user_dice == robot_dice:
                    result = f"당신의 {amount} ZEN을 Hope가 강탈하지 못했습니다. Hope한테 삥뜯으려면 다시 ㄱㄱ🤡"
                    _color = 0xFAFA00
                else:
                    await db.ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                    result = f'당신은 Hope에게 {amount} Zen을 강탈당했습니다. 약 오르지? 메렁😋'
                    _color = 0x00FF56

                embed = discord.Embed(title="던져! 던져! 주사위 게임 결과!", description="누가 누가 이겼을까? 돈놓고 돈먹기 가즈앗!",
                                      color=_color)
                embed.add_field(name="Hope's Number", value=f":game_die: {robot_dice}", inline=True)
                embed.add_field(name=f"{ctx.author.name}'s Number", value=f":game_die: {user_dice}", inline=True)
                embed.set_footer(text=result)
                await ctx.send(embed=embed)

        except Exception as e:
            print("!주사위", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["가위바위보"])
    async def 가바보(self, ctx, userRPS: str, amount: int):
        """ 가위바위보 게임을 시작합니다. (!가바보 [가위, 바위, 보] [배팅액]) """
        try:
            await db.update_user(ctx.author.id)
            user_bal = await db.ecomoney.find_one({"id": ctx.author.id})

            if amount > user_bal["wallet"]:
                await ctx.send('봇짐에 잔고가 부족합니다.')
            elif amount <= 0:
                await ctx.send('0 ZEN 이상을 배팅해주세요.')
            # elif amount > 10000:
            #     await ctx.send('최대 1000 ZEN 만 배팅 가능합니다.')
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
                        await db.ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": +amount}})
                        _color = 0xFF0000
                    else:
                        result = f'당신은 Hope에게 졌다!'
                        await db.ecomoney.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                        _color = 0x00FF56

                    embed = discord.Embed(title="가위바위보 게임 결과!", description="누가 누가 이겼을까? 돈놓고 돈먹기 가즈앗!", color=_color)
                    embed.add_field(name="Hope", value=botEmoji, inline=True)
                    embed.add_field(name=f"{ctx.author.name}", value=userEmoji, inline=True)
                    embed.set_footer(text=result)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("가위 바위 보 중에 하나를 선택하세요.")
        except Exception as e:
            print("!가바보", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')


def setup(bot):
    bot.add_cog(게임(bot))