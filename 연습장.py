import datetime
import random
import json
from flask import Flask
from flask import abort, request

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
                        datetime.datetime.now() - datetime.timedelta(days=1, hours=1) if key == "gm_time" else 0)

    except Exception as e:
        print(e)

def upgrade_item(ss: str):
    
    for x in bag['bag']:
        if x[0] == ss:
            init_amount = x[1]
            index = bag['bag'].index(x)

            if x[2] is None:
                for i in range(1, init_amount):

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
