import discord
from discord.ext import commands
from discord import app_commands
import re, json, os, time

TOKEN = os.environ['TOKEN']

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

roblox_link_pattern = re.compile(r"https?://(?:www\.)?roblox\.com/(games|game|experiences)/\d+")

CONFIG_FILE = "sniper_config.json"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {"snipe_channels": {}, "position_channels": {}, "blacklist": {}}

recent_links = {}  # {guild_id: {link: timestamp}}

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="setsnipe", description="Set this channel to scan Roblox game links.")
async def set_snipe(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You must have Administrator permissions to use this command.", ephemeral=True)
        return

    gid = str(interaction.guild_id)
    cid = interaction.channel_id

    if config["position_channels"].get(gid) == cid:
        await interaction.response.send_message("This channel is already set as the position channel.", ephemeral=True)
        return

    config["snipe_channels"][gid] = cid
    save_config()
    await interaction.response.send_message("This channel is now set to snipe Roblox links.", ephemeral=True)

@bot.tree.command(name="position", description="Set this channel to receive globally sniped links.")
async def set_position(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You must have Administrator permissions to use this command.", ephemeral=True)
        return

    gid = str(interaction.guild_id)
    cid = interaction.channel_id

    if config["snipe_channels"].get(gid) == cid:
        await interaction.response.send_message("This channel is already set as the snipe channel.", ephemeral=True)
        return

    config["position_channels"][gid] = cid
    save_config()
    await interaction.response.send_message("This channel is now set to receive sniped links.", ephemeral=True)

@bot.tree.command(name="blacklist", description="Blacklist a keyword or ID from being scanned.")
@app_commands.describe(entry="Keyword or number to blacklist.")
async def blacklist(interaction: discord.Interaction, entry: str):
    gid = str(interaction.guild_id)
    config["blacklist"].setdefault(gid, [])

    if entry in config["blacklist"][gid]:
        config["blacklist"][gid].remove(entry)
        msg = f"Removed `{entry}` from the blacklist."
    else:
        config["blacklist"][gid].append(entry)
        msg = f"Added `{entry}` to the blacklist."

    save_config()
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="blacklistshow", description="Show current blacklist for this server.")
async def show_blacklist(interaction: discord.Interaction):
    gid = str(interaction.guild_id)
    bl = config["blacklist"].get(gid, [])
    if not bl:
        await interaction.response.send_message("No blacklist entries found.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Blacklist:\n" + "\n".join(f"- `{e}`" for e in bl), ephemeral=True)

@bot.tree.command(name="config", description="Show the bot's config for this server.")
async def config_check(interaction: discord.Interaction):
    gid = str(interaction.guild_id)
    sc = config["snipe_channels"].get(gid)
    pc = config["position_channels"].get(gid)
    embed = discord.Embed(title="Server Bot Configuration", color=discord.Color.blurple())
    embed.add_field(name="Snipe Channel", value=f"<#{sc}>" if sc else "Not set", inline=False)
    embed.add_field(name="Position Channel", value=f"<#{pc}>" if pc else "Not set", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help", description="How to use the Roblox Link Sniping Bot.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Roblox Link Sniper Bot",
        description="Detects Roblox game links across servers and reposts them globally.",
        color=discord.Color.purple()
    )
    embed.add_field(name="/setsnipe", value="Set this channel to watch Roblox links", inline=False)
    embed.add_field(name="/position", value="Set this channel to receive sniped links", inline=False)
    embed.add_field(name="/blacklist", value="Add/remove keywords or game IDs to ignore", inline=False)
    embed.add_field(name="/blacklistshow", value="See your blacklist entries", inline=False)
    embed.add_field(name="/config", value="Check which channels are set", inline=False)
    embed.set_footer(text="Bot by YourServerName | discord.gg/YourInvite")
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot or not message.guild:
        return

    gid = str(message.guild.id)
    snipe_channel_id = config.get("snipe_channels", {}).get(gid)

    if message.channel.id == snipe_channel_id:
        match = re.search(roblox_link_pattern, message.content)

        # Delete if masked or blacklisted
        if "://" in message.content and "[" in message.content:
            await message.delete()
            return

        blacklist = config.get("blacklist", {}).get(gid, [])
        if any(bad in message.content for bad in blacklist):
            await message.delete()
            return

        if not match:
            await message.delete()
            return

        link = match.group(0)

        # Check recent links
        now = time.time()
        recent_links.setdefault(gid, {})
        last_shared = recent_links[gid].get(link)

        if last_shared and now - last_shared < 3600:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, that link was already posted less than an hour ago.", delete_after=6)
            return

        # Update timestamp
        recent_links[gid][link] = now

        # Broadcast
        for target_gid, pos_channel_id in config.get("position_channels", {}).items():
            server = bot.get_guild(int(target_gid))
            if server:
                channel = server.get_channel(pos_channel_id)
                if channel:
                    embed = discord.Embed(
                        title="Roblox Game Sniped!",
                        description=f"[Click to view game]({link})",
                        color=discord.Color.from_rgb(180, 50, 255)
                    )
                    embed.add_field(name="Source Server", value=message.guild.name, inline=False)
                    embed.set_footer(text="Bot by YourServerName | discord.gg/YourInvite")
                    embed.timestamp = message.created_at
                    await channel.send(embed=embed)

    elif bot.user in message.mentions:
        embed = discord.Embed(
            title="Need Help?",
            description="Use the slash commands below to control the bot.",
            color=discord.Color.blurple()
        )
        embed.add_field(name="/help", value="Show command list", inline=False)
        embed.add_field(name="/setsnipe", value="Scan this channel for Roblox links", inline=False)
        embed.add_field(name="/position", value="Receive sniped links in this channel", inline=False)
        embed.set_footer(text="Bot by YourServerName | discord.gg/YourInvite")
        await message.channel.send(embed=embed)

bot.run(TOKEN)