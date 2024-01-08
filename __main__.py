import os
import pickle
import discord
import re
import traceback
import json
from discord.utils import get_or_fetch
from Confirm import Confirm

from constant import DATA_FILE, TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot : discord.Bot = discord.Bot(intents=intents)

data: dict[int, dict[int, int]] = {}

command_channel_id = {
    964318267785216020, # meemo testing
    1189679223288369193, # Fountain 1
    1189679598498222230, # Fountain 2
    1190704329703833700, # valentine 1
    1190704371458117674, # valentin 2
    1191843216136339567 # fountain-test
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

def get_member_score(guild_id: int, member_id: int) -> int | None:
    guild = data.get(guild_id)
    if guild is None:
        return None
    score = guild.get(member_id)
    if score is None:
        return None
    return score

def update_member_score(guild_id: int, member_id: int, score: int, increment_if_exist=False):
    guild = data.get(guild_id)
    if guild is None:
        guild = {member_id: score}
        data[guild_id] = guild
        return
    
    if increment_if_exist:
        if member_id not in guild:
            guild[member_id] = score
        else:
            guild[member_id] += score
    else:
        guild[member_id] = score

def get_participing_members(guild_id: int) -> dict[int, int]:
    guild = data.get(guild_id)
    if guild is None:
        return {}
    return guild
    
        
async def new_mimu_house_command(message: discord.Message):
    text = build_text(message)
    matchs: list[str] = re.findall(r"<@[0-9]+>,.you have earned [0-9]+", text, re.IGNORECASE | re.MULTILINE)
    for match in matchs:
        parts = match.strip().split(" ")
        try:
            point_to_add = int(parts[-1])
            member_id = int(match.split("@")[1].split(">")[0].strip())
            emoji = '\N{THUMBS UP SIGN}'
            update_member_score(message.guild.id, member_id, point_to_add, increment_if_exist=True)
            save_data()
            await message.add_reaction(emoji)

            member: discord.Member = await get_or_fetch(message.guild, "member", int(member_id))
            description=f"""{member.mention} has received {point_to_add} <:Amortenia_NF2U:1187203058384519168>

You now have {get_member_score(message.guild.id, member_id)} <:Amortenia_NF2U:1187203058384519168> 
[Jump to mimu message]({message.jump_url})"""
            embed = discord.Embed(title="Potions saved !", description=description, color=0xFFD3E2)
            await message.channel.send(embed=embed)
        except:
            exception = traceback.format_exception()
            await message.channel.send(f"```{exception}```")

@bot.slash_command(description="Show ranking")
async def leaderboard(ctx: discord.ApplicationContext):
    global member_to_points
    await ctx.defer()
    current_points = get_member_score(ctx.guild_id, ctx.author.id)
    if current_points is None:
        current_points = 0
    
    members = get_participing_members(ctx.guild_id)
    if len(members) == 0:
        description = "No one has participated yet"
    else:
        i = 1
        description = ""
        for member_id, points in {k: v for k, v in sorted(members.items(), key=lambda item: item[1], reverse=True)}.items():
            member: discord.Member = await get_or_fetch(ctx.guild, "member", int(member_id))
            description += f"{i}) {member.mention} with {points} <:Amortenia_NF2U:1187203058384519168> \n"
            i += 1
    embed = discord.Embed(title=f"You have {current_points} <:Amortenia_NF2U:1187203058384519168>", 
                          description=description, color=0xFFD3E2)
    await ctx.respond(embed=embed)
    
@bot.slash_command(description="Get my current points")
async def balance(ctx: discord.ApplicationContext,
                       member: discord.Option(
                            discord.Member, 
                            description="The member to check their points", required=False, default=None)):
    await ctx.defer()
    if member is None:
        current_points = get_member_score(ctx.guild_id, ctx.author.id)
        if current_points is None:
            current_points = 0
        await ctx.respond(f"You now have {current_points} <:Amortenia_NF2U:1187203058384519168>")
    else:
        current_points = get_member_score(ctx.guild_id, member.id)
        if current_points is None:
            current_points = 0
        await ctx.respond(embed=discord.Embed(
            description=f"The user {member.mention} now has {current_points} <:Amortenia_NF2U:1187203058384519168>")
        )


@bot.slash_command(description="Add points to a member")
async def add_points(ctx: discord.ApplicationContext, member: discord.Member, points: discord.Option(int)):
    await ctx.defer()
    update_member_score(ctx.guild_id, member.id, points, increment_if_exist=True)
    save_data()
    await ctx.respond(embed = discord.Embed(
        description="{} <:Amortenia_NF2U:1187203058384519168> were added to {}. New total is {} <:Amortenia_NF2U:1187203058384519168>".format(
        points, member.mention, get_member_score(ctx.guild_id, member.id) ))
    )
    
@bot.slash_command(description="Remove points from a member")
async def remove_points(ctx: discord.ApplicationContext, member: discord.Member, points: discord.Option(int, min_value=0)):
    await ctx.defer()
    member_score  = get_member_score(ctx.guild_id, member.id)
    if member_score is None:
        await ctx.respond(embed = discord.Embed(description="No <:Amortenia_NF2U:1187203058384519168> were removed because {} doesn't have any yet".format(
            member.mention
        )))
    else:
        update_member_score(ctx.guild_id, member.id, -points, increment_if_exist=True)
        save_data()
        await ctx.respond(embed = discord.Embed(description="{} <:Amortenia_NF2U:1187203058384519168> were removed from {}. New total is {} points".format(
            points, member.mention, member_score - points)))
    
@bot.slash_command(description="Set points to a member")
async def set_points(ctx: discord.ApplicationContext, member: discord.Member, points: discord.Option(int, min_value=0)):
    await ctx.defer()
    update_member_score(ctx.guild_id, member.id, points)
    save_data()
    await ctx.respond(embed = discord.Embed(description="{} now has {} <:Amortenia_NF2U:1187203058384519168>".format(member.mention, points)))
    
@bot.slash_command(description="Delete all the points data")
async def clear_all_points(ctx: discord.ApplicationContext):
    global data
    view = Confirm()
    await ctx.respond("Do you really want to delete all the <:Amortenia_NF2U:1187203058384519168> of EVERYONE ?", view=view)
    await view.wait()
    if view.value:
        data.clear()
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
    global data
    with open(DATA_FILE, "wb") as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
def load_data():
    global data
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "rb") as handle:
            data = pickle.load(handle)
            print(json.dumps(
                data,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')
))
    else:
        data = {}

load_data()
bot.run(TOKEN)