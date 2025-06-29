import discord
from discord.ext import commands
from discord import app_commands
import os
import aiohttp
import re


class TestForm(discord.ui.Modal, title='Questionnaire'):
    name = discord.ui.TextInput(label='Name', custom_id='name', style=discord.TextStyle.short,required=True)
    tell_me = discord.ui.TextInput(label='Tell me about yourself!', custom_id='bio',style=discord.TextStyle.long)
    async def on_submit(self, int:discord.Interaction):
        await int.response.send_message(f'Response recorded.')
        print(self.name,self.tell_me)
    async def on_timeout(self):
        print(f'Timeout occurred.')
        self.stop()

async def cb(interaction):
    await interaction.response.send_message(f'The following is your data: \n```{str(interaction.data)}```',ephemeral=True)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents, activity=discord.Activity(type=discord.ActivityType.watching,name='FIU panthers'), status=discord.Status.do_not_disturb)



@bot.event
async def on_ready():
    print('Ready!')
    print('\n'.join(k.name for k in bot.guilds))

@bot.event
async def on_message(m):
    if m.author.id == 247492668131770369 and m.content == f'{bot.user.mention} sync':
        await m.reply('Will do!')
        try:
            await bot.tree.sync()
        except Exception as e:
            print(e)


p = r'<GarageName>([a-zA-Z0-9]+)<\/GarageName><StudentSpaces>(\d+)<\/StudentSpaces><StudentMax>(\d+)<\/StudentMax>'
names = {'PG1':'PG1 (Gold Garage)', 'PG2': 'PG2 (Blue Garage)', 'PG3': 'PG3 (Panther Garage)', 'PG4': 'PG4 (Red Garage)', 'PG5': 'PG5 (Market Station)', 'PG6': 'PG6 (Tech Station)'}

@bot.tree.command(name='parking', description='Get parking details about the various garages around FIU.')
@app_commands.describe(garage = 'The specific garage whose information you would like to query.')
@app_commands.choices(garage=[ app_commands.Choice(name=f'PG{i}',value=i) for i in range(1,7) ])
async def parking(interaction: discord.Interaction, garage: app_commands.Choice[int] = None):
    async with aiohttp.request('get','https://patcount.fiu.edu/garagecount.xml') as result:
        info = await result.text(encoding='utf-16')
        matches = re.findall(p, info)
        if garage is None:
            ans = '\n'.join(
                f'{names[entry[0]]}: {max(int(entry[2]) - int(entry[1]),0)} spaces left ({min(100, int(100 * int(entry[1]) / int(entry[2])))}% full)'
                for entry in matches)
            await interaction.response.send_message(ans)
        else:
            entry = matches[garage.value-1]
            await interaction.response.send_message(f'{names[entry[0]]}: {max(int(entry[2]) - int(entry[1]),0)} spaces left ({min(100, int(100 * int(entry[1]) / int(entry[2])))}% full)')


locations = {1: (25.7562894576001, -80.37554052671632), 2: (25.90872378463799, -80.14017203764566), 3: (25.992155428732445, -80.33981177062306)}

@bot.tree.command(name='weather',description='Query information about the weather at a specific campus')
@app_commands.describe(campus="The specific campus whose weather you'd like to query. If none is given, this will default to MMC.")
@app_commands.choices(campus = [
    app_commands.Choice(name='MMC',value=1),
    app_commands.Choice(name='BBC',value=2),
    app_commands.Choice(name='I-75',value=3)
])
async def weather(interaction: discord.Interaction, campus: app_commands.Choice[int] = None):
    await interaction.response.defer()
    async with aiohttp.request('get',f'http://api.weatherapi.com/v1/current.json?key=e387556e2ba74025a5b232102232107&q={",".join(map(str,locations[campus.value if campus else 1]))}') as result:
        info = await result.json()
        # print(info)
        stuff = f'{campus.name if campus else "MMC"} weather information:\n{info["current"]["temp_f"]} °F ({info["current"]["temp_c"]} °C), {info["current"]["condition"]["text"]}\nWind speed: {info["current"]["wind_mph"]} mph ({info["current"]["wind_kph"]} kph)'
        await interaction.followup.send(stuff)




bot.run(os.environ.get('DISCORD_TOKEN'))
