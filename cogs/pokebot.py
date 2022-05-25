import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
from bson.objectid import ObjectId
import requests
import random
import datetime
import math
import re
import json
import motor.motor_asyncio

with open('./data.json') as f:
    d1 = json.load(f)
with open('./market.json') as f:
    d2 = json.load(f)

mongo_url = d1['mongo']

cluster = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)

db = cluster["pokebot"]
pokemon = db["pokemon"]
servers = db["servers"]

# pokemon.create_index("createdAt", expireAfterSeconds= 10800, partialFilterExpression={"owner": ""})

# intents = discord.Intents().all()
# client = commands.Bot(command_prefix="p!", intents=intents)

class Pokebot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        res = servers.find_one({"_id": guild.id})
        if res is None:
            # add the server to the database
            servers.insert_one({"_id": guild.id, "spawn_count": 5, "spawn_channel": guild.text_channels[0].id, "message_counter": 0})

            # send a message in the server saying set a spawn count and channel

            text_channel = guild.text_channels[0]
            embed = discord.Embed(
                title= "Welcome to PokeBot!",
                description="Thank you for adding PokeBot to your server! Before you can start catching Pokemon,"
                            "have a server admin use the commands p!spawn and p!channel to set the Pokemon spawn count and "
                            "spawn channel respectively.",
                colour=discord.Color.gold()
            )
            embed.set_thumbnail(url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/25.png")
            embed.set_author(name="kimi", url="https://github.com/KIMIOMI/Zenbot",
                             icon_url="https://avatars.githubusercontent.com/u/102003898?v=4")
            await text_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        # check if the server exists in servers and if not create an entry
        server = servers.find_one({"_id": message.guild.id})
        if server is None:
            servers.insert_one({"_id": message.guild.id, "spawn_count": 5, "spawn_channel": message.guild.text_channels[0].id, "message_counter": 0})
        else:
            # check server message_counter
            message_counter = server["message_counter"]
            spawn_count = server["spawn_count"]

            # spawn pokemon ever spawn_count message in a specific server channel
            if message_counter + 1 >= spawn_count:
                # spawn a pokemon
                r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{random.randint(1, 898)}")
                data = r.json()
                name = data["name"]
                image = data["sprites"]["other"]["official-artwork"]["front_default"]

                types = []
                for type in data["types"]:
                    types.append(type["type"]["name"])

                hp = data["stats"][0]["base_stat"]
                attack = data["stats"][1]["base_stat"]
                defense = data["stats"][2]["base_stat"]
                special_attack = data["stats"][3]["base_stat"]
                special_defense = data["stats"][4]["base_stat"]
                speed = data["stats"][5]["base_stat"]
                weight = data["weight"]
                experience = data["base_experience"]

                abilities = []
                for ability in data["abilities"]:
                    abilities.append(ability["ability"]["name"])
                level = 0
                new_pokemon = {
                    "name": name, "image": image, "types": types, "hp": hp, "attack": attack, "defense": defense,
                    "special_attack": special_attack, "special_defense": special_defense, "speed": speed,
                    "weight": weight, "experience": experience, "abilities": abilities, "level": level, "owner": "",
                    "selected": False, "spawn_server": message.guild.id, "createdAt": datetime.datetime.utcnow()
                }
                pokemon.insert_one(new_pokemon)

                embed = discord.Embed(
                    title=f'A wild Pokemon {name} has appeared !!',
                    description="Quick! Catch them with **!pcatch pokemon name**."
                                "\nPokemon tends to run away after 3 hours appearing.",
                    color = discord.Color.gold()
                )
                embed.set_image(url=image)
                spawn_channel = message.guild.get_channel(server["spawn_channel"])
                await spawn_channel.send(embed=embed)
                message_counter = 0
            else:
                message_counter += 1
            servers.update_one(server, {"$set":{"message_counter": message_counter}})

            # check if the user owns any pokemon
            res = pokemon.find_one({"owner": message.author.id})
            if res is None:
                pass
            else:
                # increase the experience of the user's selected pokemon by 1
                pokemon.update_one({"owner": message.author.id, "selected": True}, {"$inc": {"experience": 1}})

                # check if the pokemon has leveled up
                poke = pokemon.find_one({"owner": message.author.id, "selected": True})
                exp =poke["experience"]
                level = poke["level"]
                if exp > math.pow(level, 3) and level < 100:
                    pokemon.update_one(poke, {"$inc":{"level": 1}})
                    await message.channel.send(f'{message.author.name}\'s Pokemon {poke["name"]} has leveled up.')


        await self.bot.process_commands(message)

    @commands.command()
    @commands.is_owner()
    @cooldown(1, 2, BucketType.user)
    async def pspawn(self, ctx, count : int):
        servers.update_one({"_id": ctx.guild.id}, {"$set": {"spawn_count": count}})


    @commands.command()
    @commands.is_owner()
    @cooldown(1, 2, BucketType.user)
    async def pchannel(self, ctx, text_channel : discord.TextChannel):
        servers.update_one({"_id": ctx.guild.id}, {"$set": {"spawn_channel": text_channel.id}})

    @commands.command()
    @commands.is_owner()
    @cooldown(1, 2, BucketType.user)
    async def pserver(self, ctx):
        res = servers.find_one({"_id": ctx.guild.id})
        embed = discord.Embed(
            title=f'Server Settings for {ctx.guild.name}',
            description=f'Spawn Count: {res["spawn_count"]}'
                        f'\nSpawn Channel: {ctx.guild.get_channel(res["spawn_channel"]).mention}',
            colour=discord.Color.gold()
        )

        await ctx.send(embed=embed)

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    async def pinventory(self, ctx):
        # find all pokemon with owner equal to ctx.author.id
        inv = pokemon.find({"owner": ctx.author.id})
        inv = list(inv)
        if len(inv) > 0:
            items = ""
            embed = discord.Embed(
                title=f"{ctx.author.name}'s Pokemon Inventory",
                colour=discord.Color.gold()
            )
            # loop through the response and display them in an embed
            for item in inv:
                if item["selected"]:
                    items = f'Name: {item["name"]} | Number: {item["_id"]}\n{items}'
                else:
                    items += f'Name: {item["name"]} | Number: {item["_id"]}'
            embed.add_field(name="Pokemon", value=items)
            await ctx.send(embed=embed)
        else:
            await ctx.send("You don't have Pokemon in your Inventory.")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    async def pnumber(self, ctx, *, name: str):
        # find all pokemon with owner equal to ctx.author.id
        # find all pokemon with name equal to name argument
        clean = re.match("^[a-zA-Z- ]*$", name)
        if clean is None:
            await ctx.send("Please enter a valid name.")
            return

        poke = pokemon.find({"owner": ctx.author.id, "name": name})
        poke = list(poke)

        if len(poke) > 0:
            items = ""
            embed = discord.Embed(
                title=f"{ctx.author.name}'s {name}s",
                color=discord.Color.gold()
            )

            # loop through the res and display each _id in an embed
            for item in poke:
                items += f'Name: {item["name"]} | Number : {item["_id"]}\n'
            embed.add_field(name="Pokemon", value=items)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"You don't own any pokemon with the name {name}")

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    async def pselect(self, ctx, object_id: str):
        # find the one pokemon with _id equal to object_id argument
        clean = re.match("^[a-zA-Z0-9]*$", object_id)
        if clean is None and len(object_id) != 24:
            await ctx.send("Please enter a valid number.")
            return

        res = pokemon.find_one({"_id": ObjectId(object_id), "owner": ctx.author.id})
        if res is None:
            await ctx.send("You don't have a Pokemon with this Number in your Inventory.")
        else:
            # find all pokemon with owner equal to ctx.author.id and selected equal to True, change selected to False
            pokemon.update_many({"owner": ctx.author.id, "selected": True}, {"$set": {"selected": False}})
            # change object_id pokemon selected to True
            pokemon.update_one({"_id": ObjectId(object_id), "owner": ctx.author.id}, {"$set": {"selected": True}})
            await ctx.send(f'Name: {res["name"]} | Number: {res["_id"]} is now your selected Pokemon.')

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    async def pinfo(self, ctx, object_id: str):
        # find one Pokemon with id equal to the object_id argument
        # get all the pokemon attributes and display them in an embed
        clean = re.match("^[a-zA-Z0-9]*$", object_id)
        if clean is None and len(object_id) != 24:
            await ctx.send("Please enter a valid number.")
            return

        poke = pokemon.find_one({"_id": ObjectId(object_id)})
        if poke is None:
            await ctx.send("A pokemon with this Number does not exist.")
        else:
            stats = f'Level: {poke["level"]}\nExperience: {poke["experience"]}\nHP: {poke["hp"]}\n' \
                    f'Attack: {poke["attack"]}\nDefense: {poke["defense"]}\nSpecial Attack: {poke["special_attack"]}\n' \
                    f'Special Defense: {poke["special_defense"]}\nSpeed: {poke["speed"]}\nWeight: {poke["weight"]}\n'
            abilities = ""
            for ability in poke["abilities"]:
                abilities += f'{ability.replace("-", " ")}\n'

            types = ""
            for type in poke["types"]:
                types += f'{type}\n'

            embed = discord.Embed(
                title=f'Info and stats for {poke["name"]}',
                description=f'{poke["name"]} | {object_id}',
                color=discord.Color.gold()
            )

            embed.set_thumbnail(url=poke["image"])
            embed.add_field(name="Stats", value=stats, inline=True)
            embed.add_field(name="Abilities", value=abilities, inline=True)
            embed.add_field(name="Types", value=types, inline=True)

            await ctx.send(embed=embed)

    @commands.command()
    @cooldown(1, 2, BucketType.user)
    async def pcatch(self, ctx, *, name: str):
        # if the pokemon doesn't have an owner
        # if the pokemon spawn_server is equal to ctx.guild.id
        # if the pokemon name matches the name argument
        clean = re.match("^[a-zA-Z- ]*$", name)
        if clean is None:
            await ctx.send("Please enter a valid name.")
            return

        poke = pokemon.find_one({"owner": "", "spawn_server": ctx.guild.id, "name": name.replace(" ", "-").lower()})
        if poke is None:
            await ctx.send("Either that is not the name of the Pokemon, this Pokemon has already been caught, "
                           "or this Pokemon has run away!")
        else:
            res = pokemon.find_one({"owner": ctx.author.id, "selected": True})
            if res is None:
                selected = True
            else:
                selected = False
            pokemon.update_one(poke, {"$set": {"owner": ctx.author.id, "selected": selected}})
            await ctx.send(f'{ctx.author.name} has caught a wild {poke["name"]}!')

def setup(bot):
    bot.add_cog(Pokebot(bot))