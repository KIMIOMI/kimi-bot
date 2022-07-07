import motor.motor_asyncio
import nest_asyncio
import json
import datetime

class db():
    def __init__(self):
        with open('./data.json') as f:
            d1 = json.load(f)

        nest_asyncio.apply()
        mongo_url = d1['mongo']
        cluster = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        self.ecomoney = cluster["eco"]["money"]
        self.ecobag = cluster["eco"]["bag"]
        self.ecouser = cluster["eco"]["user"]
        self.key = ["id", "wallet", "bank", "land", "wage", "inventory", "gm_time", "tw_time"]
        self.userkey = ["id", "level", "exp", "armed", "att", "def", "health", "skill", "title"]

    async def open_account(self, id: int):
        new_user = {"id": id, "wallet": 0, "bank": 100, "land": 0, "wage": 0, "inventory": [],
                    "gm_time": datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=1)}
        # wallet = current money, bank = money in bank
        await self.ecomoney.insert_one(new_user)

    async def open_bag(self, id : int):
        if id is not None:
            newuser = {"id": id, "bag": []}
            await self.ecobag.insert_one(newuser)

    async def open_user(self, id : int):
        if id is not None:
            newuser = {"id": id, "level": 1, "exp": 0, "armed":{"weapon": "", "armor": "", "shoes": ""},"att": 1, "def": 1, "health": 10, "skill": [], "title": []} ## 추가
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

    async def update_user(self, id: int):
        try:
            if id is not None:
                bal = await self.ecomoney.find_one({"id": id})
                if bal is None:
                    await self.open_account(id)
                    bal = await self.ecomoney.find_one({"id": id})
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
                        elif key == "skill" or key == "title":
                            val = {}
                        else:
                            val = 0
                        await self.ecouser.update_one({"id": id}, {"$set": {key: val}})
                user = await self.ecouser.find_one({"id": id})
                return user
            else:
                return None
        except Exception as e:
            print(e)