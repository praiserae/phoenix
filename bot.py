import discord
from discord.ext import commands, tasks
import random
import json
import os

# Create the bot instance
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load/Save data to a JSON file (or use a database)
data_file = "user_data.json"
if not os.path.exists(data_file):
    with open(data_file, "w") as f:
        json.dump({}, f)

# Function to load user data
def load_data():
    with open(data_file, "r") as f:
        return json.load(f)

# Function to save user data
def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

# Leveling System: Grant XP when a user sends a message
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load_data()

    user_id = str(message.author.id)
    if user_id not in data:
        data[user_id] = {"xp": 0, "level": 1, "messages_sent": 0}

    # Grant XP for each message
    data[user_id]["xp"] += random.randint(10, 20)  # Add random XP between 10-20
    data[user_id]["messages_sent"] += 1

    # Level Up Check
    xp_needed = data[user_id]["level"] * 100  # XP required to level up
    if data[user_id]["xp"] >= xp_needed:
        data[user_id]["level"] += 1
        # Send level-up message to #levels channel
        levels_channel = discord.utils.get(message.guild.text_channels, name="levels")
        if levels_channel:
            await levels_channel.send(f"🎉 {message.author.mention} leveled up to Level {data[user_id]['level']}!")

    save_data(data)
    await bot.process_commands(message)

# Command to show user's level and XP
@bot.command()
async def level(ctx):
    # Restrict this command to the #bot-commands channel
    if ctx.channel.name != "bot-commands":
        await ctx.send("Please use this command in the #bot-commands channel.")
        return

    user_id = str(ctx.author.id)
    data = load_data()

    if user_id not in data:
        await ctx.send(f"{ctx.author.mention}, you haven't earned any XP yet!")
        return

    xp = data[user_id]["xp"]
    level = data[user_id]["level"]
    await ctx.send(f"{ctx.author.mention}, you are at Level {level} with {xp} XP.")

# Command to show leaderboard
@bot.command()
async def leaderboard(ctx):
    # Restrict this command to the #bot-commands channel
    if ctx.channel.name != "bot-commands":
        await ctx.send("Please use this command in the #bot-commands channel.")
        return

    data = load_data()
    leaderboard_data = sorted(data.items(), key=lambda x: x[1]['xp'], reverse=True)

    leaderboard_message = "🏆 **Leaderboard** 🏆\n"
    for rank, (user_id, stats) in enumerate(leaderboard_data[:10]):
        user = await bot.fetch_user(user_id)
        leaderboard_message += f"{rank + 1}. {user.mention} - Level {stats['level']} | {stats['xp']} XP\n"

    await ctx.send(leaderboard_message)

# Command to create custom commands
@bot.command()
@commands.has_permissions(administrator=True)
async def addcommand(ctx, name: str, *, response: str):
    # Restrict this command to the #bot-commands channel
    if ctx.channel.name != "bot-commands":
        await ctx.send("Please use this command in the #bot-commands channel.")
        return

    data = load_data()
    if "commands" not in data:
        data["commands"] = {}

    data["commands"][name] = response
    save_data(data)
    await ctx.send(f"Custom command `{name}` added successfully!")

# Command to execute custom commands
@bot.command()
async def custom(ctx, name: str):
    # Restrict this command to the #bot-commands channel
    if ctx.channel.name != "bot-commands":
        await ctx.send("Please use this command in the #bot-commands channel.")
        return

    data = load_data()
    if "commands" in data and name in data["commands"]:
        await ctx.send(data["commands"][name])
    else:
        await ctx.send(f"No custom command found for `{name}`.")

# Reaction role (add/remove roles based on user reactions)
@bot.command()
@commands.has_permissions(administrator=True)
async def reactionrole(ctx, message_id: int, emoji: str, role: discord.Role):
    # Restrict this command to the #bot-commands channel
    if ctx.channel.name != "bot-commands":
        await ctx.send("Please use this command in the #bot-commands channel.")
        return

    message = await ctx.fetch_message(message_id)
    await message.add_reaction(emoji)
    
    # Save the role-reaction mapping to a file or database
    data = load_data()
    if "reaction_roles" not in data:
        data["reaction_roles"] = {}
    data["reaction_roles"][str(message_id)] = {"emoji": emoji, "role": role.id}
    save_data(data)
    await ctx.send(f"Reaction role set! React with {emoji} to get the {role.name} role.")

# Assign roles based on reactions
@bot.event
async def on_reaction_add(reaction, user):
    data = load_data()
    if "reaction_roles" in data and str(reaction.message.id) in data["reaction_roles"]:
        role_id = data["reaction_roles"][str(reaction.message.id)]["role"]
        emoji = data["reaction_roles"][str(reaction.message.id)]["emoji"]

        if reaction.emoji == emoji:
            role = discord.utils.get(user.guild.roles, id=role_id)
            await user.add_roles(role)
            await user.send(f"You have been given the {role.name} role!")

# Welcome message for new members
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if channel:
        await channel.send(f"Welcome {member.mention} to the server! 🎉 We're glad to have you here.")

# Admin-only command to clear the chat (up to 100 messages)
@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int):
    # Restrict this command to the #bot-commands channel
    if ctx.channel.name != "bot-commands":
        await ctx.send("Please use this command in the #bot-commands channel.")
        return

    if amount > 100:
        await ctx.send("You can only delete up to 100 messages at a time.")
        return
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"Cleared {amount} messages!")

# Command to display a list of all available commands
@bot.command()
async def cmds(ctx):
    # Restrict this command to the #bot-commands channel
    if ctx.channel.name != "bot-commands":
        await ctx.send("Please use this command in the #bot-commands channel.")
        return

    cmds_list = """
    **List of Available Commands:**
    - `!level` - Check your level and XP
    - `!leaderboard` - View the top 10 users by XP
    - `!custom <command_name>` - Execute a custom command
    - `!addcommand <name> <response>` - Admin command to create custom commands
    - `!reactionrole <message_id> <emoji> <role>` - Admin command to set up reaction roles
    - `!clear <amount>` - Admin command to clear up to 100 messages
    """
    await ctx.send(cmds_list)

# Run the bot
bot.run('MTMxNDMyNjg0MzMyNjk5MjQ5Nw.G4WLjC.FTENcRXiajbVUf-X9mLqX3idlDC1Ui-L2MlyW8')
