import discord
import os
import random
import string
import json
import time

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")  # Get token from Replit secrets

if not TOKEN:
    print("Error: Bot token is missing! Add it in Replit Secrets.")
    exit()

ALLOWED_USER_ID = 1146808618054848604  # Your Discord user ID
ROLE_NAME = "Redeemed"
GEN_CHANNEL_ID = 1335732302466256906
PREMIUM_GEN_CHANNEL_ID = 1335732391465058345  # Channel for premium generator

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

generated_keys = {}
redeemed_keys = {}

DATA_FILE = "redeemed_keys.json"

def load_redeemed_keys():
    global redeemed_keys
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            try:
                redeemed_keys = json.load(file)
            except json.JSONDecodeError:
                redeemed_keys = {}

def save_redeemed_keys():
    with open(DATA_FILE, "w") as file:
        json.dump(redeemed_keys, file, indent=4)

def generate_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def parse_time(duration):
    time_units = {"m": 60, "h": 3600, "d": 86400, "w": 604800, "mo": 2592000}
    if duration[-1] in time_units:
        return int(duration[:-1]) * time_units[duration[-1]]
    return None

def format_time(seconds):
    units = [("mo", 2592000), ("w", 604800), ("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]
    time_string = ""
    for name, value in units:
        if seconds >= value:
            time_string += f"{seconds // value}{name} "
            seconds %= value
    return time_string.strip() if time_string else "Expired"

async def get_or_create_role(guild):
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if not role:
        try:
            role = await guild.create_role(name=ROLE_NAME, reason="Auto-created for redeemed keys")
        except discord.Forbidden:
            return None
    return role

@client.event
async def on_ready():
    load_redeemed_keys()
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!help"):
        embed = discord.Embed(title="📜 Help Menu", color=0x000000)  # AMOLED Black
        embed.add_field(
            name="🧑 Regular User Commands",
            value="`!rkey [your_key]` → Redeem a key & get a role.\n"
                  "`!ckey` → Check your redeemed key & expiration.\n"
                  "`!help` → Show this help message.",
            inline=False
        )
        embed.add_field(
            name="⭐ Free Generator Commands",
            value="`!fgen roblox` → Generate a free Roblox account.",
            inline=False
        )
        embed.add_field(
            name="🌟 Premium Generator Commands",
            value="`!pgen roblox` → Generate a premium Roblox account.",
            inline=False
        )
        if message.author.id == ALLOWED_USER_ID:
            embed.add_field(
                name="👑 Owner Commands",
                value="`!gkey [amount] [duration]` → Generate keys.\n"
                      "`!purge` → Delete bot messages.\n"
                      "`!skeys` → View all redeemed keys.",
                inline=False
            )
        await message.channel.send(embed=embed)

    elif message.content.startswith("!gkey"):
        if message.author.id != ALLOWED_USER_ID:
            await message.channel.send("🚫 You don't have permission to generate keys!")
            return

        parts = message.content.split(" ")
        amount = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        duration = parse_time(parts[2]) if len(parts) > 2 else None

        if duration is None:
            await message.channel.send("❌ Invalid time format! Use `m`, `h`, `d`, `w`, `mo`.")
            return

        keys = {}
        for _ in range(amount):
            key = generate_key()
            keys[key] = int(time.time()) + duration

        generated_keys.update(keys)
        key_list = "\n".join(f"`{k}`" for k in keys.keys())
        duration_text = parts[2] if len(parts) > 2 else "Never"
        await message.channel.send(f"✅ Generated {amount}x {duration_text} Key(s):\n{key_list}")

    elif message.content.startswith("!rkey "):
        _, user_key = message.content.split(" ", 1)

        if user_key in generated_keys:
            if generated_keys[user_key] < int(time.time()):
                await message.channel.send("❌ This key has expired!")
                return

            if str(message.author.id) in redeemed_keys:
                await message.channel.send("🚫 You have already redeemed a key!")
                return

            redeemed_keys[str(message.author.id)] = {
                "key": user_key,
                "expires": generated_keys[user_key]
            }
            save_redeemed_keys()

            role = await get_or_create_role(message.guild)
            member = message.guild.get_member(message.author.id)
            if role and member:
                await member.add_roles(role)
                await message.channel.send(f"✅ {message.author.mention} redeemed a key and received the `{ROLE_NAME}` role!")

        else:
            await message.channel.send("❌ Invalid or already redeemed key!")

    elif message.content.startswith("!fgen roblox"):
        if message.channel.id != GEN_CHANNEL_ID:
            await message.channel.send(f"🚫 {message.author.mention} cannot use this command here. Use it in <#{GEN_CHANNEL_ID}>.")
            return

        if not os.path.exists("roblox.txt"):
            await message.channel.send("❌ No Roblox accounts available!")
            return

        with open("roblox.txt", "r") as file:
            accounts = file.readlines()

        if not accounts:
            await message.channel.send("❌ No Roblox accounts left!")
            return

        account = random.choice(accounts).strip()

        with open("roblox.txt", "w") as file:
            file.writelines([acc for acc in accounts if acc.strip() != account])

        with open("deletedroblox.txt", "a") as file:
            file.write(account + "\n")

        await message.author.send(account)

        embed = discord.Embed(title="🕹️ Your Free Roblox Account", color=0x000000)
        embed.add_field(name="📝 Account Info", value=f"```{account}```", inline=False)
        embed.set_footer(text="Tap and hold to copy on mobile ( First message that was sent. ) 📱")

        await message.author.send(embed=embed)
        await message.channel.send(f"✅ {message.author.mention}, check your DMs!")

    elif message.content.startswith("!pgen roblox"):
        if message.channel.id != PREMIUM_GEN_CHANNEL_ID:
            await message.channel.send(f"🚫 {message.author.mention} cannot use this command here. Use it in <#{PREMIUM_GEN_CHANNEL_ID}>.")
            return

        if not os.path.exists("roblox1.txt"):
            await message.channel.send("❌ No Premium Roblox accounts available!")
            return

        with open("roblox1.txt", "r") as file:
            accounts = file.readlines()

        if not accounts:
            await message.channel.send("❌ No Premium Roblox accounts left!")
            return

        account = random.choice(accounts).strip()

        with open("roblox1.txt", "w") as file:
            file.writelines([acc for acc in accounts if acc.strip() != account])

        with open("deletedroblox1.txt", "a") as file:
            file.write(account + "\n")

        await message.author.send(account)

        embed = discord.Embed(title="🕹️ Your Premium Roblox Account", color=0x000000)
        embed.add_field(name="📝 Account Info", value=f"```{account}```", inline=False)
        embed.set_footer(text="Tap and hold to copy on mobile ( First message that was sent. ) 📱")

        await message.author.send(embed=embed)
        await message.channel.send(f"✅ {message.author.mention}, check your DMs!")

    elif message.content.startswith("!ckey"):
        user_id = str(message.author.id)
        if user_id in redeemed_keys:
            remaining_time = max(0, redeemed_keys[user_id]["expires"] - int(time.time()))
            time_left = format_time(remaining_time)

            embed = discord.Embed(title="🔑 Your Redeemed Key", color=0x000000)
            embed.set_thumbnail(url=message.author.avatar.url)
            embed.add_field(name="👤 User", value=f"{message.author.mention}", inline=False)
            embed.add_field(name="🕒 Time Left", value=time_left, inline=False)
            await message.author.send(embed=embed)
            await message.channel.send(f"✅ {message.author.mention}, check your DMs!")
        else:
            await message.channel.send("🚫 You have not redeemed a key!")

client.run(TOKEN)
