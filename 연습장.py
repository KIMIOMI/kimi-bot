import asyncio

from flask import Flask
from flask import abort, request
import motor.motor_asyncio
import nest_asyncio
import json
import random
import datetime
import numpy as np
from utils.twitter_api import twitter_util as tu
from urllib.parse import urlparse
import re
import math
import os


WINRATE = 2
LOSERATE = 0.5


def 가바보():
    amount = 1000
    total_amount = 5000
    for i in range(1, 10000):
        user_dice = 3
        robot_dice = random.randint(1, 3)
        if robot_dice == 2:
            if random.randint(1, 10) == 9:
                famount = amount * WINRATE
            else:
                famount = amount
            total_amount += famount
        elif robot_dice == 1:
            famount = 0
            total_amount -= famount
        else:
            if random.randint(1, 10) == 9:
                famount = amount / LOSERATE
            else:
                famount = amount
            total_amount -= famount

    print('가바보', total_amount)


def 주사위():
    amount = 1000
    total_amount = 5000

    for i in range(1, 10000):
        user_dice = random.randint(1, 7)
        robot_dice = random.randint(1, 7)
        if user_dice > robot_dice:
            if random.randint(1, 10) == 9:
                famount = amount * WINRATE
            else:
                famount = amount
            total_amount += famount
        elif user_dice == robot_dice:
            pass
        else:
            if random.randint(1, 10) == 9:
                famount = amount / LOSERATE
            else:
                famount = amount
            total_amount -= famount
    print('주사위', total_amount)


def 배팅():
    amount = 1000
    total_amount = 5000

    for i in range(1, 10000):
        num = random.randint(1, 100)
        if num <= 50:
            if random.randint(1, 10) == 9:
                famount = amount * WINRATE
            else:
                famount = amount
            total_amount += famount
        else:
            if random.randint(1, 10) == 9:
                famount = amount / LOSERATE
            else:
                famount = amount
            total_amount -= famount
    print('배팅', total_amount)


def 스플릿(amount, n):
    a = amount
    avg_amount = round(amount / n)

    pieces = []
    for idx in range(1, n):
        remainer = a - sum(pieces)
        at_least = (n - idx) * avg_amount
        max_amount = remainer - at_least

        amount = random.randint(round(max_amount / 2), max_amount)
        pieces.append(random.randint(1, amount))
    pieces.append(a - sum(pieces))
    return pieces


def gatcha():
    with open('./market2.json', encoding='UTF-8') as f:
        d3 = json.load(f)

    # weights = (50 / 17, 40 / 17, 35 / 17, 30 / 17, 25 / 17, 20 / 17, 15 / 17, 10 / 17,
    #            9 / 17, 8 / 17, 7 / 17, 6 / 17, 5 / 17, 4 / 17, 3 / 17, 3 / 17, 1 / 17)
    weights = (80, 20, 10, 5, 25, 20, 15, 10, 9, 8, 7, 6, 5, 4, 3, 3, 1)
    result = {}
    for i in range(1, 10000):
        a = random.choices(list(d3["item"]), weights=weights)
        name = a[0]
        if name not in result.keys():
            result[name] = 1
        else:
            result[name] += 1
    for i in result:
        print(i, result[i])


def 가챠읽기():
    with open('./gatcha.json', encoding='UTF-8') as f:
        d3 = json.load(f)

    ss = "만만한 Hope_Candy의 막대사탕"
    for i, x in enumerate(d3["item"]):
        if ss in x:
            a = x[ss]
            stats = f'공격력: {a["att"]}\n방어력: {a["def"]}\nHP: {a["health"]}\n'
            upProbability = a["강화확률"]
            upPrice = a["강화비용"]

    print(stats)
    print(upProbability)
    print(upPrice)


