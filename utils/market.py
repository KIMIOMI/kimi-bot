import json
import random

class Market():
    def __init__(self):
        with open('./market.json', encoding='UTF-8') as f:
            self.market_data = json.load(f)
        with open('./item_abbrev.json', encoding='UTF-8') as f:
            self.item_abbrev = json.load(f)

        self.items = {}
        self.land = self.market_data["Land"]

        for x, item in self.market_data["Weapon"].items():
            i = {x: ["무기", item['price'], x]}
            self.items.update(i)

        for x, item in self.market_data["item"].items():
            i = {x: ["가챠", item['price'], x]}
            self.items.update(i)

    def item_abbreviation(self, name: str):
        if name in self.item_abbrev.keys():
            return self.item_abbrev[name]
        else:
            return name

    def item(self, name):
        if name in self.items.keys():
            iteminshop = self.items[name]
        else:
            return 0, 0, 0, 0, 0, 0, 0, False

        if iteminshop[0] == '무기':
            item = self.market_data["Weapon"][name]
        elif iteminshop[0] == '가챠':
            item = self.market_data["item"][name]
        else:
            return 0, 0, 0, 0, 0, 0, 0, False

        price = item["price"]
        upPrice = item["강화비용"]
        upProbability = item["강화확률"]
        att = item["att"]
        defense = item["def"]
        health = item["health"]
        image = item["image"]

        return price, upPrice, upProbability, att, defense, health, image, True

    def gotcha(self):
        # weights = (50 / 17, 40 / 17, 35 / 17, 30 / 17, 25 / 17, 20 / 17, 15 / 17, 10 / 17, 9 / 17, 8 / 17, 7 / 17, 6 / 17, 5 / 17, 4 / 17, 3 / 17, 3 / 17, 1 / 17)
        weights = (80, 20, 10, 5, 25, 20, 15, 8, 7, 6, 5, 4, 3, 3, 1)
        a = random.choices(list(self.market_data["item"]), weights=weights)
        name = a[0]

        return name

    def armed_weapon_name_split(self, name: str):
        a = name.split('(')
        weapon_name = a[0]
        return weapon_name
