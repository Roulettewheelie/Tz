import discord
from discord.ext import commands
from discord import app_commands
from Api import core  # Your class
import place

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

@bot.tree.command(name="baitgame", description="Create and upload a bait game")
@app_commands.describe(cookie="Your Roblox .ROBLOSECURITY cookie")
async def baitgame(interaction: discord.Interaction, cookie: str):
    await interaction.response.defer()

    try:
        c = core(cookie=cookie)
        if not c.check_cookie():
            await interaction.followup.send("❌ Invalid or banned cookie.")
            return

        result = c.newplace()
        if not result:
            await interaction.followup.send("❌ Game creation failed.")
            return

        universe_id, place_id = result

        # Force R6 avatar type
        csrf_token = c.csrf()
        c.session.patch(
            url=f"https://develop.roblox.com/v1/universes/{universe_id}/avatar",
            json={"avatarType": "R6"},
            cookies={".ROBLOSECURITY": cookie},
            headers={
                "x-csrf-token": csrf_token,
                "User-Agent": "Roblox/WinInet",
                "Content-Type": "application/json"
            }
        )

        # Configure, activate, publish, thumbnail, icon
        c.configure(universe_id, place_id)
        c.activate(universe_id)
        c.publish(place_id)
        c.thumbnail(universe_id)

        with open("icon.png", "rb") as icon_file:
            c.session.post(
                url=f"https://publish.roblox.com/v1/games/{universe_id}/icon/image",
                files={"file": icon_file},
                headers={
                    "x-csrf-token": csrf_token,
                    "User-Agent": "Roblox"
                },
                cookies={".ROBLOSECURITY": cookie}
            )

        # ✅ Create private server and get link
        vip_id = c.create_private_server(universe_id)
        if not vip_id:
            await interaction.followup.send("❌ Failed to create private server.")
            return

        link = c.gen_link(vip_id)
        if not link:
            await interaction.followup.send("❌ Failed to generate join link.")
            return

        await interaction.followup.send(
            f"🎮 **Game Created & Uploaded**\n"
            f"📍 Place ID: `{place_id}`\n"
            f"🌌 Universe ID: `{universe_id}`\n"
            f"✅ Forced R6, Configured, Activated, Published\n"
            f"🖼️ Icon & Thumbnail uploaded\n"
            f"🔒 Private Server Created\n"
            f"🔗 Join Link: {link}"
        )

    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

bot.run("MTQwNDQ0Nzc0OTMxNDcwNzYwNw.Gtm6Ud.rcW_QQV8K4Hdpmvl_CJpefLdbApP-3lwS5wdco")