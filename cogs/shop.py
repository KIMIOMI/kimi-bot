import random
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
import datetime
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


class 상점(commands.Cog):
    """ 무기 상점 명령어 """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Shop Cog Loaded Succesfully")

    @commands.group(invoke_without_command=True)
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["무기상점"])
    async def 상점(self, ctx):
        """ 상점 목록을 불러옵니다. (!상점) """
        embed = discord.Embed(
            timestamp=ctx.message.created_at,
            title="상점 목록",
            color=0xFF0000,
        )
        embed.add_field(
            name="무기",
            value="무기 상점 | 사용 `!상점 무기`",
            inline=False
        )
        embed.add_field(
            name="가챠",
            value="가챠 상점 | 사용 `!상점 가챠템`",
            inline=False
        )
        embed.set_footer(
            text=f"요청자 : {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
        )

        await ctx.send(embed=embed)

    @상점.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["무기상점"])
    async def 무기(self, ctx):
        """ 무기 상점 (!상점 무기) """
        embed = discord.Embed(
            timestamp=ctx.message.created_at,
            title="무기 상점",
            color=0xFF0000,
        )
        for x, item in db.market.market_data["Weapon"].items():
            embed.add_field(
                name=x,
                value=f"공격력: {item['att']} | 방어력: {item['def']} | 체력: {item['health']}\n가격: {item['price']} ZEN",
                inline=False
            )
        embed.set_footer(
            text=f"요청자 : {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
        )
        await ctx.send(embed=embed)

    @상점.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["무기상점"])
    async def 가챠템(self, ctx):
        """ 가챠 상점 (!상점 가챠템) """
        embed = discord.Embed(
            timestamp=ctx.message.created_at,
            title="가챠템 목록",
            color=0xFF0000,
        )
        for x, item in db.market.market_data["item"].items():
            embed.add_field(
                name=x,
                value=f"공격력: {item['att']} | 방어력: {item['def']} | 체력: {item['health']}\n가격: {item['price']} ZEN",
                inline=False
            )
        embed.set_footer(
            text=f"요청자 : {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
        )
        await ctx.send(embed=embed)

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["무기상점"])
    async def 산다(self, ctx, name: str, amount: int = 1):
        """ 상점에서 물건을 구입한다. (!산다 [아이템] [수량]) 아이템 명이 띄워쓰기가 있을경우 "" 쌍따옴표로 감싸주세요 """
        id = ctx.author.id
        if amount <= 0 or amount > 100:
            await ctx.send("한번에 최소 1개에서 최대 100개 까지 구입 가능합니다.")
            return

        bal = await db.update_user(id)
        bag = await db.update_bag(id)
        if bal is None or bag is None:
            await ctx.send("문제 발생! 관리자에게 문의 하세요")

        fg = db.market.items.get(name)

        if fg is None or fg[0] != '무기':
            await ctx.send("취급하지 않는 물건입니다..")
            return

        price = fg[1] * amount
        u_bal = bal["bank"]

        if u_bal < price:
            await ctx.send(f"은행에 충분한 ZEN이 없습니다. 총 가격은 {price} ZEN 입니다.")
            return

        await db.update_bank(ctx.author.id, u_bal - price)
        item, index = await db.update_upgrade_item(id, name)

        _, upPrice, upProbability, att, defense, health, image, _bool = db.market.item(name)
        if _bool is False:
            await ctx.send("취급하지 않는 물건입니다..")
            return

        if item is not None:
            item = item['bag'][0]
            init_amount = item[1]
            final_amount = amount + init_amount

            await db.edit_item(id, index, final_amount)
            await ctx.send(f"{name} {amount}개를 {price} ZEN에 구입하였습니다.")
            return
        else:
            await db.add_item(id, name, amount)
            await ctx.send(f"{name} {amount}개를 {price} ZEN에 구입하였습니다.")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["무기상점"])
    async def 판다(self, ctx, name: str, amount: int = 1):
        """ 상점에 물건을 70%의 가격으로 판매합니다. (!판다 [아이템] [수량]) 아이템 명이 띄워쓰기가 있을경우 "" 쌍따옴표로 감싸주세요 """
        user = ctx.author
        user_profile = await db.update_battle_user(user.id)
        armed_weapon = user_profile["armed"]["weapon"]
        armed_weapon_name = db.market.armed_weapon_name_split(armed_weapon)
        if armed_weapon_name == name:
            await ctx.send("착용 하고 있는 아이템은 팔 수 없습니다.")
            return
        bal = await db.update_user(user.id)
        bag = await db.update_bag(user.id)
        if bal is None or bag is None:
            await ctx.send("문제 발생! 관리자에게 문의 하세요")

        fg = db.market.items.get(name)

        if fg is None:
            await ctx.send("취급하지 않는 물건입니다.")
            return

        if name == '만만한 Hope_Candy의 막대사탕':
            price = int(round(fg[1] * amount * 0.1, 0))
        else:
            price = int(round(fg[1] * amount * 0.7, 0))

        u_bal = bal["bank"]

        item, index = await db.update_upgrade_item(user.id, name)

        if item is not None:
            item = item['bag'][0]
            init_amount = item[1]
            if amount > init_amount:
                await ctx.send("수량을 다시 확인해주세요")
                return

            final_amount = init_amount - amount
            if final_amount == 0:
                await db.remove_item(user.id, name)
                await db.update_bank(user.id, u_bal + price)
            else:
                await db.edit_item(user.id, index, final_amount)
                await db.update_bank(user.id, u_bal + price)
            await ctx.send(f"{name} {amount}개를 판매하였습니다. 총 {price} ZEN을 드리겠습니다.")
        else:
            await ctx.send("없는 물건은 못 팝니다.")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["무기상점"])
    async def 가챠(self, ctx):
        """ 가챠템을 뽑습니다. (!가챠) """

        bal = await db.update_user(ctx.author.id)
        bag = await db.update_bag(ctx.author.id)
        if bal is None or bag is None:
            await ctx.send("문제 발생! 관리자에게 문의 하세요")

        item = db.market.gotcha()
        fg = db.market.items.get(item)

        if fg is None or fg[0] != '가챠':
            await ctx.send("가챠템 민팅 문제 발생! 관리자에게 문의 하세요")
            return
        amount = 1
        price = fg[1] * amount
        name = fg[2]
        u_bal = bal["bank"]

        if u_bal < price:
            await ctx.send(f"은행에 충분한 ZEN이 없습니다. 총 가격은 {price} ZEN 입니다.")
            return

        await db.update_bank(ctx.author.id, u_bal - price)

        for x in bag['bag']:
            if x[0] == item:
                init_amount = x[1]
                final_amount = amount + init_amount
                index = bag['bag'].index(x)
                await db.edit_item(ctx.author.id, index, final_amount)
                await ctx.send(f"축하합니다. {name}를 뽑았습니다. 총 수량 : {final_amount}")
                return

        await db.add_item(ctx.author.id, item, amount)
        await ctx.send(f"축하합니다. {name}를 뽑았습니다. 총 수량 : 1")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["무기상점"], db.channel_data["사냥터"])
    async def 가방(self, ctx, page: int = 1):
        """ 가방을 확인합니다. (!가방 [페이지수]) 1페이지당 10개의 아이템이 표시됩니다. """
        if page > 7 or page < 1:
            await ctx.send("페이지는 1에서 최대 7까지 입니다.")
            return
        bal = await db.update_user(ctx.author.id)
        bag = await db.update_bag(ctx.author.id)
        if bal is None or bag is None:
            await ctx.send("문제 발생! 관리자에게 문의 하세요")

        total = 0
        page_dict = {1: "0-9", 2: "10-20", 3: "20-30", 4: "30-40", 5: "40-50", 6: "50-60", 7: "60-70"}
        intial, final = page_dict[page].split('-')
        for x in bag['bag']:
            total += 1
        if total == 0:
            await ctx.send("가방이 비어있습니다.")
            return

        page_items = bag['bag'][int(intial):int(final) + 1]

        embed = discord.Embed(
            title=f"{ctx.author.name}의 가방",
            description=f"페이지 {page} | 아이템 개수: {total}",
            color=0xFF0000
        )
        for x in page_items:
            fg = db.market.items.get(x[0])
            embed.add_field(name=f"{fg[2]}({x[2]['강화']}강)", value=f"{x[1]}", inline=False)

        embed.set_footer(
            text=f"요청자 : {ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
        )
        await ctx.send(embed=embed)

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["무기상점"], db.channel_data["사냥터"])
    async def 템(self, ctx, name: str):
        """ 자신의 아이템 정보를 확인합니다. (!템 [아이템명]) 아이템 명이 띄워쓰기가 있을경우 "" 쌍따옴표로 감싸주세요 """
        bag = await db.update_bag(ctx.author.id)
        if bag is None:
            await ctx.send("문제 발생! 관리자에게 문의 하세요")
        item, _ = await db.update_upgrade_item(ctx.author.id, name)

        if item is not None:
            item = item['bag'][0]
            init_amount = item[1]
            stats = f'공격력: {item[2]["att"]}\n방어력: {item[2]["def"]}\n체력: {item[2]["health"]}\n'
            upProbability = item[2]["강화확률"]
            upPrice = item[2]["강화비용"]
            total_up = item[2]["강화"]
            image = db.market.item(name)[6]
            embed = discord.Embed(
                title=f'{ctx.author.name}의 {name}({total_up}강)',
                color=discord.Color.gold()
            )

            embed.set_thumbnail(url=image)
            embed.add_field(name="Stats", value=stats, inline=False)
            embed.add_field(name="강화확률", value=f'{upProbability}%', inline=True)
            embed.add_field(name="강화비용", value=f'{upPrice} ZEN', inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send('가방에 없는 아이템 입니다.')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["무기상점"])
    async def 강화(self, ctx, name: str):
        """ 아이템을 강화 합니다. (!강화 [아이템명]) 아이템 명이 띄워쓰기가 있을경우 "" 쌍따옴표로 감싸주세요 """
        user = ctx.author
        user_profile = await db.update_battle_user(user.id)
        armed_weapon = user_profile["armed"]["weapon"]
        armed_weapon_name = db.market.armed_weapon_name_split(armed_weapon)
        if armed_weapon_name == name:
            await ctx.send("착용 하고 있는 아이템은 강화 할 수 없습니다.")
            return
        bal = await db.update_user(user.id)
        bag = await db.update_bag(user.id)
        if bal is None or bag is None:
            await ctx.send("문제 발생! 관리자에게 문의 하세요")
        item, index = await db.update_upgrade_item(user.id, name)

        u_bal = bal["bank"]

        _, upPrice, upProbability, _, _, _, _, _bool = db.market.item(name)
        if _bool is False:
            await ctx.send("없는 아이템 입니다.")
            return

        if upPrice > u_bal:
            await ctx.send('은행에 잔고가 부족합니다.')
            return

        if item is not None:
            item = item['bag'][0]
            init_amount = item[1]
            total_up = item[2]['강화']
            att = round(item[2]['att'] * 1.1)
            defense = round(item[2]['def'] * 1.1)
            health = round(item[2]['health'] * 1.1)

            await db.update_bank(user.id, u_bal - upPrice)
            if random.random() <= (upProbability / 100):
                await db.ecobag.update_one({"id": user.id}, {
                    "$inc": {f"bag.{index}.2.강화": 1, f"bag.{index}.2.강화 성공": 1, f"bag.{index}.2.강화 시도": 1},
                    "$set": {f"bag.{index}.2.att": att, f"bag.{index}.2.def": defense,
                             f"bag.{index}.2.health": health}})

                await ctx.send(f'강화 성공! {user.mention}의 {name}이 {total_up + 1}강이 되었습니다.')
                return
            else:
                await db.ecobag.update_one({"id": user.id}, {
                    "$inc": {f"bag.{index}.2.강화 시도": 1}})
                await ctx.send(f'강화 실패! {ctx.author.mention}의 {name}이 여전히 {total_up}강 입니다.')
                return
        else:
            await ctx.send('가방에 없는 아이템 입니다.')

    # leaderboard
    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["주막"])
    async def 랭킹(self, ctx, field: str):
        """ 각종 랭킹을 확인합니다. (!랭킹 [필드명]) 필드 목록 : 은행, 레벨, 토지 """
        if field == "은행":
            rankings = db.ecomoney.find().sort("bank", -1)
        elif field == "레벨":
            rankings = db.ecouser.find().sort("level", -1)
        elif field == "토지":
            rankings = db.ecomoney.find().sort("land", -1)
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
    bot.add_cog(상점(bot))