def 연습():
    keys = ["id", "wallet", "bank", "land", "wage", "inventory", "gm_time"]
    for key in keys:
        a = lambda key: 100 if key == "bank" else (
            datetime.datetime.now() - datetime.timedelta(days=1, hours=1) if key == "gm_time" else 0)
        print(a(key))


items = {}
keys = ["id", "wallet", "bank", "land", "wage", "inventory", "gm_time"]


def open_account(id: int):
    new_user = {"id": id, "wallet": 0, "bank": 100, "land": 0, "wage": 0, "inventory": []}
    # wallet = current money, bank = money in bank
    items.update(new_user)


def update_user(id: int):
    try:
        if id is not None:
            # bal = items.get(id)
            bal = 0
            if bal is None:
                open_account(id)
                bal = items.get(id)
            for key in keys:
                if key in bal:
                    pass
                else:
                    a = lambda key: 100 if key == "bank" else (
                        datetime.datetime.now() - datetime.timedelta(days=1, hours=1) if key == "gm_time" else (datetime.datetime.now() - datetime.timedelta(days=1, hours=1) if key == "tw_time" else 0))

    except Exception as e:
        print(e)


async def upgrade_item(ss:str):
    with open('./data.json') as f:
        d1 = json.load(f)
    with open('./market.json', encoding='UTF-8') as f:
        d2 = json.load(f)
    nest_asyncio.apply()

    mongo_url = d1['mongo']

    cluster = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    ecomoney = cluster["eco"]["money"]
    ecobag = cluster["eco"]["bag"]

    id = 847032918747512872
    bal = await ecomoney.find_one({"id": id})
    bag = await ecobag.find_one({"id": id})

    print(bal)
    print(bag)

    item = d2["Weapon"][ss]

    price = item["강화비용"]
    name = item.keys()
    upProbability = item["강화확률"]
    att = item["att"]
    defense = item["def"]
    health = item["health"]

    u_bal = bal["bank"]

    for x in bag['bag']:
        if x[0] == ss:
            init_amount = x[1]
            index = bag['bag'].index(x)

            if len(x) < 3:
                print("x2 is none")
                json_items = items
                for i in range(0, init_amount):
                    json_items['{}'.format(i+1)] = {"강화": 0, "강화 성공": 0, "강화 시도": 0, "att": att, "def": defense, "health": health}
                print(json_items)
                await ecobag.update_one({"id": id}, {"$set": {f"bag.{index}.2": json_items}})

            if np.random.binomial(1, upProbability/100) == 1:
                print('강화 성공')
                await ecobag.update_one({"id":id}, {"$inc": {f"bag.{index}.2.1.강화": 1, f"bag.{index}.2.1.강화 성공": 1, f"bag.{index}.2.1.강화 시도": 1, f"bag.{index}.2.1.att": 1, f"bag.{index}.2.1.def": 1, f"bag.{index}.2.1.health": 1 }})
            else:
                print('강화 실패')
                await ecobag.update_one({"id": id}, {"$inc": {f"bag.{index}.2.1.강화": 1, f"bag.{index}.2.1.강화 성공": 0, f"bag.{index}.2.1.강화 시도": 1}})


def twitter_check(link):
    with open('./hashTags.json', encoding='UTF-8') as f:
        hashTags = json.load(f)["hashTags"]

    link = urlparse(link)
    username = link.path.split('/')[1]
    tweet = tu()
    headers = tweet.create_headers()

    url = tweet.create_get_user_url(username)
    json_response = tweet.connect_to_endpoint(url[0], headers, url[1])
    user_id = json_response["data"]["id"]

    url = tweet.create_user_timeline_url(user_id)
    json_response = tweet.connect_to_endpoint(url[0], headers, url[1])
    tweets = json_response["data"]

    for tweet in tweets:
        text = tweet["text"]
        id = tweet["id"]
        created_at = tweet["created_at"]
        tweethashTags = re.findall(r"#(\w+)", text)
        print(tweethashTags, created_at)
        hashResult = True
        for hashtag in hashTags:
            if hashtag in tweethashTags:
                hashResult &= True
            else:
                hashResult &= False
        if hashResult:
            return hashResult, created_at

    return False , 0

