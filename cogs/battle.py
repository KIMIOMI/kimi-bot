import asyncio
import random
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
from utils.dbctrl import db
from utils.event import event

monster_json = {
    "하급빌런": {'name': '하급 빌런', 'current_hp': 5, 'att': 1, 'def': 1, 'exp': 10, 'reward': 10},
    "중급빌런": {'name': '중급 빌런', 'current_hp': 50, 'att': 20, 'def': 11, 'exp': 100, 'reward': 50},
    "상급빌런": {'name': '상급 빌런', 'current_hp': 500, 'att': 80, 'def': 50, 'exp': 400, 'reward': 200},
    "빌런대장": {'name': '빌런 대장', 'current_hp': 1000, 'att': 110, 'def': 40, 'exp': 800, 'reward': 400}
}



def is_channel(*channelId):
    def predicate(ctx):
        result = False
        for channel in channelId:
            if ctx.message.channel.id == channel:
                result = True
        return result

    return commands.check(predicate)


async def add_exp(id: int, level: int, exp_now: int, exp: int, hp: int, total_hp: int):
    exp_total = exp_now + exp
    next_exp = round(0.04 * (level ** 3) + 0.8 * (level ** 2) + 2 * level)
    ## level up
    if exp_total > next_exp:
        exp_now = exp_total - next_exp
        await db.ecouser.update_one({"id": id}, {"$inc": {"level": 1, "att": 2, "def": 2, "health": 20},
                                                 "$set": {"exp": exp_now, "current_hp": total_hp + 20}})
        return True
    else:
        await db.ecouser.update_one({"id": id}, {"$set": {"exp": exp_total, "current_hp": hp}})
        return False


def battle(opponent, user):
    o_hp = opponent["current_hp"]
    o_att = opponent["att"]
    o_def = opponent["def"]

    u_hp = user["current_hp"]
    u_att = user["att"]
    u_def = user["def"]

    round_ = 0

    while (o_hp * u_hp) > 0 and round_ < 10:
        o_hp -= round((u_att - o_def) * random.randint(5, 10) / 10) if (u_att - o_def) > 0 else random.randint(1, 5)
        u_hp -= round((o_att - u_def) * random.randint(5, 10) / 10) if (o_att - u_def) > 0 else random.randint(1, 5)
        round_ += 1
        # print("{} 라운드 m_hp = {} u_hp = {}".format(round_, o_hp, u_hp))

    return round_, o_hp, u_hp


async def weapon_check(id, weapon, user):
    armed_weapon_name = db.market.armed_weapon_name_split(weapon)
    armed_item, index = await db.update_upgrade_item(id, armed_weapon_name)
    if armed_item is None:
        response = "착용 무기 에러 관리자에게 문의 주세요"
        return False, False, 0, 0, response
    armed_item = armed_item['bag'][0]
    if '내구도' in armed_item[2]:
        durability = armed_item[2]["내구도"]
    else:
        durability = 100

    if durability <= 0:
        battle_user = {"current_hp": user["current_hp"] - armed_item[2]["health"],
                       "att": user["att"] - armed_item[2]["att"], "def": user["def"] - armed_item[2]["def"]}
    else:
        battle_user = user
    return index, durability, battle_user


