import random
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
from utils.dbctrl import Db


db = Db()

monster_json = {
    "하급빌런": {'name': '하급 빌런', 'health': 5, 'att': 1, 'def': 1, 'exp': 10, 'reward': 0},
    "중급빌런": {'name': '중급 빌런', 'health': 50, 'att': 20, 'def': 11, 'exp': 100, 'reward': 100},
    "상급빌런": {'name': '상급 빌런', 'health': 500, 'att': 80, 'def': 50, 'exp': 500, 'reward': 1000},
}


def is_channel(*channelId):
    def predicate(ctx):
        result = False
        for channel in channelId:
            if ctx.message.channel.id == channel:
                result = True
        return result

    return commands.check(predicate)


async def add_exp(id : int, level : int, exp_now: int, exp: int, hp: int):
        exp_total = exp_now + exp
        next_exp = round(0.04 * (level ** 3) + 0.8 * (level ** 2) + 2 * level)
        ## level up
        if exp_total > next_exp:
            exp_now = exp_total - next_exp
            await db.ecouser.update_one({"id": id}, {"$inc": {"level": 1, "att": 2, "def": 2, "health": 20}})
            await db.ecouser.update_one({"id": id}, {"$set": {"exp": 0}})
            await db.update_user_current_hp(id, hp + 20)
            return True
        else:
            await db.ecouser.update_one({"id": id}, {"$set": {"exp": exp_total}})
            return False


async def hunting(id: int, monster, user):
    m_hp = monster["health"]
    m_att = monster["att"]
    m_def = monster["def"]
    m_exp = monster["exp"]
    m_reward = monster["reward"]
    u_hp = user["current_hp"]
    u_att = user["att"]
    u_def = user["def"]
    u_level = user["level"]
    u_exp = user["exp"]
    u_total_hp = user["health"]
    round_ = 0
    if u_hp <= 0:
        return False, False, 0, 0

    while (m_hp * u_hp) > 0:
        m_hp -= round((u_att - m_def)*random.randint(5, 10)/10) if (u_att - m_def) > 0 else random.randint(1, 5)
        u_hp -= round((m_att - u_def)*random.randint(5, 10)/10) if (m_att - u_def) > 0 else random.randint(1, 5)
        print("{} 라운드 m_hp = {} u_hp = {}".format(round_, m_hp, u_hp))
        round_ += 1

    if m_hp <= 0:
        await db.update_user_current_hp(id, u_hp)
        if await add_exp(id, u_level, u_exp, m_exp, u_total_hp):
            return True, True, m_exp, u_hp
        else:
            return True, False, m_exp, u_hp
    elif u_hp <= 0:
        await db.update_user_current_hp(id, 0)
        return False, False, 0, 0


class 사냥(commands.Cog):
    """ 사냥터 명령어 """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Battle Cog Loaded Succesfully")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["사냥터"], db.channel_data["주막"], db.channel_data["무기상점"])
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

            nation =' '
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

            hunting_result, level_up, gain_exp, u_hp = await hunting(user.id, monster, user_profile)
            if hunting_result:
                await ctx.send(f"<{user.mention}> 사냥에 성공하였습니다. 경험치 {gain_exp}을 획득하였습니다."
                               f"\n현재 체력 : {u_hp}")
            else:
                await ctx.send(f"<{user.mention}> 사냥에 실패하였습니다. 체력 회복이 필요합니다.")
            if level_up:
                await ctx.send(f"{user.mention}님 축하합니다. 레벨 업 하였습니다")

        except Exception as e:
            print("!사냥 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    @is_channel(db.channel_data["사냥터"], db.channel_data["무기상점"])
    async def 착용(self, ctx, name: str = None):
        """ 무기를 착용합니다. (!착용 "아이템 명") 띄어 쓰기가 있는 아이템은 쌍 따옴표로 감싸주세요!
        """

        try:
            user = ctx.author
            user_profile = await db.update_battle_user(user.id)
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
            await db.update_wallet(user.id, user_wallet - 20)
            await ctx.send(f"{user.mention}의 체력이 회복되었습니다"
                           f"현재 체력은 {u_hp} 입니다.")

        except Exception as e:
            print("!회복 ", e)
            await ctx.send('취..익 취이..ㄱ 관리자를 불러 나를 고쳐주세요')

def setup(bot):
    bot.add_cog(사냥(bot))