def time_test():
    date = datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=1)

    # link = 'https://twitter.com/kimi3672/status/1544874169481183232'
    link = 'h'
    result, created_at = twitter_check(link)
    created_at = datetime.datetime.strptime(created_at ,"%Y-%m-%dT%H:%M:%S.%fZ")

    if (created_at.date() - date.date()).days < 1:
        print("true")
    else:
        print("false")

    print(date)
    print(created_at)
    print((created_at.date() - date.date()).days)

def leveling():
    exp_disgea =[]
    exp_poke = []
    exp_ori = []
    exp_free = []
    t = np.arange(0., 5., 0.2)
    for level in range(1, 10000):
        exp_disgea.append(round(0.04 * (level ** 3) + 0.8 * (level ** 2) + 2 * level))
        exp_poke.append(math.pow(level,3))
        exp_ori.append(round((4 * (level ** 3)) / 5))
        exp_free.append(math.floor(1000 * (level ** 3)))
    plt.plot(exp_disgea, 'r--')
    plt.show()


def hunting(monster, user):
    m_hp = monster["health"]
    m_att = monster["att"]
    m_def = monster["def"]
    u_hp = user["health"]
    u_att = user["att"]
    u_def = user["def"]
    round = 0
    while (m_hp * u_hp) > 0:
        m_hp -= (u_att - m_def) if (u_att - m_def) > 0 else 1
        u_hp -= (m_att - u_def) if (m_att - u_def) > 0 else 1
        print("{} 라운드 m_hp = {} u_hp = {}".format(round, m_hp, u_hp))
        round += 1

    if m_hp < 0:
        print('유저 윈')
    elif u_hp < 0:
        print('유저 패')

def weapon_split(name:str):
    a= name.split('#')
    weapon_name = a[0]
    b= a[1].split('(')
    num = b[0]
    print(weapon_name, num)

def up():
    upProbability = 10
    success = 0
    for i in range(1, 1000):
        if random.random() <= (upProbability / 100):
            success += 1
    print(success/1000)

def re_use(name):
    # amount = re.findall(r'\d+', name)
    # name = name.split(amount)[0]
    # pattern = re.compile(r'[ㄱ-ㅣ가-힣]+ \d+\ ')
    pattern = re.compile(r' \d+')
    result1 = re.findall(pattern, name)
    if len(result1) == 0:
        return
    amount = int(result1)
    name = name.split(result1)[0]
    print(name)
    print(amount)

print(os.environ)
#
# a = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']
# a = list(map(int, a))
# print(max(a))
# weapon_split('죽도#3(0강)')
# time_test()
# asyncio.run(upgrade_item("죽도"))


# with open('./market2.json', encoding='UTF-8') as f:
#     d2 = json.load(f)
#
# items = {}
#
# for x, item in d2["Weapon"].items():
#     i = {x: ["무기", item['price'], x]}
#     items.update(i)
#
# for x, item in d2["item"].items():
#     i = {x: ["가챠", item['price'], x]}
#     items.update(i)
#
# ss='만만한 Hope_Candy의 막대사탕2'
# if ss in items.keys():
#     print('yes')
#     ssItem = items[ss]
# else:
#     ssItem = 'none'
#
# print(ssItem)



# update_user(10)


# app = Flask(__name__)
#
#
# @app.route('/')
# def hello_world():
#     return 'Hello World!'
#
#
# @app.before_request
# def limit_remote_addr():
#     if request.remote_addr != '127.0.0.2':
#         abort(403)  # Forbidden
#
#
# @app.route('/enroll', methods=['POST'])
# def enroll():
#     print(request.is_json)
#     params = request.get_json()
#     print(params['1'])
#     return 'ok'
#
#
# if __name__ == '__main__':
#     app.run()