async def hunting(userd: discord.Member, monster, user):
    id = userd.id
    reward = monster["reward"]
    u_level = user["level"]
    u_exp = user["exp"]
    u_total_hp = user["health"]
    exp = monster["exp"]
    response = ""

    weapon = user["armed"]["weapon"]
    if weapon != '':
        index, durability, battle_user = await weapon_check(id, weapon, user)
    else:
        durability = 0
        battle_user = user

    if durability <= 0:
        user_bal = await db.update_user(id)
        user_wallet = user_bal["wallet"]
        if user_wallet < reward:
            response = "무기가 없이 싸우면 ZEN을 털립니다. 지갑에 충분한 ZEN이 없어 도망 칩니다."
            return False, False, 0, 0, response
        else:
            await db.add_wallet(id, -reward)
            response += f"무기가 없이 싸워 {reward} ZEN을 털렸습니다.\n"

    round_, m_hp, u_hp = battle(monster, battle_user)

    durability -= round_
    if durability <= 0:
        durability = 0
        response += f"무기 내구도가 {durability}이거나 무기를 장착하지 않아 맨몸입니다.\n"
    else:
        response += f"무기 내구도가 {durability}이 되었습니다.\n"
    if weapon != '':
        await db.ecobag.update_one({"id": id}, {"$set": {f"bag.{index}.2.내구도": durability}})

    if round_ >= 10:
        exp = round(exp * 0.3)
        response += f"{monster['name']}과 승부가 나지 않아 경험치를 일부 획득합니다.\n"

    if u_hp > 0:
        response += f"<{userd.mention}> 사냥에 성공하였습니다. 경험치 {exp}을 획득하였습니다.\n현재 체력 : {u_hp}"
        if await add_exp(id, u_level, u_exp, exp, u_hp, u_total_hp):
            response += f"{userd.mention}님 축하합니다. 레벨 업 하였습니다"
            return True, True, exp, u_hp, response
        else:
            return True, False, exp, u_hp, response
    elif u_hp <= 0:
        response += f"<{userd.mention}> 사냥에 실패하였습니다. 체력 회복이 필요합니다."
        await db.update_user_current_hp(id, 0)
        return False, False, 0, 0, response


