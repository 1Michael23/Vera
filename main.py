import os
import random
import json
import discord
import asyncio
import logging
import coloredlogs
from discord_webhook import DiscordWebhook, DiscordEmbed
import random
import os
import requests
import shutil
import time
import string
import filetype
import urllib.request
import sqlite3

# BOT INIT

database = sqlite3.connect("vera.db")
db_cur = database.cursor()

database.execute("CREATE TABLE IF NOT EXISTS image_support (server_id TEXT, status TEXT)")
database.execute("CREATE TABLE IF NOT EXISTS blacklist (server_id TEXT, status TEXT)")

with open('statements.txt', 'r+') as file:
    statements = json.load(file)
with open('responses.txt', 'r+') as file:
    responses = json.load(file)
current_statement = statements[random.randint(0, len(statements)-1)]

logger = logging.getLogger(__name__)
fmt = ("%(asctime)s - %(message)s")
coloredlogs.install(fmt=fmt, logger=logger)
f = open("settings.json", "r")
settings = json.load(f)
token = settings['token']
webhook_url = settings['webhook']
status = settings['status']
prefix = settings['prefix']


class VeraBot(discord.Client):
    async def webhook_online(self):

        servers_serving = ""
        amt_server = 0
        for s in self.guilds:
            servers_serving = servers_serving+"\n"+s.name
            amt_server += 1
        try:
            webhook = DiscordWebhook(webhook)
            embed = DiscordEmbed(title=f'Vera Online Running On:  {str(amt_server)} Server(s)\nRunning As: {str(self.user)}',
                                 description=f'Using Key: {l_key}\nServing Server(s):\n{str(servers_serving)}\n', color=242424)
            webhook.add_embed(embed)
            #response = webhook.execute()
        except:
            logger.info(f"Error in inital webhook")
    async def on_ready(self):
        if settings['status'] != "":
            await self.change_presence(activity=discord.Game(name=str(status)))
        await self.webhook_online()
        logger.info(f"{self.user} is now online.")

    def ImageDatabase(self,server_name,status):
        if status == 'enable':
            database.execute("UPDATE image_support SET status = 'true' WHERE server_id = "+server_name)
            database.commit()
        elif status == 'disable':
            database.execute("UPDATE image_support SET status = 'false' WHERE server_id = "+server_name)
            database.commit()
        elif status == 'query_exist':
            db_cur.execute("SELECT * FROM image_support WHERE server_id = "+server_name)
            res = db_cur.fetchone()
            print(res)
            if res:
                return True
            else:
                return False
        elif status == 'query':
            db_cur.execute("SELECT status FROM image_support WHERE server_id = "+server_name)
            res = db_cur.fetchone()
            print(res)
            if res[0] == "true":
                return True
            elif res[0] == "false":
                return False
        elif status == "add":
            database.execute("INSERT INTO image_support (server_id,status) VALUES ("+server_name+",'true')")
            database.commit()

    def CheckImageList(self,server_name):
        db_cur.execute("SELECT status FROM image_support WHERE server_id =="+server_name)
        res = db_cur.fetchone()
        print(res)
    def downloadFile(self, url, path):
        try:
            letters = string.ascii_lowercase
            path = path+''.join(random.choice(letters) for i in range(8))
            r = requests.get(url)
            if r.status_code == 200:
                kind = filetype.guess(r.content)
                path = path+"."+kind.extension
            with open(path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            logger.critical(f"Error: {e}")

    def getImage(self, filelocation):
        file = random.choice([x for x in os.listdir(
            filelocation) if os.path.isfile(os.path.join(filelocation, x))])
        return filelocation + file

    async def on_message(self, message):
        if message.author == self.user:
            return

        check_res = self.ImageDatabase(str(message.guild.id),"query_exist")
        if check_res == True:
            pass
        elif check_res == False:
            self.ImageDatabase(str(message.guild.id),"add")

        image_status = self.ImageDatabase(str(message.guild.id),"query")
        if image_status == True:
            image_time = 'true'
        elif image_status == False:
            image_time = "false"
        if message.guild == None or settings['channel_name'] in message.channel.name:
            if message.content == settings['prefix']+"quit" and message.author.id in settings['admin']:
                logger.info("Exiting")
                self.loop.stop()
                await self.logout()

                exit()

            elif message.content == "^images enable" and message.author.guild_permissions(manage_channels=True):
                self.ImageDatabase(str(message.guild.id),"enable")
                await message.channel.send("**Image Support** Enabled")
            elif message.content == "^images diable" and message.author.guild_permissions(manage_channels=True):
                self.ImageDatabase(str(message.guild.id),"disable")
                await message.channel.send("**Image Support** Disabled")

            else:
                if message.content == "" and message.attachments == True or len(message.attachments) > 0:
                    await message.channel.trigger_typing()
                    if image_time == 'enabled':
                        image = self.getImage(f"images/")
                        for file in message.attachments:
                            self.downloadFile(file.url, './images/')
                        await message.channel.send(file=discord.File(image))
                    else:
                        pass
                else:
                    logger.info(f"Input: {message.content}")
                    await message.channel.trigger_typing()
                    num = random.randint(1, 20)
                    if num == 10 and image_time == "true":
                        image = self.getImage("images/")
                        await message.channel.send(file=discord.File(image))
                    else:
                           global current_statement
                           usrinput = message.content.lower()
                           is_in_s = usrinput in statements
                           if is_in_s == True:
                                if usrinput in responses.keys():
                                    value = random.choice(responses[usrinput])
                                    await message.channel.send(value)
                                    current_statement = value
                                else:
                                    await message.channel.send(usrinput)
                                    current_statement = usrinput
                           else:
                                statements.append(usrinput)
                                responses.setdefault(current_statement, [])
                                if usrinput in responses[current_statement]:
                                    pass
                                else:
                                    responses[current_statement].append(
                                        usrinput)
                                    current_statement = statements[random.randint(
                                        0, len(statements)-1)]
                                    await message.channel.send(current_statement)
                           jstatements = json.dumps(statements)
                           jresponses = json.dumps(responses)
                           with open('statements.txt', 'w+') as file:
                                file.write(jstatements)
                           with open('responses.txt', 'w+') as file:
                                file.write(jresponses)


bot = VeraBot()
bot.run(token)
