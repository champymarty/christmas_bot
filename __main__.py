import os
import pickle
import discord
import re
import traceback
from discord.utils import get_or_fetch
from Confirm import Confirm

from constant import DATA_FILE, TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot : discord.Bot = discord.Bot(intents=intents)

member_to_points = {}

command_channel_id = {
    964318267785216020
}

listen_members_id = {
    493716749342998541 # Mimu id
}

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message: discord.Message):
    if message.channel.id in command_channel_id and message.author.id in listen_members_id:
        await new_mimu_house_command(message)
        
async def new_mimu_house_command(message: discord.Message):
    text = build_text(message)
    matchs: list[str] = re.findall(r"<@[0-9]+>,.you have earned [0-9]+", text, re.IGNORECASE | re.MULTILINE)
    for match in matchs:
        parts = match.strip().split(" ")
        try:
            point_to_add = int(parts[-1])
            member_id = int(match.split("@")[1].split(">")[0].strip())
            emoji = '\N{THUMBS UP SIGN}'
            if not member_id in member_to_points:
                member_to_points[member_id] = point_to_add
            else:
                member_to_points[member_id] += point_to_add
            save_data()
            await message.add_reaction(emoji)

            member: discord.Member = await get_or_fetch(message.guild, "member", int(member_id))
            description=f"The member {member.mention} have received {point_to_add}. That member now have {member_to_points.get(member_id)} points\n[Jump to mimu message]({message.jump_url})"
            embed = discord.Embed(title="You have received new currency !", description=description)
            await message.channel.send(embed=embed)
        except:
            exception = traceback.format_exception()
            await message.channel.send(f"```{exception}```")

@bot.slash_command(description="Show ranking")
async def leaderboard(ctx: discord.ApplicationContext):
    global member_to_points
    await ctx.defer()
    current_points = member_to_points.get(ctx.author.id)
    if current_points is None:
        current_points = 0
    
    if len(member_to_points) == 0:
        description = "No one have participated yet"
    else:
        i = 1
        description = ""
        for member_id, points in {k: v for k, v in sorted(member_to_points.items(), key=lambda item: item[1], reverse=True)}.items():
            member: discord.Member = await get_or_fetch(ctx.guild, "member", int(member_id))
            description += "{}) {} with {} points \n".format(i, member.mention, points)
            i += 1
    embed = discord.Embed(title="You have {} points".format(current_points), description=description)
    await ctx.respond(embed=embed)
    
@bot.slash_command(description="Get my current points")
async def balance(ctx: discord.ApplicationContext,
                       member: discord.Option(
                            discord.Member, 
                            description="The member to check his/her points", required=False, default=None)):
    global member_to_points
    await ctx.defer()
    current_points = 0
    if member is None:
        if ctx.author.id in member_to_points:
            current_points = member_to_points.get(ctx.author.id)
        await ctx.respond("You have now {} points".format(current_points))
    else:
        if member.id in member_to_points:
            current_points = member_to_points.get(member.id)
        await ctx.respond(embed=discord.Embed(description="The user {} now have {} points".format(
            member.mention, current_points)))


@bot.slash_command(description="Add points to a member")
async def add_points(ctx: discord.ApplicationContext, member: discord.Member, points: discord.Option(int)):
    global member_to_points
    await ctx.defer()
    if not member.id in member_to_points:
        member_to_points[member.id] = points
    else:
        member_to_points[member.id] += points
    save_data()
    await ctx.respond(embed = discord.Embed(description="{} points where added to {}. New total is {} points".format(
        points, member.mention, member_to_points[member.id] )))
    
@bot.slash_command(description="Remove points to a member")
async def remove_points(ctx: discord.ApplicationContext, member: discord.Member, points: discord.Option(int, min_value=0)):
    global member_to_points
    await ctx.defer()
    if not member.id in member_to_points:
        await ctx.respond(embed = discord.Embed(description="No points where remove because {} dont have any yet".format(
            member.mention
        )))
    else:
        member_to_points[member.id] -= points
        save_data()
        await ctx.respond(embed = discord.Embed(description="{} points where remove from {}. New total is {} points".format(
            points, member.mention, member_to_points[member.id])))
    
@bot.slash_command(description="Set points to a member")
async def set_points(ctx: discord.ApplicationContext, member: discord.Member, points: discord.Option(int, min_value=0)):
    global member_to_points
    await ctx.defer()
    member_to_points[member.id] = points
    save_data()
    await ctx.respond(embed = discord.Embed(description="{} now have {} points".format(member.mention, points)))
    
@bot.slash_command(description="Delete all the points data")
async def clear_all_points(ctx: discord.ApplicationContext):
    global member_to_points
    view = Confirm()
    await ctx.respond("Do you really want to delete all the points of EVERYONE ?", view=view)
    await view.wait()
    if view.value:
        member_to_points = {}
        save_data()
        await ctx.respond(embed = discord.Embed(description="All data reset !"))
    
def build_text(message: discord.Message):
    text = ""
    text += message.content
    try:
        for embed in message.embeds:
            text += embed.description
            for field in embed.fields:
                text += field.name
                text += field.value
    except TypeError:
        pass
    return text

def save_data():
    global member_to_points
    with open(DATA_FILE, "wb") as handle:
        pickle.dump(member_to_points, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
def load_data():
    global member_to_points
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "rb") as handle:
            member_to_points = pickle.load(handle)
            print(member_to_points)
    else:
        member_to_points = {}

load_data()
bot.run(TOKEN)