class 사냥(commands.Cog):
    """ 사냥터 명령어 """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Battle Cog Loaded Succesfully")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["사냥터"], db.channel_data["주막"], db.channel_data["무기상점"], db.channel_data["강화"])
    async def 프로필(self, ctx, user: discord.Member = None):
        """ 유저의 스탯을 확인합니다. (!프로필)
         """
        try:
            if user is None:
                user = ctx.author
            user_profile = await db.update_battle_user(user.id)
            eka_role = discord.utils.find(lambda r: r.id == 950255167264141412, ctx.message.guild.roles)
            mudrA_role = discord.utils.find(lambda r: r.id == 950255295786016768, ctx.message.guild.roles)
            gItA_role = discord.utils.find(lambda r: r.id == 950255426740568105, ctx.message.guild.roles)

            nation = ' '
            if eka_role in user.roles:
                nation = 'eka(에카, एक)'
            if mudrA_role in user.roles:
                nation = 'mudrA(무드라, मुद्रा)'
            if gItA_role in user.roles:
                nation = 'gItA(기타, गीता)'

            embed = discord.Embed(
                timestamp=ctx.message.created_at,
                title=f"{user.name}의 프로필",
                description=f"이름: `{user.name}`　　　국가 :`{nation}`\n레벨: `{user_profile['level']}`　　　경험치: `{user_profile['exp']}`\n착용무기: `{user_profile['armed']['weapon']}`",
                color=0xFF0000,
            )
            embed.add_field(
                name="스탯",
                value=f"공격력: `{user_profile['att']}`\n방어력: `{user_profile['def']}`\n체력: `{user_profile['health']}`"
            )
            ment = ''
            for skill in user_profile['skill']:
                ment += f"{skill['name']} lv:{skill['level']}\n"
            embed.add_field(
                name="스킬",
                value=ment,
            )
            ment = ''
            for title in user_profile['title']:
                ment += f"{title['name']} ({title['rarity']})\n"
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
            print("!프로필 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["사냥터"])
    async def 사냥(self, ctx, monster: str):
        """ 사냥을 시작합니다. (!사냥 [몬스터]) 현재 사냥 가능한 빌런 : 상급빌런, 중급빌런, 하급빌런
        """
        try:
            user = ctx.author
            user_profile = await db.update_battle_user(user.id)

            if monster in monster_json.keys():
                monster = monster_json[monster]
            else:
                await ctx.send("없는 몬스터 입니다.")
                return

            hunting_result, level_up, gain_exp, u_hp, response = await hunting(user, monster, user_profile)
            await ctx.send(response)

        except Exception as e:
            print("!사냥 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["사냥터"], db.channel_data["전투장"])
    async def 전투(self, ctx, opponent: discord.Member):
        """ 전투를 시작합니다. (!전투 [유저])
        """
        try:
            user = ctx.author
            if opponent.id == db.bot_id:
                await ctx.send('나를 건들이지 마십시오!')
                return
            user_profile = await db.update_battle_user(user.id)
            opponent_profile = await db.update_battle_user(opponent.id)
            user_bal = await db.update_user(user.id)
            opponent_bal = await db.update_user(opponent.id)

            if user_profile is None or opponent_profile is None or user_bal is None or opponent_bal is None:
                ctx.send("없는 유저입니다.")
                return

            user_weapon = user_profile["armed"]["weapon"]
            opponent_weapon = opponent_profile["armed"]["weapon"]
            user_wallet = user_bal["wallet"]
            opponent_wallet = opponent_bal["wallet"]

            if user_weapon != '':
                user_weapon_index, user_weapon_durability, battle_user = await weapon_check(user.id, user_weapon, user_profile)
            else:
                battle_user = user_profile

            if opponent_weapon != '':
                opponent_weapon_index, opponent_weapon_durability, battle_opponent = await weapon_check(opponent.id, opponent_weapon, opponent_profile)
            else:
                battle_opponent = opponent_profile

            round_, o_hp, u_hp = battle(battle_opponent, battle_user)

            if user_weapon != '':
                user_weapon_durability -= round_
                if user_weapon_durability < 0:
                    user_weapon_durability = 0
                await db.ecobag.update_one({"id": user.id}, {"$set": {f"bag.{user_weapon_index}.2.내구도": user_weapon_durability}})
            if opponent_weapon != '':
                opponent_weapon_durability -= round_
                if opponent_weapon_durability < 0:
                    opponent_weapon_durability = 0
                await db.ecobag.update_one({"id": opponent.id},
                                       {"$set": {f"bag.{opponent_weapon_index}.2.내구도": opponent_weapon_durability}})

            message = await ctx.send(f"{user.mention}님이 {opponent.mention}님에게 전투를 신청 하였습니다.\n"
                                     f"<{user.mention}> 공격력 : {battle_user['att']}, 방어력 : {battle_user['def']}, 체력 : {battle_user['current_hp']}\n"
                                     f"<{opponent.mention}> 공격력 : {battle_opponent['att']}, 방어력 : {battle_opponent['def']}, 체력 : {battle_opponent['current_hp']}\n")
            await asyncio.sleep(2)
            await message.edit(content='전투중 ..')
            await asyncio.sleep(3)
            if o_hp <= 0 < u_hp:
                rob_price = round(opponent_wallet * (round_ / 100) * 5)
                if rob_price < user_wallet * 0.1:
                    rob_price = round(user_wallet * 0.1)
                await db.update_user_current_hp(opponent.id, 0)
                await db.update_user_current_hp(user.id, u_hp)
                await db.ecomoney.update_one({"id": user.id}, {"$inc": {"wallet": +rob_price}})
                await db.ecomoney.update_one({"id": opponent.id}, {"$inc": {"wallet": -rob_price}})
                await message.edit(content=
                    f"{user.mention} 님이 승리하였습니다. {opponent.mention} 님의 지갑에 있는 ZEN 중 {rob_price} ZEN을 빼앗았습니다. "
                    f"\n{user.mention}님의 남은 체력 : {u_hp}"
                    f"\n{opponent.mention}님의 남은 체력 : 0")
            elif u_hp <= 0 < o_hp:
                rob_price = round(user_wallet * (round_ / 100) * 5)
                if rob_price < opponent_wallet * 0.1:
                    rob_price = round(opponent_wallet * 0.1)
                await db.update_user_current_hp(user.id, 0)
                await db.update_user_current_hp(opponent.id, o_hp)
                await db.ecomoney.update_one({"id": opponent.id}, {"$inc": {"wallet": +rob_price}})
                await db.ecomoney.update_one({"id": user.id}, {"$inc": {"wallet": -rob_price}})
                await message.edit(content=
                    f"{opponent.mention} 님이 승리하였습니다. {user.mention} 님의 지갑에 있는 ZEN 중 {rob_price} ZEN을 빼앗았습니다. "
                    f"\n{opponent.mention}님의 남은 체력 : {o_hp}"
                    f"\n{user.mention}님의 남은 체력 : 0")
            elif u_hp > 0 and o_hp > 0:
                await db.update_user_current_hp(user.id, u_hp)
                await db.update_user_current_hp(opponent.id, o_hp)
                await message.edit(content=f"{user.mention} VS {opponent.mention} 의 자웅을 가릴 수 없습니다. 더 강해지고 다시 도전하시지요"
                               f"\n{user.mention}님의 남은 체력 : {u_hp}"
                               f"\n{opponent.mention}님의 남은 체력 : {o_hp}")
            else:
                await db.update_user_current_hp(user.id, 0)
                await db.update_user_current_hp(opponent.id, 0)
                await message.edit(content=f"{user.mention} VS {opponent.mention} 둘다 체력이 바닥 이구만! 수련을 더 열심히 하고 전투를 하시지요"
                               f"\n{user.mention}님의 남은 체력 : 0"
                               f"\n{opponent.mention}님의 남은 체력 : 0")

        except Exception as e:
            print("!전투 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["사냥터"], db.channel_data["무기상점"], db.channel_data["강화"])
    async def 착용(self, ctx, *, name: str = None):
        """ 무기를 착용합니다. (!착용 "아이템 명")
        """
        try:
            user = ctx.author
            user_profile = await db.update_battle_user(user.id)
            name = db.market.item_abbreviation(name)
            item, _ = await db.update_upgrade_item(user.id, name)
            armed_weapon = user_profile['armed']['weapon']
            if armed_weapon == '':
                att, defense, hp = 0, 0, 0
            else:
                armed_weapon_name = db.market.armed_weapon_name_split(armed_weapon)
                armed_item, _ = await db.update_upgrade_item(user.id, armed_weapon_name)
                if armed_item is None:
                    await ctx.send("에러 발생 관리자에게 문의해 주세요! 착용무기 에러")
                    return
                armed_item = armed_item['bag'][0]
                att = -armed_item[2]["att"]
                defense = -armed_item[2]["def"]
                hp = -armed_item[2]["health"]

            if item is not None:
                item = item['bag'][0]
                att += item[2]["att"]
                defense += item[2]["def"]
                hp += item[2]["health"]
                up = item[2]["강화"]
                await db.arm_weapon(user.id, name, up, att, defense, hp)
                await ctx.send(f"{name}({up}강)을 착용 하였습니다.")
            else:
                if name is None:
                    await db.disarm_weapon(user.id, att, defense, hp)
                    await ctx.send(f"무장을 해제 하였습니다.")
                else:
                    await ctx.send('가방에 없는 아이템 입니다.')

        except Exception as e:
            print("!착용 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["사냥터"], db.channel_data["무기상점"], db.channel_data["강화"])
    async def 해제(self, ctx):
        """ 착용 중인 무기를 해제 합니다. (!착용 "아이템 명")
        """
        try:
            user = ctx.author
            user_profile = await db.update_battle_user(user.id)
            armed_weapon = user_profile['armed']['weapon']

            if armed_weapon == '':
                await ctx.send("착용한 무기가 없습니다.")
                return
            else:
                armed_weapon_name = db.market.armed_weapon_name_split(armed_weapon)
                armed_item, _ = await db.update_upgrade_item(user.id, armed_weapon_name)
                if armed_item is None:
                    await ctx.send("에러 발생 관리자에게 문의해 주세요! 착용무기 에러")
                    return
                armed_item = armed_item['bag'][0]
                att = -armed_item[2]["att"]
                defense = -armed_item[2]["def"]
                hp = -armed_item[2]["health"]

            await db.disarm_weapon(user.id, att, defense, hp)
            await ctx.send(f"무장을 해제 하였습니다.")

        except Exception as e:
            print("!착용 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 300, BucketType.user)
    @is_channel(db.channel_data["사냥터"], db.channel_data["주막"])
    async def 회복(self, ctx):
        """ 20 Zen을 사용하여 현재 체력을 회복합니다. 회복력 = 레벨 * 20hp(!회복) """
        try:
            user = ctx.author
            user_profile = await db.update_battle_user(user.id)
            user_bal = await db.update_user(user.id)
            user_wallet = user_bal['wallet']
            if user_wallet < 20:
                await ctx.send("지갑에 20 ZEN이 없어 힐을 받을 수 없습니다.")
                return
            u_level = user_profile['level']
            u_hp = user_profile['current_hp']
            u_hp += 20 * u_level
            if u_hp > user_profile['health']:
                u_hp = user_profile['health']
            await db.update_user_current_hp(user.id, u_hp)
            await db.add_wallet(user.id, -20)
            await ctx.send(f"{user.mention}의 체력이 회복되었습니다"
                           f"현재 체력은 {u_hp} 입니다.")

        except Exception as e:
            print("!회복 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["무기상점"])
    async def 수리(self, ctx, *, name: str):
        """ Zen을 사용하여 무기를 수리합니다. (!수리 [아이템명]) """
        try:
            user = ctx.author
            user_bal = await db.update_user(user.id)
            name = db.market.item_abbreviation(name)
            item, index = await db.update_upgrade_item(user.id, name)

            if item is not None:
                item = item['bag'][0]
                durability = item[2]['내구도']
                price = round(item[2]['강화'] * (100 - item[2]['강화확률']) * (100 - durability) / 200)
                if price < 0:
                    price = 10
                user_bank = user_bal['bank']
                if user_bank < price:
                    await ctx.send(f"은행에 {price} ZEN이 없어 수리를 받을 수 없습니다.")
                    return

                await db.ecobag.update_one({"id": user.id}, {"$set": {f"bag.{index}.2.내구도": 100}})
                await db.add_bank(user.id, -price)
                await ctx.send(f"{user.mention}의 {name}이 수리 되었습니다."
                               f"수리 비용은 {price} ZEN 입니다.")
            else:
                await ctx.send('가방에 없는 아이템 입니다.')

        except Exception as e:
            print("!수리 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 300, BucketType.user)
    @is_channel(db.channel_data["사냥터"])
    async def 보스사냥(self, ctx):
        """ 보스 레이드에 참가합니다. (!보스사냥) """
        try:
            if not event.isboss:
                await ctx.send("현재 보스레이드 시간이 아닙니다.")
                return

            user = ctx.author
            user_profile = await db.update_battle_user(user.id)
            if user_profile is None:
                ctx.send("없는 유저입니다.")
                return

            if user_profile['current_hp'] <= 0:
                ctx.send('체력이 충분하지 않아 참가할 수 없습니다.')
                return

            user_weapon = user_profile["armed"]["weapon"]

            if user_weapon != '':
                user_weapon_index, user_weapon_durability, battle_user = await weapon_check(user.id, user_weapon,
                                                                                            user_profile)
            else:
                battle_user = user_profile
                user_weapon_durability = 0

            round_, boss_hp, u_hp = battle(event.boss, battle_user)

            if user_weapon != '':
                user_weapon_durability -= round_
                if user_weapon_durability < 0:
                    user_weapon_durability = 0
                await db.ecobag.update_one({"id": user.id}, {"$set": {f"bag.{user_weapon_index}.2.내구도": user_weapon_durability}})

            damage = event.boss['current_hp'] - boss_hp

            point = round(damage * (10 + (2 * (11 - round_))) / 10)

            db.ecouser.update_one({"id":user.id}, {"$inc": {"point": point}})
            await ctx.send(f"보스를 공격합니다 {point} 기여도 포인트 획득!\n무기의 내구도가 {user_weapon_durability} 남았습니다.")

        except Exception as e:
            print("!보스사냥 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')


def setup(bot):
    bot.add_cog(사냥(bot))
