import motor.motor_asyncio
import nest_asyncio
import json
import datetime
from utils.market import Market


class Db():
    def __init__(self):
        with open('./data.json') as f:
            mongo_data = json.load(f)
        with open('./channel.json', encoding='UTF-8') as f:
            self.channel_data = json.load(f)

        nest_asyncio.apply()
        mongo_url = mongo_data['mongo']
        cluster = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        self.market = Market()
        self.ecomoney = cluster["eco"]["money"]
        self.ecobag = cluster["eco"]["bag"]
        self.ecouser = cluster["eco"]["user"]
        self.ecoinfo = cluster["eco"]["info"]
        self.key = ["id", "wallet", "bank", "land", "wage", "inventory", "gm_time", "tw_time"]
        self.userkey = ["id", "level", "exp", "current_hp", "armed", "att", "def", "health", "skill", "title"]

    async def open_account(self, id: int):
        new_user = {"id": id, "wallet": 0, "bank": 100, "land": 0, "wage": 0, "inventory": [],
                    "gm_time": datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=1)}
        # wallet = current money, bank = money in bank
        await self.ecomoney.insert_one(new_user)

    async def open_bag(self, id: int):
        if id is not None:
            newuser = {"id": id, "bag": []}
            await self.ecobag.insert_one(newuser)

    async def open_user(self, id: int):
        if id is not None:
            newuser = {"id": id, "level": 1, "exp": 0, "current_hp": 10,
                       "armed":{"weapon": "", "armor": "", "shoes": ""},"att": 1, "def": 1,
                       "health": 10, "skill": [{"name": "찌르기", "level": 1, "att": 1, "type": "normal"}],
                       "title": [{"name": "초보 헌터", "rarity": "normal"}]}
            await self.ecouser.insert_one(newuser)

    async def update_wallet(self, id: int, wallet: int):
        if id is not None:
            await self.ecomoney.update_one({"id": id}, {"$set": {"wallet": wallet}})

    async def update_bank(self, id: int, bank: int):
        if id is not None:
            await self.ecomoney.update_one({"id": id}, {"$set": {"bank": bank}})

    async def add_wallet(self, id: int, amount: int):
        if id is not None:
            await self.ecomoney.update_one({"id": id}, {"$inc": {"wallet": amount}})

    async def add_land(self, id: int, amount: int):
        if id is not None:
            await self.ecomoney.update_one({"id": id}, {"$inc": {"wallet": amount}})

    async def arm_weapon(self, id: int, name, up, att, defense, hp):
        if id is not None:
            await self.ecouser.update_one({"id": id}, {"$inc": {"att": att, "def": defense, "health": hp}})
            await self.ecouser.update_one({"id": id}, {"$set": {"armed.weapon": f'{name}({up}강)'}})

    async def disarm_weapon(self, id: int, att, defense, hp):
        if id is not None:
            await self.ecouser.update_one({"id": id}, {"$inc": {"att": att, "def": defense, "health": hp}})
            await self.ecouser.update_one({"id": id}, {"$set": {"armed.weapon": ""}})

    async def update_user_current_hp(self, id: int, hp: int):
        if id is not None:
            await self.ecouser.update_one({"id": id}, {"$set": {"current_hp": hp}})

    async def update_user(self, id: int):
        try:
            if id is not None:
                bal = await self.ecomoney.find_one({"id": id})
                if bal is None:
                    await self.open_account(id)
                    bal = await self.ecomoney.find_one({"id": id})
                is_changed = False
                for key in self.key:
                    if key in bal:
                        pass
                    else:
                        if key == "bank":
                            val = 100
                        elif key == "gm_time" or key == "tw_time":
                            val = datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=1)
                        else:
                            val = 0
                        await self.ecomoney.update_one({"id": id}, {"$set": {key: val}})
                        is_changed = True
                if is_changed:
                    bal = await self.ecomoney.find_one({"id": id})
                return bal
            else:
                return None
        except Exception as e:
            print(e)

    async def update_bag(self, id: int):
        try:
            if id is not None:
                bag = await self.ecobag.find_one({"id": id})
                if bag is None:
                    await self.open_bag(id)
                    bag = await self.ecobag.find_one({"id": id})
                return bag
            else:
                return None
        except Exception as e:
            print(e)

    async def update_battle_user(self, id: int):
        try:
            if id is not None:
                user = await self.ecouser.find_one({"id": id})
                if user is None:
                    await self.open_user(id)
                    user = await self.ecouser.find_one({"id": id})
                for key in self.userkey:
                    if key in user:
                        pass
                    else:
                        if key == "level" or key == "att" or key == "def":
                            val = 1
                        elif key == "exp":
                            val = 0
                        elif key == "armed":
                            val = {"weapon": "", "armor": "", "shoes": ""}
                        elif key == "health":
                            val = 10
                        elif key == "skill":
                            val = [{"name": "찌르기", "level": 1, "att": 1, "type": "normal"}]
                        elif key == "title":
                            val = [{"name": "초보 헌터", "rarity": "normal"}]
                        elif key == "current_hp":
                            val = 10
                        else:
                            val = 0
                        await self.ecouser.update_one({"id": id}, {"$set": {key: val}})
                user = await self.ecouser.find_one({"id": id})
                return user
            else:
                return None
        except Exception as e:
            print(e)

    async def update_upgrade_item(self, id: int, name: str):
        bag = await self.update_bag(id)
        price, upPrice, upProbability, att, defense, health, image, _bool = self.market.item(name)
        if _bool is False:
            return None, 0

        for x in bag['bag']:
            if x[0] == name:
                index = bag['bag'].index(x)
                if len(x) < 3:
                    json_items = {"강화": 0, "강화 성공": 0, "강화 시도": 0, "att": att,
                                  "def": defense, "health": health, "강화확률": upProbability,
                                  "강화비용": upPrice}
                    await self.ecobag.update_one({"id": id}, {"$set": {f"bag.{index}.2": json_items}})
                return await self.ecobag.find_one({"id": id}, {"_id": 0, f"bag": {"$slice": [index, 1]}}), index
        return None, 0

    # function to add item in ecobag
    async def add_item(self, id: int, item: str, amount: int):
        if id is not None:
            price, upPrice, upProbability, att, defense, health, image, _bool = self.market.item(item)
            if _bool is not False:
                item_status = {"강화": 0, "강화 성공": 0, "강화 시도": 0, "att": att,
                               "def": defense, "health": health, "강화확률": upProbability,
                               "강화비용": upPrice}
                await self.ecobag.update_one({"id": id}, {"$push": {"bag": [item, amount, item_status]}})

    # function to edit amount of item in ecobag
    async def edit_item(self, id: int, index: int, amount: int):
        if id is not None:
            await self.ecobag.update_one({"id": id}, {"$set": {f"bag.{index}.1": amount}})

    # function to remove item from ecobag
    async def remove_item(self, id: int, name: str):
        if id is not None:
            await self.ecobag.update_one({"id": id}, {"$pull": {"bag": {"$in": [name]}}})
