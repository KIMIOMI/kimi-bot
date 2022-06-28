from aiohttp import web
from discord.ext import commands, tasks
import discord
import os
import aiohttp

app = web.Application()
routes = web.RouteTableDef()

class Webserver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web_server.start()

        @routes.get('/')
        async def welcome(request):
            return web.Response(text="Hello, world")

        @routes.post('/addrole')
        async def addrole(request):
            if request.headers.get('authorization') == '3mErTJMYFt':
                data = await request.json()
                user_id = int(data['user'])
                print(type(user_id))
                print(user_id)
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                if user is None:
                    return
                guild = self.bot.get_guild(973400785931079721)

                member = guild.get_member(user_id)
                role = guild.get_role(973444672754171944)
                await member.add_roles(role)
                embed = discord.Embed(title="Welcome Holder", colour=discord.Color.blurple())
                embed.description = f'New Holder : {user.mention} Just veryfied'
                embed.set_thumbnail(url=user.avatar_url)
                channel = self.bot.get_channel(973400785931079724)
                await channel.send(embed=embed)
            return web.Response(status=200)

        @routes.post('/removerole')
        async def removerole(request):
            if request.headers.get('authorization') == '3mErTJMYFt':
                data = await request.json()
                user_id = int(data['user'])
                print(type(user_id))
                print(user_id)
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                if user is None:
                    return
                guild = self.bot.get_guild(973400785931079721)
                member = guild.get_member(user_id)
                role = guild.get_role(973444672754171944)
                await member.remove_roles(role)
            return web.Response(status=200)

        self.webserver_port = os.environ.get('PORT', 5000)
        app.add_routes(routes)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Webserver Cog Loaded Succesfully")

    @tasks.loop()
    async def web_server(self):
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=self.webserver_port)
        await site.start()

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Webserver(bot))